import logging
import os

from aiogram import types
from aiogram.dispatcher.filters import Command

from keyboards.choice_rep_sync import choice_rep_sync
from loader import dp
from services.synchronization import get_all_rest_info, sync_rep


@dp.message_handler(Command('sync_all'))
async def choice_tr_group(message: types.Message):
    logging.info(f'Запуск от: {message.from_user.full_name}')
    await message.reply(text='Кого будем синхронить?', reply_markup=choice_rep_sync)


@dp.callback_query_handler(text='sync_irb')
@dp.callback_query_handler(text='sync_yum')
@dp.callback_query_handler(text='sync_all')
async def owner_for_sync_rest(query: types.CallbackQuery):
    await query.answer()
    logging.info(f'Получен ответ: {query.data}')
    if query.data == 'sync_yum':
        logging.info('Собираю информацию по ресторанам ЯМ!')
        owner = 'Ям Ресторантс Раша'
    elif query.data == 'sync_irb':
        owner = 'Интернэшнл Ресторант Брэндс'
    else:
        owner = 'all'

    restaurants = get_all_rest_info(owner)
    sync_start = []
    sync_error = []

    await query.message.answer(f'Ресторанов для синхронизации: {len(restaurants)}')

    for rest in restaurants:
        logging.info(f'Запуск синхронизации для ресторана {rest["name"]}')
        start_sync = sync_rep(rest['web_link'])
        rest['sync_status'] = start_sync['status']
        if start_sync['status'] == 'In Progress':
            sync_start.append(rest)
        else:
            sync_error.append(rest)

    path_to_file = r".\files\conn_error.txt"

    with open(path_to_file, "w", encoding='UTF-8') as file:
        file.writelines("%s\n" % line for line in sync_error)

    message_sync_result = f'Ok: {len(sync_start)} Error: {len(sync_error)}'

    if os.stat(path_to_file).st_size == 0:
        await query.message.answer(message_sync_result)
    else:
        doc_to_send = types.InputFile(path_to_file, filename="sync_error.txt")
        await query.message.answer_document(document=doc_to_send, caption=message_sync_result)

    await query.message.edit_reply_markup(reply_markup=None)


@dp.callback_query_handler(text='sync_cancel')
async def kb_answer_for_sync_rest(query: types.CallbackQuery):
    await query.answer()
    logging.info(f'Получен ответ: {query.data}')
    logging.info('Отменил синхронизацию')
    await query.message.edit_reply_markup(reply_markup=None)
