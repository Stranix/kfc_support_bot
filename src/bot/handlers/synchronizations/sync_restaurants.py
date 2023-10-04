import asyncio
import logging

import aiohttp
from aiohttp import ClientTimeout

import aiogram.utils.markdown as md

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup

from asgiref.sync import sync_to_async
from django.conf import settings

from src.bot import keyboards
from src.bot.handlers.synchronizations.sync_report import report_save_in_db
from src.bot.handlers.synchronizations.sync_report import create_sync_report
from src.bot.scheme import SyncStatus
from src.bot.utils import sync_referents
from src.models import Restaurant

logger = logging.getLogger('support_bot')


class SyncRestState(StatesGroup):
    waiting_for_choice = State()
    waiting_rest_list = State()
    waiting_rest_group = State()


async def start(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации ресторанов от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncRestState.waiting_for_choice.state)
    await message.reply(
        text='Будем синхронизировать?',
        reply_markup=await keyboards.get_choice_rest_sync_keyboard()
    )


async def choice(query: types.CallbackQuery, state: FSMContext):
    user_choice = query.data
    await query.message.delete()

    if user_choice == 'rest_list':
        await query.message.answer(
            md.text(
                'Жду код ресторана(ов). Можно передавать через пробел\n',
                'Например: ' + md.hcode('5050 8080 3333')
            )
        )
        await state.set_state(SyncRestState.waiting_rest_list.state)

    if user_choice == 'rest_group':
        await query.message.answer(
            text='Какие рестораны будем синхронизировать?',
            reply_markup=await keyboards.get_choice_rest_owner_keyboard()
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
        sync_statuses = await start_synchronized_restaurants(restaurants)
        message_for_send, _ = await create_sync_report(sync_statuses)
        sync_report = await report_save_in_db(
            query.from_user.id,
            'Report',
            sync_statuses,
            user_choice,
        )
        await query.message.answer(
            message_for_send,
            reply_markup=await keyboards.get_report_keyboard(sync_report.id),
        )
        await state.finish()


async def sync_by_list(
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
                'Не верный формат ресторанов. Попробуйте еще раз. \n',
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
    sync_statuses = await start_synchronized_restaurants(restaurants)
    message_for_send, _ = await create_sync_report(sync_statuses)
    sync_report = await report_save_in_db(
        message.from_user.id,
        'Report',
        sync_statuses,
        'rest_list',
    )
    await message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.finish()


async def sync_by_group(
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
    sync_statuses = await start_synchronized_restaurants(restaurants)
    message_for_send, _ = await create_sync_report(sync_statuses)
    sync_report = await report_save_in_db(
        query.from_user.id,
        'Report',
        sync_statuses,
        'rest_group',
    )
    await query.message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.finish()


async def start_synchronized_restaurants(
        restaurants: list[Restaurant]
) -> list[SyncStatus]:
    logger.info('Запуск синхронизации ресторанов %s', restaurants)
    conn = aiohttp.TCPConnector(ssl=settings.SSL_CONTEXT)

    async with aiohttp.ClientSession(
            trust_env=True,
            connector=conn,
            raise_for_status=True,
            timeout=ClientTimeout(total=5)
    ) as session:
        tasks = []
        for restaurant in restaurants:
            rest_web_server_url = f'https://{restaurant.server_ip}:9000/'
            task = asyncio.create_task(
                sync_referents(session, rest_web_server_url, restaurant.name)
            )
            tasks.append(task)

        sync_report = list(await asyncio.gather(*tasks))
        logger.debug('sync_report: %s', sync_report)
    return sync_report
