import logging

import pytest

from src.utils import check_conn_to_main_server, sync_referents


@pytest.mark.asyncio
async def test_check_conn_to_main_server_fail(caplog):
    caplog.set_level(logging.DEBUG, logger='support_bot')
    web_server_url = 'https://172.27.31.96:9002'
    conn_status = await check_conn_to_main_server(web_server_url)
    assert conn_status is False


@pytest.mark.asyncio
async def test_check_conn_to_main_server_ok(caplog):
    caplog.set_level(logging.DEBUG, logger='support_bot')
    web_server_url = 'https://172.27.31.96:8002'
    conn_status = await check_conn_to_main_server(web_server_url)
    assert conn_status is True


@pytest.mark.asyncio
async def test_sync_referents(caplog):
    caplog.set_level(logging.DEBUG, logger='support_bot')
    web_server_url = 'https://172.27.31.96:8002'
    sync_status = await sync_referents(web_server_url)
    assert sync_status.status == 'ok'
