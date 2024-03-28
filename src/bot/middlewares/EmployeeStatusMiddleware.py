import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.models import CustomUser

logger = logging.getLogger('middleware_support_bot')


class EmployeeStatusMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        logger.info(
            'EmployeeStatusMiddleware - Проверка статуса пользователя'
        )
        if event.text == '/start':
            return await handler(event, data)
        employee: CustomUser = data['employee']
        logger.info('Пользователь: %s', employee.name)
        if not employee.is_active:
            await event.reply(
                'Ваша запись не активирована.\n'
                'Дождитесь сообщения о активации чтобы пользоваться ботом'
            )
            return
        return await handler(event, data)
