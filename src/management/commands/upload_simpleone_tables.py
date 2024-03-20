import asyncio
import logging
from urllib.parse import urljoin

from aiohttp import ContentTypeError
from django.core.management.base import BaseCommand
from django.db.models import Model

from src.entities.SimpleOneClient import SimpleOneClient
from src.utils import configure_logging
from src.models import SimpleOneRequestType
from src.models import SimpleOneSupportGroup
from src.models import SimpleOneCompany
from src.models import SimpleOneCIService

logger = logging.getLogger('upload_simpleone_tables')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            asyncio.run(upload())
        except ContentTypeError:
            logger.error('Не смог получить токен. Выгрузка не возможна')
        except Exception as err:
            logger.exception(err)


async def upload():
    tables = [
        ('sys_group', SimpleOneSupportGroup),
        ('org_company', SimpleOneCompany),
        ('sys_rmc_model', SimpleOneRequestType),
        ('sys_cmdb_ci_service', SimpleOneCIService),
    ]
    simpleone_client = SimpleOneClient()
    await simpleone_client.get_token()
    for table, db in tables:
        url = urljoin(simpleone_client.api, f'table/{table}')
        params = {'sysparm_fields': 'sys_id,name'}
        if table == 'sys_rmc_model':
            params['sysparm_fields'] = 'sys_id,title'
        logger.debug('url: %s, params: %s', url, params)
        table_info = await simpleone_client.send_get_request(url, params)
        logger.debug('table_info:', table_info)
        await save_in_db(table_info, db)


async def save_in_db(task_info: dict, db: Model):
    for item in task_info['data']:
        sys_id = int(item['sys_id'])
        name = item.get('name', False)
        if not name:
            name = item['title']
        try:
            await db.objects.aget(id=sys_id)
        except db.DoesNotExist:
            logger.info('Отсутствует %s в базе. Сохраняю', sys_id)
            await db.objects.acreate(id=sys_id, name=name)
            logger.info('Успешно')
