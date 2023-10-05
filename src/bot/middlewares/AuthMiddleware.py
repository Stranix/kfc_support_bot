import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from src.models import Employee

logger = logging.getLogger('support_bot')


class AuthUpdateMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.active_users = {}

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        logger.info('AuthUpdateMiddleware - Проверка пользователя')
        user_id = 0
        if event.callback_query:
            logger.debug('AuthUpdateMiddleware callback_query')
            user_id = event.callback_query.from_user.id
        if event.message:
            logger.debug('AuthUpdateMiddleware message')
            user_id = event.message.from_user.id
        logger.debug('user_id: %s', user_id)
        if not self.active_users.get(user_id):
            logger.info('Пытаемся получить пользователя из БД')
            try:
                employee = await Employee.objects.prefetch_related(
                    'groups', 'managers'
                ).aget(tg_id=user_id)
                logger.info('Информация по пользователю получена. Фиксируем')
                self.active_users[user_id] = employee
            except Employee.DoesNotExist:
                logger.warning('Пользователь без регистрации')
        data['employee'] = self.active_users.get(user_id)
        logger.info('Проверка завершена')
        return await handler(event, data)
