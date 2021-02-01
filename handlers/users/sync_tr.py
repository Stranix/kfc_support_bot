import logging

from aiogram import types
from aiogram.dispatcher.filters import Command
from keyboards.choice_tr import choice_tr
from loader import dp


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
    if query.data == 'yum':
        logging.info('Запускаю синхронизацию по транзитам ЯМ!')
        await query.message.answer(f'Запускаю синхронизацию по транзитам: {query.data}')
    elif query.data == 'irb':
        logging.info('Запускаю синхронизацию по транзитам IRB')
        await query.message.answer(f'Запускаю синхронизацию по транзитам: {query.data}')
    elif query.data == 'all':
        logging.info('Запускаю синхронизацию по всем транзитам')
        await query.message.answer(f'Запускаю синхронизацию по всем транзитам')
    elif query.data == 'cancel':
        logging.info('Отменил синхронизацию транзитов')
        await query.message.edit_reply_markup(reply_markup=None)
    else:
        logging.error('Не выбран транзит для синхронизации!')

    sync_result = 'Результат синхронизации: ОК'
    await query.message.answer(sync_result)
