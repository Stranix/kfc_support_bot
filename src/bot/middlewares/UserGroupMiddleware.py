import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from src.entities.SberEngineer import SberEngineer
from src.entities.FieldEngineer import FieldEngineer
from src.entities.SupportEngineer import SupportEngineer
from src.models import CustomUser

logger = logging.getLogger('middleware_support_bot')


class UserGroupMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        logger.info(
            'UserGroupMiddleware - Проверка группы пользователя'
        )
        employee: CustomUser = data['employee']
        data['field_engineer'] = None
        data['support_engineer'] = None
        if await employee.groups.filter(name__contains='Подрядчик').aexists():
            data['field_engineer'] = FieldEngineer(employee)
        if await employee.groups.filter(
            name__in=(
                'Инженеры',
                'Старшие инженеры',
                'Ведущие инженеры',
                'Диспетчеры',
            )
        ).aexists():
            data['support_engineer'] = SupportEngineer(employee)
        if await employee.groups.filter(name__contains='SBER').aexists():
            data['sber_engineer'] = SberEngineer(employee)
        logger.debug('data: %s', data)
        return await handler(event, data)
