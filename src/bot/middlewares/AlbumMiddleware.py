import asyncio
import logging

from typing import Any, Union
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


logger = logging.getLogger('support_bot')


class AlbumMiddleware(BaseMiddleware):

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency
        self.is_last = False
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.debug('AlbumMiddleware')

        if not event.media_group_id:
            return await handler(event, data)

        try:
            logger.debug('Добавляем файлы в альбом')
            self.album_data[event.media_group_id].append(event)
            return
        except KeyError:
            self.album_data[event.media_group_id] = [event]
            await asyncio.sleep(self.latency)
            self.is_last = True
            data['album'] = self.album_data[event.media_group_id]
            return await handler(event, data)
