import re
import asyncio
import logging

from urllib.parse import urljoin

import aiohttp

from aiohttp import ClientSession

from aiogram import html
from aiogram import types

from bs4 import BeautifulSoup

from django.conf import settings

from src.models import Employee
from src.bot.scheme import SyncStatus
from src.bot.keyboards import get_user_activate_keyboard

logger = logging.getLogger('support_bot')


async def sync_referents(
        session: ClientSession,
        web_server_url: str,
        server_name: str,
) -> SyncStatus:
    logger.info('Запуск синхронизации для: %s', web_server_url)
    sync_status = SyncStatus(web_link=web_server_url, server_name=server_name)
    try:
        link_to_sync = urljoin(web_server_url, '/rk7api/v1/forcesyncrefs.xml')
        check_conn = await check_conn_to_main_server(session, web_server_url)
        if not check_conn:
            sync_status.status = 'error'
            sync_status.msg = 'Нет соединения с вышестоящим транзитом'
        async with session.get(link_to_sync) as response:
            logger.debug('response_status: %s', response.status)
        return sync_status
    except asyncio.TimeoutError:
        sync_status.status = 'error'
        sync_status.msg = 'Отсутствует подключение к серверу (timeout)'
        return sync_status
    except aiohttp.ClientConnectionError as error:
        logger.debug('ClientConnectionError: %s', error.args)
        sync_status.status = 'error'
        sync_status.msg = 'Отсутствует подключение к серверу'
        return sync_status
    except aiohttp.ClientResponseError:
        sync_status.status = 'error'
        sync_status.msg = 'Ошибка авторизации'
        return sync_status


async def check_conn_to_main_server(
        session: ClientSession,
        web_server_url: str
) -> bool:
    logger.debug('Старт проверки подключения к вышестоящему серверу')
    conn_tab = urljoin(web_server_url, 'Connects')

    async with session.get(conn_tab) as response:
        soup = BeautifulSoup(await response.text(), 'lxml')

    main_server = soup.find_all(
        string=[
            re.compile('TRANSIT'),
            re.compile('CENT')
        ],
    )
    logger.debug('main_server: %s', main_server)

    if not main_server:
        logger.warning('Сервер %s не подключен к транзиту', web_server_url)
        return False

    logger.debug(
        'Сервер %s подключен к транзиту %s',
        web_server_url,
        main_server,
    )
    return True


async def user_registration(message: types.Message):
    logger.info('Регистрация пользователя')
    employee = await Employee.objects.acreate(
        name=message.from_user.full_name,
        tg_id=message.from_user.id,
        tg_nickname='@' + message.from_user.username,
    )
    await message.bot.send_message(
        chat_id=settings.TG_BOT_ADMIN,
        text='Новый пользователь \n\n'
             'Данные: \n' + html.code(message.from_user),
        reply_markup=await get_user_activate_keyboard(employee.id),
    )
    await message.answer('Заявка на регистрацию отправлена.')
