import re
import logging

from dataclasses import asdict
from dataclasses import dataclass

from telethon import events
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from django.conf import settings
from django.db import IntegrityError
from django.core.management.base import BaseCommand

from src.utils import configure_logging
from src.models import CustomUser
from src.models import Dispatcher
from src.entities.User import User
from src.entities.Message import Message
from src.bot.keyboards import get_choice_dispatcher_task_closed_keyboard
from src.bot.dialogs import notify_for_engineers_from_dispatcher

logger = logging.getLogger('dispatchers_bot')
client = TelegramClient(
    StringSession(settings.TG_SESSION),
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
    new_performer: CustomUser | None
    gsd_numbers: list | None
    simpleone_number: str | None
    closing_comment: str


@client.on(events.NewMessage(chats=settings.TG_GET_MESSAGE_FROM))
async def get_message_from_tg_chanel(event):
    logger.info('Обработка сообщения о закрытии заявки')
    company = [
        'ЮНИРЕСТ',
        'Рестораны быстрого питания',
        'ИНТЕРНЭШНЛ РЕСТОРАНТ БРЭНДС',
    ]
    dispatcher_task = await parce_tg_notify(event.text)
    if dispatcher_task.company not in company:
        logger.debug('Не интересная задача. Пропускаем')
        return
    if not dispatcher_task.new_performer:
        logger.debug('Не нашел исполнителя в базе. Пропускаем')
        return

    outside_number = dispatcher_task.gsd_numbers
    if dispatcher_task.simpleone_number:
        outside_number = dispatcher_task.simpleone_number

    logger.info('Подходящая задача, сохраняю в базе')
    try:
        task = await Dispatcher.objects.acreate(**asdict(dispatcher_task))
        message, keyboard = await notify_for_engineers_from_dispatcher(
            task.id,
            str(dispatcher_task.dispatcher_number),
            outside_number,
            dispatcher_task.closing_comment,
        )
        logger.info('Сохранил. Подготавливаю и отправляю уведомление')
        keyboard = await get_choice_dispatcher_task_closed_keyboard(
            task.id,
        )
        await Message.send_tg_notification(
            [User(dispatcher_task.new_performer)],
            message,
            keyboard=keyboard,
        )
    except IntegrityError as err:
        logger.warning(
            'Не смог сохранить задачу %s',
            dispatcher_task.dispatcher_number,
        )
        logger.exception(err)


async def parce_tg_notify(message: str) -> DispatcherTaskNotify:
    logger.info('Парсим сообщение закрытой заявки из телеграм')
    clear_message = message.replace('**', '')
    message_lines = clear_message.split('\n')
    dispatcher_number = re.search(r'\d{6}', message_lines[0])
    itsm_number = re.search(r'ITSM_\d{5}', message_lines[4])
    closing_comment = clear_message.split('Решение:')[1].replace('\n', '')
    performer = message_lines[5].split(':')[1].strip()
    simpleone_number = re.search(r'[A-Z]{3}[0-9]{7}', message_lines[9])
    try:
        if settings.DEBUG:
            performer = await CustomUser.objects.aget(
                dispatcher_name='Смуров К.А.',
            )
        else:
            performer = await CustomUser.objects.aget(
                dispatcher_name=performer,
            )
    except CustomUser.DoesNotExist:
        logger.warning('Не найден сотрудник из диспетчера')
        performer = None

    if dispatcher_number:
        dispatcher_number = int(dispatcher_number.group())
    if itsm_number:
        itsm_number = itsm_number.group()
    if simpleone_number:
        simpleone_number = simpleone_number.group()

    dispatcher_task_notify = DispatcherTaskNotify(
        dispatcher_number=dispatcher_number,
        company=message_lines[2].split(':')[1].strip(),
        restaurant=message_lines[3].split(':')[1].strip(),
        itsm_number=itsm_number,
        new_performer=performer,
        gsd_numbers=re.findall(r'(SC-\d{7})+', message_lines[9]),
        simpleone_number=simpleone_number,
        closing_comment=closing_comment.strip(),
    )
    logger.info('Успех. Разобрали')
    logger.debug('dispatcher_task_notify: %s', asdict(dispatcher_task_notify))
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
