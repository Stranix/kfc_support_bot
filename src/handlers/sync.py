import logging
import json
import os

import aiogram.utils.markdown as md

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup

from src.keyboards import get_choice_tr_keyboard
from src.utils import sync_referents

logger = logging.getLogger('support_bot')


class SyncTrState(StatesGroup):
    waiting_for_tr_choice = State()


def register_handlers_sync(dp: Dispatcher):
    logger.info('Регистрация команд синхронизации')
    dp.register_message_handler(sync_tr_start, commands='sync_tr', state='*')
    dp.register_callback_query_handler(sync_tr_choice, state='*')


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
    call_back_answer = query.data
    tr_settings = os.path.join('./', 'config/tr_settings.json')
    with open(tr_settings) as json_file:
        transits = json.load(json_file)

    logger.debug('Загруженные данные по транзитам: %s', transits)

    if call_back_answer == 'cancel':
        await state.finish()
        await query.message.delete()
        await query.answer('Действие отменено', show_alert=True)

    sync_report = {
        'ok': [],
        'error': [],
    }
    for tr_port in range(*transits[call_back_answer]['ports_range']):
        tr_ip = transits[call_back_answer]['ip']
        tr_web_server_url = f'https://{tr_ip}:{tr_port}/'
        sync_info = await sync_referents(tr_web_server_url)

        if sync_info.status == 'error':
            sync_report['error'].append(sync_info)
        if sync_info.status == 'ok':
            sync_report['ok'].append(sync_info)

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
