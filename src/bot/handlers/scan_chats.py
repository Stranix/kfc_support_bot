import re
import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Regexp

logger = logging.getLogger('support_bot')


def register_handlers_scan_chats(dp: Dispatcher):
    logger.info('Регистрация команд поиска текста в чатах')
    dp.register_message_handler(scan_ticket, Regexp(regexp=r'SC-(\d{7})+'))


async def scan_ticket(message: types.Message, regexp: re.Match):
    logger.info(f'Нашел в сообщении номер тикета: {regexp.group()}')
    message_for_send = regexp.group()
    if not message_for_send:
        logger.info('Не нашел информацию по тикету')

    await message.reply(md.hcode(message_for_send))
