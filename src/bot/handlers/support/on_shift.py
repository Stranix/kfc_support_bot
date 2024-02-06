import logging

from datetime import timedelta

from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Router
from aiogram import html
from aiogram import types
from aiogram.filters import Command

from django.utils import timezone

from src.models import CustomUser
from src.models import WorkShift
from src.bot.utils import send_notify
from src.bot.utils import get_employee_managers
from src.bot.utils import send_new_tasks_notify_for_middle
from src.bot.handlers.schedulers import check_end_of_shift

logger = logging.getLogger('support_bot')
router = Router(name='on_shift_handlers')


@router.message(Command('on_shift'))
async def on_shift(
        message: types.Message,
        employee: CustomUser,
        scheduler: AsyncIOScheduler,
):
    logger.info('Сотрудник заступает на смену')
    if await is_active_shift(employee):
        await message.answer('У вас уже есть открытая смена')
        return
    logger.debug('Фиксируем старт смены в БД')
    shift = await WorkShift.objects.acreate(
        new_employee=employee,
        shift_start_at=timezone.now(),
    )
    logger.debug('Добавляю задачу на проверку окончания смены через 9 часов')
    try:
        scheduler.add_job(
            check_end_of_shift,
            'date',
            run_date=timezone.now() + timedelta(hours=9),
            timezone='Europe/Moscow',
            args=(shift.id, ),
            id=f'job_{shift.id}_end_shift',
        )
        logger.debug('Задача добавлена')
    except ConflictingIdError:
        logger.debug('Не смог добавить задачу. Такая задача уже существует.')
    logger.info('Отправляю уведомление менеджеру и пользователю')
    await message.answer('Вы добавлены в очередь на получение задач')
    await send_new_tasks_notify_for_middle(employee, message)
    managers = await get_employee_managers(employee)
    await send_notify(
        managers,
        f'Сотрудник: {html.code(employee.name)}\nЗаступил на смену',
    )


async def is_active_shift(employee: CustomUser) -> bool:
    logger.info('Проверяем есть ли у пользователя не завершенные смены')
    try:
        await employee.new_work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
        )
        logger.info('У пользователя есть активная смена')
        return True
    except WorkShift.DoesNotExist:
        logger.warning('У пользователя нет активной смены')
        return False
