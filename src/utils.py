import re
import logging

from urllib.parse import urljoin

import requests

from bs4 import BeautifulSoup

from src.scheme import SyncStatus

logger = logging.getLogger('support_bot')


async def sync_referents(web_server_url: str) -> SyncStatus:
    logger.info('Запуск синхронизации для: %s', web_server_url)
    sync_status = SyncStatus(web_link=web_server_url)
    try:
        link_to_sync = urljoin(web_server_url, '/rk7api/v1/forcesyncrefs.xml')
        check_conn = await check_conn_to_main_server(web_server_url)

        if not check_conn:
            sync_status.status = 'error'
            sync_status.msg = 'Нет соединения с транзитом'

        response = requests.get(link_to_sync, verify=False, timeout=3)
        response.raise_for_status()
        return sync_status
    except requests.exceptions.ConnectTimeout:
        sync_status.status = 'error'
        sync_status.msg = 'Отсутствует подключение к транзиту'
        return sync_status


async def check_conn_to_main_server(web_server_url: str) -> bool:
    logger.info('Старт проверки подключения к вышестоящему серверу')
    conn_tab = urljoin(web_server_url, 'Connects')

    response = requests.get(conn_tab, verify=False, timeout=3)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    main_server = soup.find_all(
        string=[re.compile('TRANSIT'), re.compile('CENT')]
    )
    logger.debug('main_server: %s', main_server)

    if not main_server:
        logger.warning('Сервер %s не подключен к транзиту', web_server_url)
        return False

    logger.debug(
        'Сервер %s подключен к транзиту %s',
        web_server_url, main_server
    )
    return True
