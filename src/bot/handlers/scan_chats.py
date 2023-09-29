import re
import logging

import aiogram.utils.markdown as md

from aiogram import F
from aiogram import Router
from aiogram import types

from django.utils.dateformat import format

from src.models import Task
from src.bot.keyboards import get_task_keyboard
from src.management.commands.upload_task import fetch_mail

logger = logging.getLogger('support_bot')
router = Router(name='scan_chats_handlers')


@router.message(F.text.regexp(r'SC-(\d{7})+').as_('regexp'))
async def scan_ticket(message: types.Message, regexp: re.Match[str]):
    logger.info(f'Нашел в сообщении номер тикета: {regexp.group()}')
    task_number = regexp.group()
    message_fo_send, keyboard = await get_task_by_number(task_number)
    if not message_fo_send:
        logger.info('Пробую еще раз загрузить почту и проверить сообщение')
        await fetch_mail()
        message_fo_send, keyboard = await get_task_by_number(task_number)

    if message_fo_send:
        await message.reply(message_fo_send, reply_markup=keyboard)


@router.callback_query(F.data.startswith('task_'))
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


async def get_task_by_number(task_number: str) -> tuple:
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
        return message_fo_send, keyboard
    except Task.DoesNotExist:
        logger.warning('Нет такой задачи (%s) в БД', task_number)
        return None, None
