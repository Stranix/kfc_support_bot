import re
import logging

from aiogram import F
from aiogram import Router
from aiogram import types


from src.bot import dialogs
from src.entities.SupportEngineer import SupportEngineer
from src.models import SDTask, SimpleOneTask, Restaurant
from src.models import GSDTask

logger = logging.getLogger('support_bot')
router = Router(name='scan_chats_handlers')


@router.message(F.text.regexp(r'SC-(\d{7})+').as_('regexp'))
async def scan_ticket(message: types.Message, regexp: re.Match[str]):
    logger.info(f'Нашел в сообщении номер тикета: {regexp.group()}')
    task_number = regexp.group()
    try:
        task = await GSDTask.objects.aget(number=task_number)
        text, keyboard = await dialogs.scan_chat_gsd_task_info(task)
        await message.reply(text, reply_markup=keyboard)
    except GSDTask.DoesNotExist:
        logger.info('Нет информации по задаче в базе')


@router.callback_query(F.data.startswith('gsd_task_'))
async def send_gsd_task_info(query: types.CallbackQuery):
    logger.info('Отправка полной информации по задаче GSD')
    task_id = query.data.split('_')[-1]
    logger.debug('task_id: %s', task_id)
    try:
        task = await GSDTask.objects.aget(id=task_id)
        task.description = re.sub(r'<[^>]*>', '', task.description)
        task.description = task.description.replace('\n', '<br>')
        message, _ = await dialogs.scan_chat_gsd_task_info(task, short=False)
        await query.message.edit_text(message)
    except GSDTask.DoesNotExist:
        logger.warning('Не удалось получить задачу')


@router.message(F.text.regexp(r'SD-(\d{5,7})+').as_('regexp'))
async def local_task_short(
        message: types.Message,
        support_engineer: SupportEngineer,
        regexp: re.Match[str],
):
    logger.info(f'Нашел в сообщении номер локального тикета: {regexp.group()}')
    task_number = regexp.group()
    try:
        task = await SDTask.objects.by_number(task_number)
        text, keyboard = await dialogs.scan_chat_sd_task_info(
            task,
            support_engineer,
        )
        await message.reply(text, reply_markup=keyboard)
    except SDTask.DoesNotExist:
        logger.warning('Нет такой задачи (%s) в БД', task_number)
        await message.answer(await dialogs.error_task_not_found())


@router.callback_query(F.data.startswith('sd_task_'))
async def local_task_full(
    query: types.CallbackQuery,
    support_engineer: SupportEngineer,
):
    logger.info('Полная информации по задачи для %s', support_engineer.user)
    task_id = query.data.split('_')[-1]
    task = await SDTask.objects.by_id(task_id)
    message, keyboard = await dialogs.scan_chat_sd_task_info(
        task,
        support_engineer,
        short=False,
    )
    await query.message.edit_text(message, reply_markup=keyboard)


@router.message(F.text.regexp(r'([A-Z]{3}[0-9]{7})+').as_('regexp'))
async def simpleone_short(message: types.Message, regexp: re.Match[str]):
    logger.info(f'Нашел в сообщении номер тикета: {regexp.group()}')
    task_number = regexp.group()
    try:
        task = await SimpleOneTask.objects.aget(number=task_number)
        task.subject = task.subject.replace('\n', '<br>')
        text, keyboard = await dialogs.scan_chat_simpleone_task_info(task)
        await message.reply(text, reply_markup=keyboard)
    except SimpleOneTask.DoesNotExist:
        logger.info('Нет информации по задаче в базе')


@router.callback_query(F.data.startswith('simpleone_task_'))
async def simpleone_full(query: types.CallbackQuery):
    logger.info('Отправка полной информации по задаче SimpleOne')
    task_id = query.data.split('_')[-1]
    logger.debug('task_id: %s', task_id)
    try:
        task = await SimpleOneTask.objects.aget(id=task_id)
        task.subject = task.subject.replace('\n', '<br>')
        message, _ = await dialogs.scan_chat_simpleone_task_info(
            task,
            short=False,
        )
        await query.message.edit_text(message)
    except SimpleOneTask.DoesNotExist:
        logger.warning('Не удалось получить задачу')


@router.message(F.text.regexp(r'\d{2,4}').as_('regexp'))
async def restaurant_info(message: types.Message, regexp: re.Match[str]):
    logger.info(f'Нашел в сообщении номер ресторана: {regexp.group()}')
    restaurant_code = regexp.group()
    try:
        restaurant = await Restaurant.objects.aget(code=restaurant_code)
        await message.reply(await dialogs.restaurant_info(restaurant))
    except Restaurant.DoesNotExist:
        logger.info('Нет информации по htc')
        await message.reply(await dialogs.error_restaurant_not_found())
