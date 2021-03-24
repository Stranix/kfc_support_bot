import logging

from aiogram import types
from aiogram.dispatcher.filters import Command
from keyboards.choice_tr import choice_tr
from loader import dp
from services.synchronization import sync_rep, generated_links_to_sync


@dp.message_handler(Command('sync_tr'))
async def choice_tr_group(message: types.Message):
    logging.info(f'Запуск от: {message.from_user.full_name}')
    await message.reply(text='Какие транзиты будем синхронить?', reply_markup=choice_tr)


@dp.callback_query_handler(text='yum')
@dp.callback_query_handler(text='irb')
@dp.callback_query_handler(text='all')
@dp.callback_query_handler(text='cancel')
async def kb_answer_for_sync_tr(query: types.CallbackQuery):
    await query.answer()
    logging.info(f'Получен ответ: {query.data}')
    tranzit_name = ''
    if query.data == 'yum':
        tranzit_name = 'ЯМ'
    if query.data == 'irb':
        tranzit_name = 'ИРБ'

    if query.data == 'all':
        links_to_sync = generated_links_to_sync(['yum', 'irb'])
    else:
        links_to_sync = generated_links_to_sync([query.data])

    sync_results = []
    for tr in links_to_sync:
        sync_results.append(sync_rep(tr))

    sync_error = ''
    for result in sync_results:
        if result['status'] != 'In Progress':
            sync_error += f'\nTranzit: {result["web_link"]}\nStatus: {result["status"]}\n'

    if sync_error == '':
        message_for_send = f'Запуск синхронизации по транзитам {tranzit_name}: Без ошибок'
    else:
        message_for_send = 'Ошибка запуска синхронизации: \n' + sync_error

    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(message_for_send)
