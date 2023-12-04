import logging

from aiogram import F
from aiogram import Router
from aiogram import html
from aiogram.types import Message
from aiogram.types import ErrorEvent
from aiogram.types import CallbackQuery
from aiogram.filters import ExceptionTypeFilter
from aiogram.exceptions import TelegramAPIError
from aiogram.exceptions import TelegramForbiddenError

from django.conf import settings

from src.models import Employee

logger = logging.getLogger('support_bot')
router = Router(name='errors_handlers')


@router.error(ExceptionTypeFilter(TelegramForbiddenError))
async def telegram_api_errors_forbidden_handler(event: ErrorEvent):
    logger.debug('Кто то заблокировал бота')
    logger.error(event.exception, exc_info=True)


@router.error(ExceptionTypeFilter(Exception), F.update.message.as_('message'))
async def message_exception(
        event: ErrorEvent,
        employee: Employee,
        message: Message,
):
    logger.critical(event.exception, exc_info=True)
    await message.bot.send_message(
        settings.TG_BOT_ADMIN,
        f'Произошла ошибка в обработчике {message.text}\n\n'
        f'Пользователь: {employee.name}\n'
        f'Телега: {employee.tg_nickname}'
    )
    await message.answer(
        '😱 ОЙ! При обработке возникла ошибка.\n'
        'Я уже сообщил о проблеме'
    )


@router.error(
    ExceptionTypeFilter(Exception),
    F.update.callback_query.as_('query')
)
async def callback_exception(
        event: ErrorEvent,
        employee: Employee,
        query: CallbackQuery,
):
    logger.critical(event.exception, exc_info=True)
    await query.answer()
    await query.message.bot.send_message(
        settings.TG_BOT_ADMIN,
        f'Произошла ошибка при callback: {html.code(query.data)}\n\n'
        f'Пользователь: {employee.name}\n'
        f'Телега: {employee.tg_nickname}'
    )
    await query.message.answer(
        '😱 ОЙ! При обработке возникла ошибка.\n'
        'Я уже сообщил о проблеме'
    )


@router.error(ExceptionTypeFilter(TelegramAPIError))
async def telegram_api_errors_handler(event: ErrorEvent):
    logger.critical(event.exception, exc_info=True)
