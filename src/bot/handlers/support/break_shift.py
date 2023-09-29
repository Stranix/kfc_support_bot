import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from django.utils import timezone

from src.models import WorkShift
from src.models import Employee

logger = logging.getLogger('support_bot')


class WorkShiftBreakState(StatesGroup):
    break_status: State()


async def break_shift(message: types.Message, state: FSMContext):
    logger.info('Запрос сотрудника на перерыв')
    keyboard = ''
    await state.set_state(WorkShiftBreakState.break_status)
    await message.answer('Перерыв. Выберете действие', reply_markup=keyboard)


async def start_break_shift(query: types.CallbackQuery, state: FSMContext):
    work_shift = await state.get_data(query.from_user.id)
    logger.debug('Фиксируем перерыв в БД')
    shift: WorkShift = work_shift.get('shift')
    employee: Employee = work_shift.get('emp')

    shift.shift_start_break_at = timezone.now()
    shift.is_works = False
    await shift.asave()
    logger.info('Отправляю уведомление менеджеру и пользователю')
    await query.answer('Зафиксировал перерыв', show_alert=True)
    for manager in employee.managers.all():
        await query.bot.send_message(
            manager.tg_id,
            md.text(
                'Сотрудник: ' + md.hcode(employee.name),
                '\nУшел на перерыв',
            ),
        )



async def stop_break_shift(query: types.CallbackQuery, state: FSMContext):
    work_shift = await state.get_data(query.from_user.id)
    logger.debug('Фиксируем Завершение перерыва в БД')
    shift: WorkShift = work_shift.get('shift')
    employee: Employee = work_shift.get('emp')

    shift.shift_end_break_at = timezone.now()
    shift.is_works = True
    await shift.asave()
    logger.info('Отправляю уведомление менеджеру и пользователю')
    await query.answer('Перерыв окончен', show_alert=True)
    for manager in employee.managers.all():
        await query.bot.send_message(
            manager.tg_id,
            md.text(
                'Сотрудник: ' + md.hcode(employee.name),
                '\nПришел с перерыва',
            ),
        )
