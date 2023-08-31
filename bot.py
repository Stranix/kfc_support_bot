import asyncio
import logging

from aiogram import Bot
from aiogram import types
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import settings
from src.handlers.common import register_handlers_common
from src.handlers.sync import register_handlers_sync
from src.handlers.scan_chats import register_handlers_scan_chats

logger = logging.getLogger('support_bot')


async def main():
    bot = Bot(token=settings.tg_bot_token, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=MemoryStorage())

    logger.info('Регистрация handlers')
    register_handlers_common(dp)
    register_handlers_sync(dp)
    register_handlers_scan_chats(dp)

    await dp.skip_updates()
    await dp.start_polling()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    asyncio.run(main())
