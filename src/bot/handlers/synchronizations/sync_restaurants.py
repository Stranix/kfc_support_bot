import asyncio
import logging

import aiohttp

from aiohttp import ClientTimeout

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram import html
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext

from asgiref.sync import sync_to_async
from django.conf import settings

from src.models import Employee
from src.models import Restaurant
from src.bot import keyboards
from src.bot.scheme import SyncStatus
from src.bot.utils import sync_referents
from src.bot.handlers.synchronizations.sync_report import report_save_in_db
from src.bot.handlers.synchronizations.sync_report import create_sync_report

logger = logging.getLogger('support_bot')
router = Router(name='sync_restaurants_handlers')


class SyncRestState(StatesGroup):
    sync_choice = State()
    rest_list = State()
    rest_group = State()


@router.message(Command('sync_rests'))
async def cmd_sync_rests(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации ресторанов от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncRestState.sync_choice)
    await message.reply(
        text='Будем синхронизировать?',
        reply_markup=await keyboards.get_choice_rest_sync_keyboard()
    )


@router.callback_query(SyncRestState.sync_choice, F.data == 'rest_list')
async def process_rest_list(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer(
        'Жду код ресторана(ов). Можно передавать через пробел\n'
        'Например: ' + html.code('5050 8080 3333')
    )
    await state.set_state(SyncRestState.rest_list)


@router.message(SyncRestState.rest_list)
async def process_sync_rest_list(
        message: types.Message,
        employee: Employee,
        state: FSMContext,
):
    logger.info('Синхронизация ресторанов по списку от пользователя')
    logger.debug('message.text: %s', message.text)
    try:
        restaurants = list(map(int, message.text.split()))
    except ValueError:
        logger.error('Не верный формат списка ресторанов')
        await message.answer(
            'Не верный формат ресторанов. Попробуйте еще раз. \n'
            'Пример правильной записи: ' + html.code('5050 8080 3333')
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
        employee,
        'Report',
        sync_statuses,
        'rest_list',
    )
    await message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.clear()


@router.callback_query(SyncRestState.sync_choice, F.data == 'rest_group')
async def process_rest_group(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer(
        text='Какие рестораны будем синхронизировать?',
        reply_markup=await keyboards.get_choice_rest_owner_keyboard()
    )
    await state.set_state(SyncRestState.rest_group)


@router.callback_query(SyncRestState.rest_group, F.data.startswith('rest_'))
async def process_sync_rest_group(
        query: types.CallbackQuery,
        employee: Employee,
        state: FSMContext,
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
        employee,
        'Report',
        sync_statuses,
        'rest_group',
    )
    await query.message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.clear()


@router.callback_query(SyncRestState.sync_choice, F.data == 'rest_all')
async def process_sync_rest_all(
        query: types.CallbackQuery,
        employee: Employee,
        state: FSMContext,
):
    await query.message.delete()
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
        employee,
        'Report',
        sync_statuses,
        'rest_all',
    )
    await query.message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.clear()


async def start_synchronized_restaurants(
        restaurants: list[Restaurant]
) -> list[SyncStatus]:
    logger.info('Запуск синхронизации ресторанов')
    conn = aiohttp.TCPConnector(ssl=settings.SSL_CONTEXT)

    async with aiohttp.ClientSession(
            trust_env=True,
            connector=conn,
            raise_for_status=True,
            timeout=ClientTimeout(total=settings.SYNC_TIMEOUT)
    ) as session:
        tasks = []
        for restaurant in restaurants:
            rest_web_server_url = f'https://{restaurant.server_ip}:9000/'
            task = asyncio.create_task(
                sync_referents(session, rest_web_server_url, restaurant.name)
            )
            tasks.append(task)
        sync_report = list(await asyncio.gather(*tasks))
        logger.info('Синхронизация завершена')
    return sync_report
