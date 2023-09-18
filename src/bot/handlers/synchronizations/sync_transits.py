import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup

from src.bot import keyboards
from src.bot import utils

logger = logging.getLogger('support_bot')


class SyncTrState(StatesGroup):
    waiting_for_tr_choice = State()


async def start(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncTrState.waiting_for_tr_choice.state)
    await message.reply(
        text='Какие транзиты будем синхронизировать?',
        reply_markup=keyboards.get_choice_tr_keyboard()
    )


async def choice(query: types.CallbackQuery, state: FSMContext):
    sync_statuses = await utils.start_synchronized_transits(query.data)
    message_for_send, _ = await utils.create_sync_report(sync_statuses)
    await query.message.delete()
    await query.message.answer(
        message_for_send,
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.finish()
