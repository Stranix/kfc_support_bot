import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup
from asgiref.sync import sync_to_async

from src.bot import keyboards
from src.bot import utils
from src.models import Restaurant

logger = logging.getLogger('support_bot')


class SyncTrState(StatesGroup):
    waiting_for_tr_choice = State()


class SyncRestState(StatesGroup):
    waiting_for_choice = State()
    waiting_rest_list = State()
    waiting_rest_group = State()


def register_handlers_sync(dp: Dispatcher):
    logger.info('Регистрация команд синхронизации')
    dp.register_message_handler(
        sync_tr_start,
        commands='sync_tr',
        state='*',
    )
    dp.register_message_handler(
        sync_rest_start,
        commands='sync_rest',
        state='*',
    )
    dp.register_callback_query_handler(
        sync_tr_choice,
        lambda call: call.data in ('yum', 'irb', 'fz', 'all'),
        state=SyncTrState,
    )
    dp.register_message_handler(
        start_sync_restaurants_by_list,
        state=SyncRestState.waiting_rest_list,
    )
    dp.register_callback_query_handler(
        start_sync_restaurants_by_group,
        state=SyncRestState.waiting_rest_group,
    )
    dp.register_callback_query_handler(
        sync_rest_choice,
        state=SyncRestState,
    )


async def sync_tr_start(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncTrState.waiting_for_tr_choice.state)
    await message.reply(
        text='Какие транзиты будем синхронизировать?',
        reply_markup=keyboards.get_choice_tr_keyboard()
    )


async def sync_tr_choice(query: types.CallbackQuery, state: FSMContext):
    sync_statuses = await utils.start_synchronized_transits(query.data)
    message_for_send, _ = await utils.create_sync_report(sync_statuses)
    await query.message.delete()
    await query.message.answer(
        message_for_send,
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.finish()


async def sync_rest_start(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации ресторанов от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncRestState.waiting_for_choice.state)
    await message.reply(
        text='Будем синхронизировать?',
        reply_markup=keyboards.get_choice_rest_sync_keyboard()
    )


async def sync_rest_choice(query: types.CallbackQuery, state: FSMContext):
    user_choice = query.data
    await query.message.delete()

    if user_choice == 'rest_list':
        await query.message.answer(
            md.text(
                'Жду код ресторана(ов). Можно передавать через пробел\n' +
                'Например: ' + md.hcode('5050 8080 3333')
            )
        )
        await state.set_state(SyncRestState.waiting_rest_list.state)

    if user_choice == 'rest_group':
        await query.message.answer(
            text='Какие рестораны будем синхронизировать?',
            reply_markup=keyboards.get_choice_rest_owner_keyboard()
        )
        await state.set_state(SyncRestState.waiting_rest_group.state)

    if user_choice == 'rest_all':
        logger.info('Выбраны все рестораны для синхронизации')
        restaurants = await sync_to_async(list)(
            Restaurant.objects.filter(
                server_ip__isnull=False,
                is_sync=True,
            )
        )
        sync_statuses = await utils.start_synchronized_restaurants(restaurants)
        message_for_send, _ = await utils.create_sync_report(sync_statuses)
        await query.message.answer(message_for_send)
        await state.finish()


async def start_sync_restaurants_by_list(
        message: types.Message,
        state: FSMContext
):
    logger.info('Синхронизация ресторанов по списку от пользователя')
    logger.debug('message.text: %s', message.text)
    try:
        restaurants = list(map(int, message.text.split()))
    except ValueError:
        logger.error('Не верный формат списка ресторанов')
        await message.answer(
            md.text(
                'Не верный формат ресторанов. Попробуйте еще раз. \n' +
                'Пример правильной записи: ' + md.hcode('5050 8080 3333')
            )
        )
        return

    restaurants = await sync_to_async(list)(
            Restaurant.objects.filter(
                server_ip__isnull=False,
                code__in=restaurants,
                is_sync=True,
            )
        )
    logger.debug('Нашел рестораны: %s', restaurants)
    sync_statuses = await utils.start_synchronized_restaurants(restaurants)
    message_for_send, _ = await utils.create_sync_report(sync_statuses)
    await message.answer(message_for_send)


async def start_sync_restaurants_by_group(
        query: types.CallbackQuery,
        state: FSMContext
):
    logger.info('Синхронизация ресторанов по выбранной группе')
    user_choice = query.data.split('_')[1]
    logger.debug('user_choice: %s', user_choice)
    await query.message.delete()
    restaurants = await sync_to_async(list)(
        Restaurant.objects.filter(
            server_ip__isnull=False,
            franchise__alias=user_choice,
            is_sync=True,
        )
    )
    logger.debug('Нашел рестораны: %s', restaurants)
    sync_statuses = await utils.start_synchronized_restaurants(restaurants)
    message_for_send, _ = await utils.create_sync_report(sync_statuses)
    await query.message.answer(message_for_send)
