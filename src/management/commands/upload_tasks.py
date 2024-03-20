import asyncio
import logging

from aiohttp import ContentTypeError
from django.conf import settings
from django.core.management.base import BaseCommand

from src.entities.MailClient import MailClient
from src.utils import configure_logging

logger = logging.getLogger('upload_tasks')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            asyncio.run(fetch_mail())
        except ContentTypeError as error:
            login_url = settings.SIMPLEONE_API + 'auth/login'
            if str(error.args[0].url) == login_url:
                logger.error('Не удалось получить токен.')
        except Exception as err:
            logger.exception(err)


async def fetch_mail():
    client = MailClient()
    client.mail_connect(
        settings.MAIL_LOGIN,
        settings.MAIL_PASSWORD,
        settings.MAIL_IMAP_SERVER,
    )
    await client.fetch_simpleone_mail()
    await client.fetch_gsd_mail()
    client.close_connection()
