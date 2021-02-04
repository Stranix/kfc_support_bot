import concurrent
import logging
from concurrent.futures.process import ProcessPoolExecutor

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from loader import dp
from services.synchronization import get_rest_info_by_code, sync_rep, check_sync_status


class SyncRep(StatesGroup):
    choice_sync_rest = State()
    restaurants = State()


@dp.message_handler(commands='sync_rest')
async def cmd_sync_rest(message: Message):
    await SyncRep.choice_sync_rest.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Один(Группу)", "Все")
    await message.reply("Выберите параметры синхронизации ресторана(ов): ", reply_markup=markup)


@dp.message_handler(state=SyncRep.choice_sync_rest)
async def process_choice_sync_rest(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['choice_sync_rest'] = message.text

    markup = types.ReplyKeyboardRemove()

    if data['choice_sync_rest'] == 'Один(Группу)':
        await SyncRep.next()
        logging.info(f"Выбран параметр шаг 1: {data['choice_sync_rest']}")
        await message.reply('Введите группу ресторанов (через пробел). \nНапример: 5028 12 1840', reply_markup=markup)
    else:
        await message.reply('будет запущена синхронизация по всем ресторанам', reply_markup=markup)
        await state.finish()


@dp.message_handler(state=SyncRep.restaurants)
async def process_restaurants(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['restaurants'] = message.text

    await message.reply('Данные получены, запускаю синхронизацию. \nОжидайте...')
    logging.info(f'Получил ресторан(ы): {data["restaurants"]}')
    rests = str(data["restaurants"]).split(' ')
    rest_with_start_sync = []
    for rest in rests:
        logging.info(f'Запуск синхронизации для ресторана: {rest}')
        rest_info = get_rest_info_by_code(rest)
        logging.debug(f'рест инфо: {rest_info}')
        if sync_rep(rest_info['web_link']):
            logging.info('Старт синхронизации: Успех')
            rest_with_start_sync.append(rest_info['web_link'])
        else:
            logging.error('Старт синхронизации: Ошибка')
    if len(rest_with_start_sync) > 0:
        with ProcessPoolExecutor(max_workers=5) as executor:
            for web_link, sync_result in zip(rest_with_start_sync, executor.map(check_sync_status, rest_with_start_sync)):
                logging.info('Start: {} Sync_result: {}'.format(web_link, sync_result))
    await state.finish()
