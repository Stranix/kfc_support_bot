import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger('middleware_support_bot')


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler: AsyncIOScheduler) -> None:
        logger.debug('SchedulerMiddleware init')
        self._scheduler = scheduler

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug('SchedulerMiddleware - Получение шедулера')
        data['scheduler'] = self._scheduler
        return await handler(event, data)
