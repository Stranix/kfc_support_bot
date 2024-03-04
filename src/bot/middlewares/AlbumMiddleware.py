import asyncio
import logging

from typing import Any, Union
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


logger = logging.getLogger('middleware_support_bot')


class AlbumMiddleware(BaseMiddleware):

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency
        self.is_last = False

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.debug('AlbumMiddleware')

        if not message.media_group_id:
            data['album'] = {}
            return await handler(message, data)

        try:
            logger.debug('Добавляем файлы в альбом')
            self.album_data[message.media_group_id].append(message)
            return
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)
            self.is_last = True
            data['album'] = self.album_data[message.media_group_id]
            await handler(message, data)
            if self.is_last:
                del self.album_data[message.media_group_id]
