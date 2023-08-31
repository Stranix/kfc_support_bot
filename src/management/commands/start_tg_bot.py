from django.conf import settings
from django.core.management.base import BaseCommand

import asyncio
import logging

from aiogram import Bot
from aiogram import types
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.bot import handlers

logger = logging.getLogger('support_bot')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not settings.TG_BOT_TOKEN:
            print('Не могу запустить команду не задан TG_BOT_TOKEN')
        asyncio.run(run_bot())


async def run_bot():
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=MemoryStorage())

    logger.info('Регистрация handlers')
    handlers.register_handlers_common(dp)
    handlers.register_handlers_sync(dp)
    handlers.register_handlers_scan_chats(dp)

    await dp.skip_updates()
    await dp.start_polling()
