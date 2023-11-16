import re
import logging
from typing import Any

from aiogram import F
from aiogram import Router
from aiogram import html
from aiogram import types

from django.utils.dateformat import format

from src.models import Task, Employee
from src.bot.keyboards import get_task_keyboard, assign_task_keyboard
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
        await query.message.answer(html.code(task_description))
        await query.message.delete()
    except Task.DoesNotExist:
        logger.warning('Не удалось получить задачу')


@router.message(F.text.regexp(r'SD-(\d{6,7})+').as_('regexp'))
async def local_service(
        message: types.Message,
        employee: Employee,
        regexp: re.Match[str],
):
    logger.info(f'Нашел в сообщении номер локального тикета: {regexp.group()}')
    task_number = regexp.group()
    task, message_fo_send = await get_local_task_by_number(task_number)
    if not message_fo_send:
        await message.answer('А нету такого обращения в базе')
        return
    keyboard = None
    if await employee.groups.filter(
            name__in=('Старшие инженеры', 'Ведущие инженеры', 'Администраторы')
    ).afirst() and not task.performer:
        keyboard = await assign_task_keyboard(task.id)
    if task.performer and not task.finish_at:
        message_fo_send += f'\n\nЗадача в работе у сотрудника: ' \
                           f'{html.code(task.performer)}'
    if task.finish_at:
        message_fo_send += f'\n\nЗадача закрыта сотрудником: ' \
                           f'{html.code(task.performer)}'
    await message.reply(message_fo_send, reply_markup=keyboard)


async def get_task_by_number(task_number: str) -> tuple:
    try:
        task = await Task.objects.aget(number=task_number)
        time_formatted_mask = 'd-m-Y H:i:s'
        start_at = format(task.start_at, time_formatted_mask)
        expired_at = format(task.expired_at, time_formatted_mask)
        message_fo_send = html.code(task.number) + \
            '\n\nУслуга: ' + html.code(task.service) + \
            '\nТип обращения: ' + html.code(task.title) + \
            '\nЗаявитель: ' + html.code(task.applicant) + \
            '\nНа группе: ' + html.code(task.gsd_group) + \
            '\nДата регистрации: ' + html.code(start_at) + \
            '\nСрок обработки: ' + html.code(expired_at)
        keyboard = await get_task_keyboard(task.id)
        return message_fo_send, keyboard
    except Task.DoesNotExist:
        logger.warning('Нет такой задачи (%s) в БД', task_number)
        return None, None


async def get_local_task_by_number(
        task_number: str
) -> tuple[Any, Any] | tuple[None, None]:
    try:
        task = await Task.objects.select_related('performer')\
                                 .aget(number=task_number)
        support_group = 'Инженеры'
        if task.support_group == 'DISPATCHER':
            support_group = 'Диспетчеры'

        time_formatted_mask = 'd-m-Y H:i:s'
        start_at = format(task.start_at, time_formatted_mask)
        message_fo_send = html.code(task.number) + \
            '\n\nУслуга: ' + html.code(task.service) + \
            '\nГруппа: ' + html.code(support_group) + \
            '\nЗаявитель: ' + html.code(task.applicant) + \
            '\nТип обращения: ' + html.code(task.title) + \
            '\nДата регистрации: ' + html.code(start_at) + \
            '\nТекста обращения: ' + html.code(task.description) + \
            '\nДочерние обращения: ' + html.code(task.sub_task_number) + \
            '\nКомментарий закрытия: ' + html.code(task.comments)
        return task, message_fo_send
    except Task.DoesNotExist:
        logger.warning('Нет такой задачи (%s) в БД', task_number)
        return None, None
