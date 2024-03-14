import re
import asyncio
import logging

from urllib.parse import urljoin

import aiohttp

from aiohttp import ClientSession

from asgiref.sync import sync_to_async

from aiogram import html
from aiogram import types

from bs4 import BeautifulSoup

from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group as DjangoGroup

from src.models import CustomUser
from src.bot.scheme import SyncStatus
from src.bot.scheme import TelegramUser
from src.entities.Message import Message
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


async def user_registration(message: types.Message) -> CustomUser:
    logger.info('Регистрация нового пользователя')
    employee = await CustomUser.objects.acreate(
        login=message.from_user.username,
        name=message.from_user.full_name.replace('@', ''),
        tg_id=message.from_user.id,
        tg_nickname=message.from_user.username,
    )
    notify = f'Новый пользователь \n\n' \
             f'Телеграм id: {html.code(message.from_user.id)}\n' \
             f'Телеграм username: @{message.from_user.username}\n' \
             f'Имя: {html.code(message.from_user.full_name)}\n'
    logger.debug('notify: %s', notify)
    notify_keyboard = await get_user_activate_keyboard(employee.id)
    await Message.send_notify_to_seniors_engineers(notify, notify_keyboard)
    await message.answer('Заявка на регистрацию отправлена.')
    return employee


async def get_tg_user_info_from_event(event: types.Update) -> TelegramUser:
    logger.debug('Получаем информацию о пользователе из telegram update')
    tg_id = 0
    nickname = ''
    if event.callback_query:
        logger.debug('event_type: callback_query')
        tg_id = event.callback_query.from_user.id
        nickname = event.callback_query.from_user.username
    if event.message:
        logger.debug('event_type: message')
        tg_id = event.message.from_user.id
        nickname = event.message.from_user.username
    telegram_user = TelegramUser(tg_id, nickname)
    logger.debug('TelegramUser: %s', telegram_user)
    return telegram_user


@sync_to_async
def has_perm(perm_codename: str, employee: CustomUser) -> bool:
    if has_perm_in_group(perm_codename, employee.groups.all()):
        return True
    logger.debug('Ищем права у пользователя')
    employee_permissions = Permission.objects.filter(user=employee)
    if employee_permissions.filter(codename=perm_codename).exists():
        logger.debug('У пользователя есть право на синхронизацию')
        return True
    return False


def has_perm_in_group(perm_codename: str, groups: list[DjangoGroup]) -> bool:
    for group in groups:
        perm_exists = group.permissions.filter(codename=perm_codename).exists()
        if perm_exists:
            logger.debug('Нашел право %s в группе %s', perm_codename, group)
            return True
    logger.debug('Нет права %s в группах пользователя', perm_codename)
    return False
