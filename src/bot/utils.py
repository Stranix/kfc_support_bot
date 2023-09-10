import re
import asyncio
import logging

from urllib.parse import urljoin

import aiohttp

from aiohttp import ClientSession
from aiohttp import ClientTimeout

from django.conf import settings
from asgiref.sync import sync_to_async

from bs4 import BeautifulSoup

from src.models import Server
from src.bot.scheme import SyncStatus

logger = logging.getLogger('support_bot')


async def sync_referents(
        session: ClientSession,
        web_server_url: str,
) -> SyncStatus:
    logger.info('Запуск синхронизации для: %s', web_server_url)
    sync_status = SyncStatus(web_link=web_server_url)
    try:
        link_to_sync = urljoin(web_server_url, '/rk7api/v1/forcesyncrefs.xml')
        check_conn = await check_conn_to_main_server(session, web_server_url)
        if not check_conn:
            sync_status.status = 'error'
            sync_status.msg = 'Нет соединения с вышестоящим транзитом'
        async with session.get(link_to_sync) as response:
            response.raise_for_status()
        return sync_status
    except (asyncio.TimeoutError, aiohttp.ClientConnectionError):
        sync_status.status = 'error'
        sync_status.msg = 'Отсутствует подключение к транзиту'
        return sync_status


async def check_conn_to_main_server(
        session: ClientSession,
        web_server_url: str
) -> bool:
    logger.info('Старт проверки подключения к вышестоящему серверу')
    conn_tab = urljoin(web_server_url, 'Connects')

    async with session.get(conn_tab) as response:
        response.raise_for_status()
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


async def start_synchronized_transits(transit_owner: str) -> list[SyncStatus]:
    logger.info('Запуск синхронизации транзитов %s', transit_owner)
    conn = aiohttp.TCPConnector(ssl_context=settings.SSL_CONTEXT)
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
                sync_referents(session, tr_web_server_url))
            tasks.append(task)

        sync_report = list(await asyncio.gather(*tasks))
        logger.debug('sync_report: %s', sync_report)
    return sync_report


@sync_to_async
def get_transits_server_by_owner(transit_owner: str) -> list[Server]:
    logger.info('Получаем список транзитов из базы по владельцу')
    transits = Server.objects.filter(
        franchise_owner__alias=transit_owner,
        is_sync=True,
    )
    if transit_owner == 'all':
        transits = Server.objects.filter(
            franchise_owner__alias__in=('yum', 'irb'),
            is_sync=True,
        )
    logger.info('Успешно')
    logger.debug('transits: %s', transits)
    return list(transits)
