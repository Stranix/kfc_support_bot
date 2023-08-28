import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import settings
from src.handlers.common import register_handlers_common

logger = logging.getLogger('support_bot')


async def main():
    bot = Bot(token=settings.tg_bot.token)
    dp = Dispatcher(bot, storage=MemoryStorage())

    logger.info('Регистрация хендлеров')
    register_handlers_common(dp)

    await dp.skip_updates()
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
