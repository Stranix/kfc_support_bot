import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from src.models import CustomUser
from src.bot.utils import user_registration
from src.bot.utils import deeplink_user_registration
from src.bot.utils import get_tg_user_info_from_event

logger = logging.getLogger('middleware_support_bot')


class AuthUpdateMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.active_users = {}

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug('AuthUpdateMiddleware - Проверка пользователя')
        self.telegram_user = await get_tg_user_info_from_event(event)
        employee_in_cache = await self.get_employee_from_cache()

        if employee_in_cache:
            data['employee'] = employee_in_cache
            return await handler(event, data)

        try:
            employee_in_db = await self.get_employee_from_db()
        except CustomUser.DoesNotExist:
            message_text = event.message.text.split()
            if len(message_text) == 2:
                employee_in_db = await deeplink_user_registration(
                    event.message,
                    message_text[1],
                )
            else:
                employee_in_db = await user_registration(event.message)

        if employee_in_db and employee_in_db.is_active:
            logger.debug('Пользователь в базе и активен. Фиксируем в кеше')
            self.active_users[employee_in_db.tg_id] = employee_in_db

        data['employee'] = employee_in_db
        return await handler(event, data)

    async def get_employee_from_db(self) -> CustomUser | None:
        logger.debug('Попытка получить пользователя из БД')
        employee = await CustomUser.objects.prefetch_related(
            'groups',
            'new_work_shifts',
        ).aget(tg_id=self.telegram_user.id)
        verified_employee = await self.check_employee_nickname_for_changes(
            employee,
        )
        logger.debug('Информация о пользователе получена')
        return verified_employee

    async def get_employee_from_cache(self) -> CustomUser | None:
        logger.debug('Попытка получить пользователя из кеша')
        employee = self.active_users.get(self.telegram_user.id)

        if not employee:
            logger.debug('Пользователь не найден в кеше')
            return

        logger.debug('Нашел пользователя в кеше')
        verified_employee = await self.check_employee_nickname_for_changes(
            employee,
        )
        return verified_employee

    async def check_employee_nickname_for_changes(
            self,
            employee: CustomUser,
    ) -> CustomUser:
        logger.debug('Проверка пользователя на изменение ника')
        employee_db_nickname = employee.tg_nickname
        employee_new_nickname = self.telegram_user.nickname

        if employee_new_nickname == employee_db_nickname:
            return employee

        logger.warning(
            'Внимание! Пользователь %s изменил свой ник %s -> %s',
            employee.name,
            employee_db_nickname,
            employee_new_nickname,
        )
        logger.debug('Фиксирую изменения в БД и кеше')
        employee.tg_nickname = employee_new_nickname
        await employee.asave()
        self.active_users[employee.tg_id] = employee
        logger.debug('Готово')
        return employee
