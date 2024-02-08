import pytz
import logging

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from django.conf import settings

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import router
from src.bot.middlewares import AuthUpdateMiddleware
from src.bot.middlewares import SchedulerMiddleware
from src.bot.middlewares import EmployeeStatusMiddleware

logger = logging.getLogger('support_bot')


def tg_webhook_init() -> tuple[Bot, Dispatcher]:
    logger.info('Загрузка настроек бота')
    job_store = {
        'default': MemoryJobStore()
    }
    if settings.REDIS_HOST == 'redis':
        job_store['default'] = RedisJobStore(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
        )
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    }
    scheduler = BackgroundScheduler(
        jobstores=job_store,
        executors=executors,
        timezone=pytz.timezone('Europe/Moscow'),
    )
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage(), skip_updates=True)
    dp.include_router(router)
    dp.update.outer_middleware(AuthUpdateMiddleware())
    dp.update.outer_middleware(SchedulerMiddleware(scheduler))
    dp.message.outer_middleware(EmployeeStatusMiddleware())
    return bot, dp
