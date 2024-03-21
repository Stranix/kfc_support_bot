import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger('middleware_support_bot')


class RightMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        logger.info(
            'EmployeeStatusMiddleware - Проверка статуса пользователя'
        )
        if message.text == '/support_help' and not data.get('field_engineer'):
            await message.answer('Команда доступна только для выездных')
            return
        return await handler(message, data)
