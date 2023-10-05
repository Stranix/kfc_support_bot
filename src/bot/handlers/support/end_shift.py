import logging

from aiogram import Router
from aiogram import html
from aiogram import types
from aiogram.filters import Command
from django.utils import timezone

from src.models import Employee
from src.models import WorkShift

logger = logging.getLogger('support_bot')
router = Router(name='end_shift_handlers')


@router.message(Command('end_shift'))
async def end_shift(message: types.Message, employee: Employee):
    logger.info('Старт процесса завершения смены')
    try:
        work_shift = await employee.work_shifts.aget(
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
    logger.debug('employee: %s', employee)
    logger.debug('work_shift: %s', work_shift)

    logger.debug('Фиксируем завершение смены в БД')
    work_shift.shift_end_at = timezone.now()
    work_shift.is_works = False
    await work_shift.asave()
    await message.answer('Смена окончена. Пока 👋')

    logger.info('Отправляю уведомление менеджеру')
    for manager in employee.managers.all():
        await message.bot.send_message(
            manager.tg_id,
            f'Сотрудник: {html.code(employee.name)}\nЗавершил смену',
        )
