import concurrent
import logging
import time
from concurrent.futures.process import ProcessPoolExecutor

from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from loader import dp
from services.synchronization import get_rest_info_by_code, sync_rep, check_sync_status, get_all_rest_ip, \
    check_conn_to_main_server


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
        await message.reply('Введите код ресторана(групп кодов через пробел). \nНапример: 5028 12 1840',
                            reply_markup=markup)
    else:
        await message.reply('Принял \nОжидайте...', reply_markup=markup)

        all_rests = get_all_rest_ip()
        start = time.time()
        with ProcessPoolExecutor(max_workers=10) as executor:
            for web_link, sync_result in zip(all_rests, executor.map(sync_rep, all_rests)):
                logging.info('Start: {} Sync_result: {}'.format(web_link, sync_result))

        await message.answer(f'Синхронизация запущена\nЗа {time.time() - start}')
        await state.finish()


@dp.message_handler(filters.Regexp(regexp=r'^(\d{2,4}\s?)+'), state=SyncRep.restaurants)
async def process_restaurants(message: types.Message, regexp, state: FSMContext):
    async with state.proxy() as data:
        data['restaurants'] = regexp.group()

    logging.info(f'Получил ресторан(ы): {data["restaurants"]}')
    codes = str(data["restaurants"]).split(' ')
    rest_info = list()
    for code in codes:
        rest_info.append(get_rest_info_by_code(code))
    for rest in rest_info:
        test = sync_rep(rest['web_link'])
    print(test)
    await state.finish()


@dp.message_handler(state=SyncRep.restaurants)
async def process_code_invalid(message: types.Message):
    return await message.reply(f'неверный формат')
