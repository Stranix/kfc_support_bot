import asyncio
import logging

import aiohttp

from aiohttp import ClientTimeout

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext

from django.conf import settings
from asgiref.sync import sync_to_async

from src.models import CustomUser
from src.models import Server
from src.bot import keyboards
from src.bot.scheme import SyncStatus
from src.bot.utils import sync_referents
from src.bot.handlers.synchronizations.sync_report import report_save_in_db
from src.bot.handlers.synchronizations.sync_report import create_sync_report

logger = logging.getLogger('support_bot')
router = Router(name='sync_transits_handlers')


class SyncTrState(StatesGroup):
    tr_choice = State()


@router.message(Command('sync_tr'))
async def cmd_sync_tr(message: types.Message, state: FSMContext):
    logging.info(
        'Запрос на запуск синхронизации транзитов от %s',
        message.from_user.full_name
    )
    await state.set_state(SyncTrState.tr_choice)
    await message.reply(
        text='Какие транзиты будем синхронизировать?',
        reply_markup=await keyboards.get_choice_tr_keyboard()
    )


@router.callback_query(SyncTrState.tr_choice, F.data.startswith('tr_'))
async def process_start_sync_tr(
        query: types.CallbackQuery,
        employee: CustomUser,
        state: FSMContext
):
    logger.debug('query: %s', query)
    transits_group = query.data.split('_')[1]
    sync_statuses = await start_synchronized_transits(transits_group)
    message_for_send, _ = await create_sync_report(sync_statuses)
    sync_report = await report_save_in_db(
        employee,
        'Transit',
        sync_statuses,
        transits_group,
    )
    await query.message.delete()
    await query.message.answer(
        message_for_send,
        reply_markup=await keyboards.get_report_keyboard(sync_report.id),
    )
    await state.clear()


async def start_synchronized_transits(transit_owner: str) -> list[SyncStatus]:
    logger.info('Запуск синхронизации транзитов %s', transit_owner)
    conn = aiohttp.TCPConnector(ssl=settings.SSL_CONTEXT)
    transits = await get_transits_server_by_owner(transit_owner)

    async with aiohttp.ClientSession(
            trust_env=True,
            connector=conn,
            raise_for_status=True,
            timeout=ClientTimeout(total=settings.SYNC_TIMEOUT)
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
