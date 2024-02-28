import logging

from typing import Any
from datetime import datetime
from datetime import timedelta

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone

from src.entities.User import User
from src.bot.handlers.schedulers import check_task_deadline
from src.bot.handlers.schedulers import check_task_activate_step_1
from src.models import CustomUser, SDTask

logger = logging.getLogger('support_bot')


class Service:

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.scheduler.start()

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
            check_task_deadline,
            timezone.now() + timedelta(minutes=settings.TASK_DEADLINE),
            f'job_{task.number}_deadline',
            task.number,
        )
        logger.info('Проверки добавлены')

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


job_store = {
        'default': MemoryJobStore()
    }
if settings.REDIS_HOST == 'redis':
    job_store['default'] = RedisJobStore(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
    )
service = Service(
    scheduler=AsyncIOScheduler(
        jobstores=job_store
    )
)
