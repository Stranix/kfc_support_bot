import asyncio
import logging

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from django.conf import settings
from django.core.management.base import BaseCommand

from aiogram import Bot
from aiogram import types
from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.utils import configure_logging
from src.bot.handlers import router
from src.bot.middlewares import AuthUpdateMiddleware
from src.bot.middlewares import SchedulerMiddleware
from src.bot.middlewares import EmployeeStatusMiddleware
from src.bot.middlewares import UserGroupMiddleware

logger = logging.getLogger('support_bot')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            if not settings.TG_BOT_TOKEN:
                logger.error('Не могу запустить команду не задан TG_BOT_TOKEN')
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            logger.info('Работа бота прервана')
        except Exception as err:
            logger.exception(err)


async def start_bot(bot: Bot):
    await set_commands(bot)
    await bot.send_message(settings.TG_BOT_ADMIN, text='Бот запущен!')


async def set_commands(bot: Bot):
    available_commands = [
        types.BotCommand(
            command='help',
            description='Посмотреть список доступных команд',
        ),
        types.BotCommand(
            command='feedback',
            description='🪬Отправить обратную связь по боту',
        ),
        types.BotCommand(
            command='cancel',
            description='Прервать диалог на любом этапе',
        ),
    ]
    await bot.set_my_commands(
        available_commands,
        types.BotCommandScopeDefault()
    )


async def run_bot():
    job_store = {
        'default': MemoryJobStore()
    }
    if settings.REDIS_HOST == 'redis':
        job_store['default'] = RedisJobStore(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
        )
    scheduler = AsyncIOScheduler(jobstores=job_store)
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage(), skip_updates=True)
    dp.include_router(router)
    dp.startup.register(start_bot)
    dp.update.outer_middleware(AuthUpdateMiddleware())
    dp.update.outer_middleware(UserGroupMiddleware())
    dp.update.outer_middleware(SchedulerMiddleware(scheduler))
    dp.message.outer_middleware(EmployeeStatusMiddleware())
    scheduler.start()
    await dp.start_polling(bot)
