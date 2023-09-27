import re
import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher.filters import Regexp

from django.utils.dateformat import format

from src.models import Task
from src.bot.keyboards import get_task_keyboard

logger = logging.getLogger('support_bot')


def register_handlers_scan_chats(dp: Dispatcher):
    logger.info('Регистрация команд поиска текста в чатах')
    dp.register_message_handler(scan_ticket, Regexp(regexp=r'SC-(\d{7})+'))
    dp.register_callback_query_handler(
        send_task,
        lambda call: re.match('task_', call.data),
        state='*',
    )


async def scan_ticket(message: types.Message, regexp: re.Match):
    logger.info(f'Нашел в сообщении номер тикета: {regexp.group()}')
    task_number = regexp.group()
    try:
        task = await Task.objects.aget(number=task_number)
        time_formatted_mask = 'd-m-Y H:i:s'
        start_at = format(task.start_at, time_formatted_mask)
        expired_at = format(task.expired_at, time_formatted_mask)
        message_fo_send = md.text(
            md.hcode(task.number),
            '\n\nУслуга: ' + md.hcode(task.service),
            '\nТип обращения: ' + md.hcode(task.title),
            '\nЗаявитель: ' + md.hcode(task.applicant),
            '\nНа группе: ' + md.hcode(task.gsd_group),
            '\nДата регистрации: ' + md.hcode(start_at),
            '\nСрок обработки: ' + md.hcode(expired_at),
        )
        keyboard = await get_task_keyboard(task.id)
        await message.reply(message_fo_send, reply_markup=keyboard)
    except Task.DoesNotExist:
        logger.warning('Нет такой задачи (%s) в БД', task_number)


async def send_task(query: types.CallbackQuery):
    logger.info('Отправка полной информации по задаче')
    task_id = query.data.split('_')[1]
    logger.debug('task_id: %s', task_id)
    try:
        task = await Task.objects.aget(id=task_id)
        await query.answer()
        task_description = re.sub(r'<[^>]*>', '', task.description)
        await query.message.answer(md.hcode(task_description))
        await query.message.delete()
    except Task.DoesNotExist:
        logger.warning('Не удалось получить задачу')
