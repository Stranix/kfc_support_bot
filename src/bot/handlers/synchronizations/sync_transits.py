import asyncio
import logging

import aiohttp
from aiohttp import ClientTimeout

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup

from django.conf import settings
from asgiref.sync import sync_to_async

from src.bot.handlers.synchronizations.sync_report import report_save_in_db, \
    create_sync_report
from src.models import Server
from src.bot import keyboards
from src.bot.scheme import SyncStatus
from src.bot.utils import sync_referents

logger = logging.getLogger('support_bot')


class SyncTrState(StatesGroup):
    waiting_for_tr_choice = State()


async def start(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncTrState.waiting_for_tr_choice.state)
    await message.reply(
        text='Какие транзиты будем синхронизировать?',
        reply_markup=await keyboards.get_choice_tr_keyboard()
    )


async def choice(query: types.CallbackQuery, state: FSMContext):
    logger.debug('query: %s', query)

    sync_statuses = await start_synchronized_transits(query.data)
    message_for_send, _ = await create_sync_report(sync_statuses)
    sync_report = await report_save_in_db(
        query.from_user.id,
        'Transit',
        sync_statuses,
    )
    await query.message.delete()
    await query.message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.finish()


async def start_synchronized_transits(transit_owner: str) -> list[SyncStatus]:
    logger.info('Запуск синхронизации транзитов %s', transit_owner)
    conn = aiohttp.TCPConnector(ssl=settings.SSL_CONTEXT)
    transits = await get_transits_server_by_owner(transit_owner)

    async with aiohttp.ClientSession(
            trust_env=True,
            connector=conn,
            raise_for_status=True,
            timeout=ClientTimeout(total=3)
    ) as session:
        tasks = []
        for transit in transits:
            tr_web_server_url = f'https://{transit.ip}:{transit.web_server}/'
            task = asyncio.create_task(
                sync_referents(session, tr_web_server_url, transit.name)
            )
            tasks.append(task)

        sync_report = list(await asyncio.gather(*tasks))
        logger.debug('sync_report: %s', sync_report)
    return sync_report


@sync_to_async
def get_transits_server_by_owner(transit_owner: str) -> list[Server]:
    logger.info('Получаем список транзитов из базы по владельцу')
    transits = Server.objects.filter(
        franchise_owner__alias=transit_owner,
        server_type__name='Transit',
        is_sync=True,
    )
    if transit_owner == 'all':
        transits = Server.objects.filter(
            franchise_owner__alias__in=('yum', 'irb', 'fz'),
            server_type__name='Transit',
            is_sync=True,
        )
    logger.info('Успешно')
    logger.debug('transits: %s', transits)
    return list(transits)
