import logging

import aiogram.utils.markdown as md

from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup

from django.utils import timezone

from src.models import WorkShift
from src.models import Employee

logger = logging.getLogger('support_bot')
router = Router(name='break_shift_handlers')


class WorkShiftBreakState(StatesGroup):
    break_status: State()


@router.message(Command('break_start'))
async def start_break_shift(message: types.Message):
    employee = await Employee.objects.prefetch_related(
                                        'work_shifts',
                                        'managers',
    ).aget(tg_id=message.from_user.id)
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
    work_shift.shift_start_break_at = timezone.now()
    work_shift.is_works = False
    await work_shift.asave()
    await message.answer('Ваш перерыв начат')

    logger.info('Отправляю уведомление менеджеру и пользователю')
    for manager in employee.managers.all():
        await message.bot.send_message(
            manager.tg_id,
            md.text(
                'Сотрудник: ' + md.hcode(employee.name),
                '\nУшел на перерыв',
            ),
        )


@router.message(Command('break_stop'))
async def stop_break_shift(message: types.Message):
    employee = await Employee.objects.prefetch_related(
                                        'work_shifts',
                                        'managers'
    ).aget(tg_id=message.from_user.id)
    try:
        work_shift = await employee.work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
            shift_start_break_at__isnull=False,
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
    work_shift.shift_end_break_at = timezone.now()
    work_shift.is_works = True
    await work_shift.asave()
    await message.answer('Ваш перерыв завершен')

    logger.info('Отправляю уведомление менеджеру и пользователю')
    for manager in employee.managers.all():
        await message.bot.send_message(
            manager.tg_id,
            md.text(
                'Сотрудник: ' + md.hcode(employee.name),
                '\nЗавершил перерыв',
            ),
        )
