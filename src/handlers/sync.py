import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup

from src.keyboards import get_choice_tr_keyboard
from src.utils import start_synchronized_transits

logger = logging.getLogger('support_bot')


class SyncTrState(StatesGroup):
    waiting_for_tr_choice = State()


def register_handlers_sync(dp: Dispatcher):
    logger.info('Регистрация команд синхронизации')
    dp.register_message_handler(sync_tr_start, commands='sync_tr', state='*')
    dp.register_callback_query_handler(sync_tr_choice, state=SyncTrState)


async def sync_tr_start(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncTrState.waiting_for_tr_choice.state)
    await message.reply(
        text='Какие транзиты будем синхронизировать?',
        reply_markup=get_choice_tr_keyboard()
    )


async def sync_tr_choice(query: types.CallbackQuery, state: FSMContext):
    sync_report = {
        'ok': [],
        'error': [],
    }

    sync_statuses = await start_synchronized_transits(query.data)

    for sync_status in sync_statuses:
        if sync_status.status == 'ok':
            sync_report['ok'].append(sync_status)
        else:
            sync_report['error'].append(sync_status)
    message_for_send = md.text(
        'Статус синхронизации транзитов:\n',
        md.text('Успешно: ', md.hcode(len(sync_report['ok']))),
        md.text('Ошибок: ', md.hcode(len(sync_report['error'])))
    )
    await query.message.delete()
    await query.message.answer(
        message_for_send,
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.finish()
