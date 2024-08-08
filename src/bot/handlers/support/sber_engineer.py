import logging

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext

from src.entities.Message import Message
from src.entities.Scheduler import Scheduler
from src.entities.SberEngineer import SberEngineer

from src.bot import dialogs

logger = logging.getLogger('support_bot')
router = Router(name='sber_engineers_handlers')


class SberNewTaskState(StatesGroup):
    waiting_rest_code = State()
    rest_code = State()
    waiting_description = State()
    description = State()
    approved = State()


@router.message(Command('help_sber'))
async def help_sber_start(message: types.Message, state: FSMContext):
    logger.info('Запрос помощи от инженера Сбер')
    await message.answer('Напишите номер ресторана в котором находитесь')
    await state.set_state(SberNewTaskState.waiting_rest_code)


@router.message(SberNewTaskState.waiting_rest_code)
async def help_sber_start_step_2(message: types.Message, state: FSMContext):
    logger.info('Обработка номера ресторана от инженера сбер')
    await state.update_data(rest_code=message.text)
    await message.answer(await dialogs.request_task_description())
    await state.set_state(SberNewTaskState.waiting_description)
    logger.info('Обработано')


@router.message(SberNewTaskState.waiting_description)
async def help_sber_start_step_3(message: types.Message, state: FSMContext):
    logger.info('Получение описания по задаче')
    task_description = message.text
    if not task_description:
        await message.answer(await dialogs.error_wrong_task_description())
        return
    data = await state.get_data()
    rest_code = data['rest_code']
    await state.update_data(description=task_description)
    text, keyboard = await dialogs.sber_request_task_confirmation(
        rest_code,
        task_description,
    )
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(SberNewTaskState.approved)
    logger.info('Описание получено')


@router.callback_query(F.data.startswith('sber_approved_new_task'))
async def help_sber_start_step_4(
        query: types.CallbackQuery,
        sber_engineer: SberEngineer,
        scheduler: Scheduler,
        state: FSMContext,
):
    logger.info('Процесс подтверждения и создания новой заявки для сбер')
    await query.message.edit_text(await dialogs.waiting_creating_task())
    data = await state.get_data()
    logger.debug('state_data: %s', data)
    task = await sber_engineer.create_sd_task_to_help(
        data['rest_code'],
        data['description'],
    )
    await scheduler.add_new_task_schedulers(task)
    await Message.send_new_task_notify(task)
    edit_text = await dialogs.new_task_notify_for_creator(
        task.number,
        task.title,
    )
    await query.message.edit_text(edit_text)
    await state.clear()
    logger.info('Процесс завершен')
