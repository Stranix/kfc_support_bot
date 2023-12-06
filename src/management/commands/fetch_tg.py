import logging
import re

from dataclasses import asdict
from dataclasses import dataclass

from telethon import events
from telethon.sync import TelegramClient

from django.conf import settings
from django.core.management.base import BaseCommand

from src.utils import configure_logging

logger = logging.getLogger('dispatchers_bot')
client = TelegramClient(
    settings.TG_SESSION_NAME,
    settings.TG_API_ID,
    settings.TG_API_HASH,
    system_version="4.16.30-vxCUSTOM",
)


@dataclass
class DispatcherTaskNotify:
    dispatcher_number: int
    company: str
    restaurant: str
    itsm_number: int | None
    performer: str
    gsd_numbers: list | None
    closed_commit: str


@client.on(events.NewMessage(chats=settings.TG_GET_MESSAGE_FROM))
async def get_message_from_tg_chanel(event):
    logger.info('Обработка сообщения о закрытии заявки')
    company = [
        'ЮНИРЕСТ',
        'Рестораны быстрого питания',
        'ИНТЕРНЭШНЛ РЕСТОРАНТ БРЭНДС',
    ]
    dispatcher_task = await parce_tg_notify(event.text)
    if dispatcher_task.company in company:
        logger.info('Информация по закрытой заявке')
        logger.debug('task_info: %s', asdict(dispatcher_task))


async def parce_tg_notify(message: str) -> DispatcherTaskNotify:
    message_lines = message.replace('**', '').split('\n')
    dispatcher_task_notify = DispatcherTaskNotify(
        dispatcher_number=int(re.search(r'\d{6}', message_lines[0]).group()),
        company=message_lines[2].split(':')[1].strip(),
        restaurant=message_lines[3].split(':')[1].strip(),
        itsm_number=int(re.search(r'\d{5}', message_lines[4]).group()),
        performer=message_lines[5].split(':')[1].strip(),
        gsd_numbers=re.findall(r'(SC-\d{7})+', message_lines[9]),
        closed_commit=message_lines[11].strip(),
    )
    return dispatcher_task_notify


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            logging.getLogger('telethon').setLevel(logging.INFO)
            client.start()
            client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info('Работа бота прервана')
        except Exception as err:
            logger.exception(err)
