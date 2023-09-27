from django.conf import settings
from django.core.management.base import BaseCommand

import asyncio
import logging

from aiogram import Bot
from aiogram import types
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.bot import handlers
from src.bot.handlers.synchronizations import register_handlers_sync
from src.bot.middlewares import SyncMiddleware
from src.utils import configure_logging

logger = logging.getLogger('support_bot')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            if not settings.TG_BOT_TOKEN:
                logger.error('Не могу запустить команду не задан TG_BOT_TOKEN')
            asyncio.run(run_bot())
        except Exception as err:
            logger.exception(err)


async def run_bot():
    available_commands = [
        types.BotCommand('/sync_rest', 'Запуск синхронизации по ресторанам'),
        types.BotCommand('/sync_tr', 'Запуск синхронизации по транзитам'),
    ]
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    await bot.set_my_commands(available_commands)
    dp = Dispatcher(bot, storage=MemoryStorage())

    logger.info('Регистрация handlers')
    handlers.register_handlers_common(dp)
    register_handlers_sync(dp)
    handlers.register_handlers_scan_chats(dp)
    dp.middleware.setup(SyncMiddleware())

    await dp.skip_updates()
    await dp.start_polling()
