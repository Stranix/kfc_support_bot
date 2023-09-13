import asyncio
import logging

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import ClientTimeout
from django.conf import settings

from src.bot.utils import sync_referents
from src.bot.utils import check_conn_to_main_server
from src.bot.utils import start_synchronized_transits


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='module')
async def get_client_session():
    conn = aiohttp.TCPConnector(ssl=settings.SSL_CONTEXT)
    async with aiohttp.ClientSession(
        trust_env=True,
        connector=conn,
        raise_for_status=True,
        timeout=ClientTimeout(total=3)
    ) as client_session:
        yield client_session
    await client_session.close()


class TestSync:
    @pytest.mark.asyncio
    async def test_check_conn_to_main_server_fail(
            self,
            get_client_session,
            caplog
    ):
        caplog.set_level(logging.DEBUG, logger='support_bot')
        web_server_url = 'https://172.27.31.96:9002'
        conn_status = await check_conn_to_main_server(
            get_client_session,
            web_server_url
        )
        assert conn_status is False

    @pytest.mark.asyncio
    async def test_check_conn_to_main_server_ok(
            self,
            get_client_session,
            caplog
    ):
        caplog.set_level(logging.DEBUG, logger='support_bot')
        web_server_url = 'https://172.27.31.96:8002'
        conn_status = await check_conn_to_main_server(
            get_client_session,
            web_server_url
        )
        assert conn_status is True

    @pytest.mark.asyncio
    async def test_sync_referents(
            self,
            get_client_session,
            caplog
    ):
        caplog.set_level(logging.DEBUG, logger='support_bot')
        web_server_url = 'https://172.27.31.96:8002'
        sync_status = await sync_referents(get_client_session, web_server_url)
        assert sync_status.status == 'ok'

    @pytest.mark.asyncio
    async def test_start_synchronized_transits(self, caplog):
        caplog.set_level(logging.DEBUG, logger='support_bot')
        sync_status = await start_synchronized_transits('fz')
        assert isinstance(sync_status, list) is True
