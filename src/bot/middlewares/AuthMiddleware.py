import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from src.models import Employee
from src.bot.utils import user_registration

logger = logging.getLogger('support_bot')


class AuthUpdateMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.active_users = {}
        self.user_tg_id = 0

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug('AuthUpdateMiddleware - Проверка пользователя')
        if event.callback_query:
            logger.debug('AuthUpdateMiddleware callback_query')
            self.user_tg_id = event.callback_query.from_user.id
        if event.message:
            logger.debug('AuthUpdateMiddleware message')
            self.user_tg_id = event.message.from_user.id
        logger.debug('Попытка получить пользователя из кеша')
        employee_in_cache = self.active_users.get(self.user_tg_id)
        if employee_in_cache:
            logger.debug('Пользователь найден в кеше')
            data['employee'] = employee_in_cache
            return await handler(event, data)
        logger.debug('Пользователь не существует в кеше. Пробуем найти в ДБ')
        employee_in_db = await self.get_employee_from_db()
        if not employee_in_db:
            logger.warning('Новый пользователь. Регистрирую')
            employee_in_db = await user_registration(event.message)
        if employee_in_db and employee_in_db.is_active:
            logger.debug('Пользователь в базе и активен. Фиксируем в кеше')
            self.active_users[self.user_tg_id] = employee_in_db
        data['employee'] = employee_in_db
        return await handler(event, data)

    async def get_employee_from_db(self) -> Employee | None:
        try:
            return await Employee.objects.prefetch_related(
                'groups',
                'managers',
                'work_shifts',
            ).aget(tg_id=self.user_tg_id)
        except Employee.DoesNotExist:
            logger.info('Нет записи о пользователе в БД')
