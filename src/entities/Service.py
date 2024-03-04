import logging

from typing import Any
from datetime import datetime
from datetime import timedelta

from aiogram.types import Message
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone

from src.bot import dialogs
from src.bot.scheme import TGDocument
from src.entities.User import User
from src.bot.tasks import check_task_deadline, check_task_activate_step_2
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
        self.scheduler.remove_job(job_id)
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
