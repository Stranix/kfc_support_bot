import logging

from typing import Any
from datetime import datetime
from datetime import timedelta

from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from django.conf import settings
from django.utils import timezone

from src.models import SDTask
from src.bot.tasks import check_task_activate_step_1
from src.bot.tasks import check_task_activate_step_2
from src.bot.tasks import check_task_deadline
from src.bot.tasks import check_end_of_shift

logger = logging.getLogger('support_bot')


class Scheduler:

    def __init__(self, scheduler: AsyncIOScheduler):
        self.aio_scheduler = scheduler

    async def add_scheduler_job_datetime(
            self,
            job_func: Any,
            run_date: datetime,
            job_name: str,
            *args,
    ):
        """Создание задачи шедулера с запуском по дате"""
        logger.info('Создание задачи шедулера с именем %s', job_name)
        self.aio_scheduler.add_job(
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
            self.aio_scheduler.remove_job(job_id)
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
