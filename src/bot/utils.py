import re
import asyncio
import logging

from urllib.parse import urljoin

import aiohttp
from aiogram.types import InlineKeyboardMarkup

from aiohttp import ClientSession

from aiogram import html, Bot
from aiogram import types
from asgiref.sync import sync_to_async

from bs4 import BeautifulSoup

from src.models import Employee, Group
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


async def user_registration(message: types.Message) -> Employee:
    logger.info('Регистрация пользователя')
    employee = await Employee.objects.acreate(
        name=message.from_user.full_name.replace('@', ''),
        tg_id=message.from_user.id,
        tg_nickname='@' + message.from_user.username,
    )
    senior_engineers = await get_senior_engineers()
    logger.debug('senior_engineers: %s', senior_engineers)
    notify = f'Новый пользователь \n\n' \
             f'Телеграм id: {html.code(message.from_user.id)}\n' \
             f'Телеграм username {html.code(message.from_user.username)}\n' \
             f'Имя: {html.code(message.from_user.full_name)}\n'
    logger.debug('notify: %s', notify)
    notify_keyboard = await get_user_activate_keyboard(employee.id)
    await send_notify(message.bot, senior_engineers, notify, notify_keyboard)
    await message.answer('Заявка на регистрацию отправлена.')
    return employee


async def send_notify(
        bot: Bot,
        employees: list[Employee],
        message: str,
        keyboard: InlineKeyboardMarkup = None,
):
    logger.info('Отправка уведомления')
    if not employees:
        logger.warning('Пустой список для отправки уведомлений')
        return
    for employee in employees:
        logger.debug('Уведомление для: %s', employee.name)
        await bot.send_message(employee.tg_id, message, reply_markup=keyboard)
    logger.info('Отправка уведомлений завершена')


async def get_senior_engineers() -> list[Employee] | None:
    senior_engineers_group = await Group.objects.aget(name='Ведущие инженеры')
    senior_engineers = await sync_to_async(list)(
        Employee.objects.filter(
            groups=senior_engineers_group,
        )
    )
    logger.debug('senior_engineers: %s', senior_engineers)
    if not senior_engineers:
        logger.error('В системе не назначены ведущие инженеры')
        return
    return senior_engineers
