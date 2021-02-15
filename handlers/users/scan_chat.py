import logging
import re

from aiogram import types
from aiogram.dispatcher import filters

from loader import dp
from services.check_mail import find_ticket


@dp.message_handler(filters.Regexp(regexp=r'SC-(\d{7})+'))
async def scan_ticket(message: types.Message, regexp):
    logging.info(f'Нашел в сообщении номер тикета: {regexp.group()}')
    message_for_send = find_ticket(regexp.group())
    if message_for_send:
        message_for_send = re.sub(r'<[^>]*>', '', message_for_send)
        await message.reply(f'<code>есть информация по тикету:\n'
                            f'{message_for_send}</code>')
    else:
        logging.info('Не нашел информацию по тикету')
