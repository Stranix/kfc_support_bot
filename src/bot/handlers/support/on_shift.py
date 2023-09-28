import logging

from aiogram import types

logger = logging.getLogger('support_bot')


async def on_shift(message: types.Message):
    # TODO добавить пользователя в список на получение задач.
    # TODO Зафиксировать дату и время прихода на смену.
    # TODO Отправка уведомления менеджеру что инженер на смене.
    pass


