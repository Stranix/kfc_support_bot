import logging

from aiogram import Router
from aiogram import types
from aiogram import html
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup

from django.utils import timezone

from src.models import WorkShift
from src.models import BreakShift
from src.models import Employee

logger = logging.getLogger('support_bot')
router = Router(name='break_shift_handlers')


class WorkShiftBreakState(StatesGroup):
    break_status: State()


@router.message(Command('break_start'))
async def start_break_shift(message: types.Message, employee: Employee):
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

    logger.debug('Фиксируем перерыв в БД')
    if not work_shift.is_works:
        await message.answer('Есть незавершенный перерыв. Завершите его.')
        return
    await work_shift.break_shift.acreate(employee=employee)
    work_shift.is_works = False
    await work_shift.asave()
    await message.answer('Ваш перерыв начат')

    logger.info('Отправляю уведомление менеджеру и пользователю')
    for manager in employee.managers.all():
        await message.bot.send_message(
            manager.tg_id,
            f'Сотрудник: {html.code(employee.name)}\nУшел на перерыв',
        )


@router.message(Command('break_stop'))
async def stop_break_shift(message: types.Message, employee: Employee):
    try:
        work_shift = await employee.work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
        )
    except WorkShift.DoesNotExist:
        logger.warning('Не нашел активный перерыв')
        await message.answer(
            'Нет информации о начале перерыва'
            'Сначала перерыв надо начать. Используй команду: /break_start'
        )
        return
    logger.debug('employee: %s', employee)
    logger.debug('work_shift: %s', work_shift)

    logger.debug('Фиксируем завершение перерыва в БД')
    try:
        active_break = await work_shift.break_shift.select_related('employee')\
                                                   .aget(is_active=True)
    except BreakShift.DoesNotExist:
        await message.answer('У вас нет активных перерывов 🤷‍♂')
        return
    active_break.end_break_at = timezone.now()
    active_break.is_active = False
    work_shift.is_works = True
    await active_break.asave()
    await work_shift.asave()

    await message.answer('Ваш перерыв завершен')

    logger.info('Отправляю уведомление менеджеру и пользователю')
    for manager in employee.managers.all():
        await message.bot.send_message(
            manager.tg_id,
            f'Сотрудник: {html.code(employee.name)}\nЗавершил перерыв',
        )
