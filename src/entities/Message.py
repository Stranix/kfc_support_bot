import logging

from asgiref.sync import sync_to_async

from django.conf import settings

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup

from src.bot import services
from src.bot import keyboards, dialogs
from src.entities.FieldEngineer import FieldEngineer
from src.entities.SupportEngineer import SupportEngineer
from src.entities.User import User
from src.models import SDTask, CustomGroup

logger = logging.getLogger('support_bot')


class Message:

    @staticmethod
    async def send_to_chat(
            chat_id: int,
            message: str,
            media_group: list,
    ):
        """Отправка уведомлений в группу или канал телеграм"""
        logger.info('Отправка сообщения в группы %s', chat_id)
        bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=ParseMode.HTML)
        try:
            logger.debug('Уведомление для: %s', chat_id)
            await bot.send_message(chat_id, message)
            await bot.send_media_group(chat_id, media_group)
        except TelegramBadRequest:
            logger.warning('Не смог отправить уведомление')
        except TelegramForbiddenError:
            logger.warning('Заблокировал бота')
        finally:
            await bot.session.close()
            logger.info('Отправка уведомлений завершена')

    @staticmethod
    async def send_tg_notification(
            recipients: list[User],
            message: str,
            *,
            keyboard: InlineKeyboardMarkup | ReplyKeyboardRemove = None,
    ):
        """Отправка уведомления в телеграм"""
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
        senior_engineers = await services.get_senior_engineers()
        await Message.send_tg_notification(
            senior_engineers,
            message,
            keyboard=keyboard,
        )

    @staticmethod
    async def send_notify_to_group_managers(
            group_id: int,
            message: str,
            keyboard=None,
    ):
        logger.info('Менеджерам группы')
        group_managers = await services.get_group_managers_by_group_id(
            group_id,
        )
        await Message.send_tg_notification(
            group_managers,
            message,
            keyboard=keyboard,
        )

    @staticmethod
    async def send_new_task_notify(task: SDTask):
        logger.info('Отправка уведомлений о новой задаче')
        recipients = await services.get_engineers_on_shift_by_support_group(
            task.support_group,
        )

        if not recipients:
            logger.warning('На смене нет инженеров или диспетчеров')
            group_id = 0
            if task.support_group == 'DISPATCHER':
                group = await CustomGroup.objects.aget(name='Диспетчеры')
                group_id = group.id
            if task.support_group == 'ENGINEER':
                group_id = await CustomGroup.objects.aget(
                    name='Старшие инженеры',
                ).id
            notify = await dialogs.error_no_engineers_on_shift(task.number)
            await Message.send_notify_to_group_managers(group_id, notify)
            await Message.send_notify_to_seniors_engineers(notify)
            return

        message = await dialogs.new_task_notify_for_engineers(
            task.number,
            task.description,
            task.new_applicant.tg_nickname,
            task.support_group,
        )
        keyboard = await keyboards.get_support_task_keyboard(task.id)
        await Message.send_tg_notification(
            recipients,
            message,
            keyboard=keyboard,
        )

    @staticmethod
    async def send_notify_on_additional_work(
            creator: FieldEngineer,
            performer: SupportEngineer,
            task_id: str,
            task_number: str,
            task_title: str,
            documents: dict,
    ):
        additional_chat_id = settings.TG_ADDITIONAL_CHAT_ID
        media_group = await services.create_documents_media_group(documents)
        text_performer = await dialogs.additional_chat_for_performer()
        text_additional_chat = await dialogs.additional_chat_message(
            task_number,
        )
        text_creator, keyboard = await dialogs.additional_chat_for_creator(
            task_id,
            task_number,
            task_title,
        )
        await Message.send_to_chat(
            additional_chat_id,
            text_additional_chat,
            media_group,
        )
        await Message.send_tg_notification(
            [creator],
            text_creator,
            keyboard=keyboard,
        )
        await Message.send_tg_notification(
            [performer],
            text_performer,
            keyboard=ReplyKeyboardRemove(),
        )

    @staticmethod
    async def send_new_tasks_notify_for_middle(engineer: SupportEngineer):
        new_tasks = await sync_to_async(list)(
            SDTask.objects.filter(status='NEW')
        )
        if not new_tasks:
            logger.debug('Нет новых задач')
            return
        tasks_numbers = [task.number for task in new_tasks]
        message = await dialogs.new_task_notify_for_middle(tasks_numbers)
        await Message.send_tg_notification([engineer], message)

    @staticmethod
    async def send_start_task_notify(sd_task: SDTask):
        text_for_performer = await dialogs.sd_task_start_for_performer(sd_task)
        text_for_creator = await dialogs.sd_task_start_for_creator(sd_task)
        await Message.send_tg_notification(
            [User(sd_task.new_performer)],
            text_for_performer,
            keyboard=ReplyKeyboardRemove(),
        )
        if sd_task.is_automatic:
            await services.send_documents_out_task(sd_task)
        await Message.send_tg_notification(
            [User(sd_task.new_applicant)],
            text_for_creator,
        )

    @staticmethod
    async def send_assigned_task_notify(
            sd_task: SDTask,
            appointer: SupportEngineer,
    ):
        logger.info('Отправка уведомлений о назначении задачи')
        text_for_appointer = await dialogs.sd_task_assign_for_appointer(
            sd_task.number,
            sd_task.new_performer.name,
        )
        text_for_performer = await dialogs.sd_task_assign_for_performer(
            appointer.user.name,
            sd_task,
        )
        text_for_creator = await dialogs.sd_task_assign_for_creator(sd_task)
        await Message.send_tg_notification(
            [appointer],
            text_for_appointer,
            keyboard=ReplyKeyboardRemove(),
        )
        await Message.send_tg_notification(
            [User(sd_task.new_performer)],
            text_for_performer,
        )
        await Message.send_tg_notification(
            [User(sd_task.new_applicant)],
            text_for_creator,
        )
        logger.info('Уведомления отправлены')

    @staticmethod
    async def send_close_task_notify(task: SDTask):
        logger.info('Отправка уведомлений о закрытии задачи')
        text_for_creator, keyboard = await dialogs.sd_task_close_for_creator(
            task.id,
            task.number,
            task.title,
        )
        text_for_performer = await dialogs.sd_task_close_for_performer(
            task.number,
        )
        await Message.send_tg_notification(
            [User(task.new_applicant)],
            text_for_creator,
            keyboard=keyboard,
        )
        await Message.send_tg_notification(
            [User(task.new_performer)],
            text_for_performer,
            keyboard=ReplyKeyboardRemove(),
        )
        logger.info('Уведомления отправлены')
