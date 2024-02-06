import logging

from aiogram import Router
from aiogram import html
from aiogram import types
from aiogram.filters import Command

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from django.utils import timezone

from src.models import CustomUser
from src.models import WorkShift
from src.bot.utils import send_notify
from src.bot.utils import get_employee_managers
from src.bot.utils import send_new_tasks_notify_for_middle

logger = logging.getLogger('support_bot')
router = Router(name='end_shift_handlers')


@router.message(Command('end_shift'))
async def end_shift(
        message: types.Message,
        employee: CustomUser,
        scheduler: AsyncIOScheduler,
):
    logger.info('Старт процесса завершения смены')
    try:
        work_shift = await employee.new_work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
        )
    except WorkShift.DoesNotExist:
        logger.warning('Не нашел открытую смену у сотрудника')
        await message.answer(
            'Нет активной смены.'
            'Сначала смену надо начать. Используй команду: /on_shift'
        )
        return
    logger.debug('Фиксируем завершение смены в БД')
    work_shift.shift_end_at = timezone.now()
    work_shift.is_works = False
    await work_shift.asave()
    await send_new_tasks_notify_for_middle(employee, message)
    logger.debug('Удаляю scheduler проверки смены')
    try:
        scheduler.remove_job(f'job_{work_shift.id}_end_shift')
        logger.debug('Удалил')
    except JobLookupError:
        logger.debug('Не нашел подходящей джобы')
    await message.answer('Смена окончена. Пока 👋')
    logger.info('Отправляю уведомление менеджеру')
    managers = await get_employee_managers(employee)
    await send_notify(
        managers,
        f'Сотрудник: {html.code(employee.name)}\nЗавершил смену',
    )
