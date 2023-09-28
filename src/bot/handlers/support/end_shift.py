import logging

from aiogram import types

logger = logging.getLogger('support_bot')


async def end_shift(message: types.Message):
    # TODO удалить из списка на получение задач.
    # TODO Фиксировать время ухода со смены.
    # TODO Отправка уведомления менеджеру что инженер ушел со смены.
    pass
