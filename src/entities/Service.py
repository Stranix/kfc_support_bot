import logging
import re

from typing import Any
from datetime import datetime
from datetime import timedelta

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone

from src.bot import dialogs
from src.bot.scheme import TGDocument
from src.entities.User import User
from src.bot.tasks import check_task_deadline, check_task_activate_step_2, \
    check_end_of_shift
from src.bot.tasks import check_task_activate_step_1
from src.models import CustomUser, SDTask, CustomGroup

logger = logging.getLogger('support_bot')


class Service:

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler

    async def add_scheduler_job_datetime(
            self,
            job_func: Any,
            run_date: datetime,
            job_name: str,
            *args,
    ):
        """Создание задачи шедулера с запуском по дате"""
        logger.info('Создание задачи шедулера с именем %s', job_name)
        self.scheduler.add_job(
            func=job_func,
            trigger='date',
            run_date=run_date,
            timezone='Europe/Moscow',
            args=args,
            id=job_name,
        )
        logger.info('Задача создана')

    async def delete_scheduler_job_by_id(self, job_id: str):
        """Удаляем задачу шедулера по id"""
        logger.info('Удаляем задачу шедулера: %s', job_id)
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            logger.debug('Не нашел подходящей джобы')
        logger.info('Задача удалена')

    async def add_new_task_schedulers(self, task: SDTask):
        logger.info('Добавление временных проверок по задаче')
        await self.add_scheduler_job_datetime(
            check_task_activate_step_1,
            timezone.now() + timedelta(minutes=settings.TASK_ESCALATION),
            f'job_{task.number}_step1',
            task.number,
        )
        await self.add_scheduler_job_datetime(
            check_task_activate_step_2,
            timezone.now() + timedelta(minutes=settings.TASK_ESCALATION * 2),
            f'job_{task.number}_step2',
            task.number,
        )
        await self.add_scheduler_job_datetime(
            check_task_deadline,
            timezone.now() + timedelta(minutes=settings.TASK_DEADLINE),
            f'job_{task.number}_deadline',
            task.number,
        )
        logger.info('Проверки добавлены')

    async def add_check_shift(self, shift_id: int):
        logger.debug(
            'Добавляю задачу на проверку окончания смены через 9 часов')
        try:
            await self.add_scheduler_job_datetime(
                    check_end_of_shift,
                    timezone.now() + timedelta(hours=9),
                    f'job_{shift_id}_end_shift',
                    shift_id,
            )
            logger.debug('Задача добавлена')
        except ConflictingIdError:
            logger.debug(
                'Не смог добавить задачу. Такая задача уже существует.')

    @staticmethod
    def get_job_store():
        job_store = {
            'default': MemoryJobStore()
        }
        if settings.REDIS_HOST == 'redis':
            job_store['default'] = RedisJobStore(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
            )
        return job_store

    @staticmethod
    async def get_engineers_on_shift_by_support_group(
            support_group: str,
    ) -> list[User]:
        """Получение инженеров на смене по группе поддержки"""
        logger.info('Получение сотрудников по группе поддержки')
        support_engineers = []
        if support_group == 'DISPATCHER':
            dispatchers = await CustomUser.objects.dispatchers_on_work()
            logger.debug('dispatchers: %s', dispatchers)
            support_engineers = dispatchers

        if support_group == 'ENGINEER':
            engineers = await CustomUser.objects.engineers_on_work()
            logger.debug('engineers: %s', engineers)
            support_engineers = engineers
        logger.debug('support_engineers: %s', support_engineers)
        return [User(engineer) for engineer in support_engineers]

    @staticmethod
    async def get_senior_engineers() -> list[User] | None:
        senior_engineers = await sync_to_async(list)(
            CustomUser.objects.prefetch_related('groups').filter(
                groups__name__contains='Ведущие инженеры',
            )
        )
        logger.debug('senior_engineers: %s', senior_engineers)
        if not senior_engineers:
            logger.error('В системе не назначены ведущие инженеры')
            return
        return [User(engineer) for engineer in senior_engineers]

    @staticmethod
    async def get_group_managers_by_group_id(
            group_id: int,
    ) -> list[User] | None:
        group = await CustomGroup.objects.prefetch_related('managers')\
                                         .aget(id=group_id)
        group_managers = group.managers.all()
        return [User(manager) for manager in group_managers]

    @staticmethod
    async def get_documents(message: Message, album: dict) -> TGDocument:
        tg_documents = TGDocument()
        if not album:
            if message.document:
                document_id = message.document.file_id
                document_name = message.document.file_name
                tg_documents.documents[document_name] = document_id
            if message.photo:
                photo_id = message.photo[-1].file_id
                tg_documents.documents['image_doc.jpg'] = photo_id

        for counter, event in enumerate(album, start=1):
            if event.photo:
                photo_id = event.photo[-1].file_id
                tg_documents.documents[f'image_act_{counter}.jpg'] = photo_id
                continue
            document_id = event.document.file_id
            document_name = event.document.file_name
            tg_documents.documents[document_name] = document_id

        if not tg_documents.documents:
            tg_documents.is_error = True
            tg_documents.error_msg = await dialogs.error_empty_documents()
        return tg_documents

    @staticmethod
    async def find_external_number_in_task(text_for_search: str) -> list:
        """Поиск номера заявки внешней системы в задаче"""
        found_numbers = []
        regex_pattern = re.compile(r'([a-zA-Z]{2,3}\S?[0-9]{7})+')
        found_numbers.extend(regex_pattern.findall(text_for_search))
        logger.debug('found_numbers: %s', found_numbers)
        if not found_numbers:
            logger.info('Не нашел номеров внешней системы в задачах')
        return found_numbers

    @staticmethod
    async def create_documents_media_group(
            tg_documents: dict,
    ) -> list:
        """Создаем медиа-группу из полученных ранее документов"""
        bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=ParseMode.HTML)
        media_group = MediaGroupBuilder(caption='Приложенные документы')
        for doc_name, doc_id in tg_documents.items():
            tg_file = await bot.get_file(doc_id)
            io_file = await bot.download_file(tg_file.file_path)
            text_file = BufferedInputFile(io_file.read(), filename=doc_name)
            media_group.add_document(text_file)
        await bot.session.close()
        return media_group.build()
