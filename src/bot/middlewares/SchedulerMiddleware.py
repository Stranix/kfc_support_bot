import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from src.entities.Service import Service

logger = logging.getLogger('middleware_support_bot')


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, service: Service) -> None:
        logger.debug('SchedulerMiddleware init')
        self._service = service

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug('SchedulerMiddleware - Получение шедулера')
        data['service'] = self._service
        return await handler(event, data)
