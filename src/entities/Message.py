import logging

from django.conf import settings

from aiogram import types, Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from src.bot import keyboards
from src.entities.Dialog import Dialog
from src.entities.FieldEngineer import FieldEngineer
from src.entities.Service import Service
from src.entities.User import User
from src.models import SDTask

logger = logging.getLogger('support_bot')


class Message:

    @staticmethod
    async def send_tg_notification(
            recipients: list[User],
            message: str,
            *,
            keyboard: types.InlineKeyboardMarkup = None,
    ):
        """Отправка уведомления пользователям в телеграм"""
        logger.info('Отправка уведомления')
        if not recipients:
            logger.warning('Пустой список для отправки уведомлений')
            return
        bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=ParseMode.HTML)
        for recipient in recipients:
            try:
                logger.debug('Уведомление для: %s', recipient.user.name)
                await bot.send_message(
                    recipient.user.tg_id,
                    message,
                    reply_markup=keyboard,
                )
            except TelegramBadRequest:
                logger.warning(
                    'Не смог отправить уведомление %s',
                    recipient.user.name,
                )
            except TelegramForbiddenError:
                logger.warning('Заблокировал бота %s', recipient.user.name)
        await bot.session.close()
        logger.info('Отправка уведомлений завершена')

    @staticmethod
    async def send_notify_to_seniors_engineers(message: str, keyboard=None):
        logger.info('Отправка уведомлений Ведущим Инженерам')
        senior_engineers = await Service.get_senior_engineers()
        await Message.send_tg_notification(
            senior_engineers,
            message,
            keyboard=keyboard,
        )

    @staticmethod
    async def send_new_task_notify(
            task: SDTask,
            field_engineer: FieldEngineer,
    ):
        logger.info('Отправка уведомлений о новой задаче')
        recipients = await Service.get_engineers_on_shift_by_support_group(
            task.support_group,
        )

        if not recipients:
            logger.warning('На смене нет инженеров или диспетчеров')
            notify = Dialog.new_task_no_engineers_on_shift(task.number)
            await Message.send_notify_to_seniors_engineers(notify)
            return

        message = Dialog.new_task_notify_for_engineers(task, field_engineer)
        keyboard = await keyboards.get_support_task_keyboard(task.id)
        await Message.send_tg_notification(
            recipients,
            message,
            keyboard=keyboard,
        )
