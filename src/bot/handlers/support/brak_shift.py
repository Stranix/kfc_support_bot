import logging

from aiogram import types

logger = logging.getLogger('support_bot')


async def break_shift(message: types.Message):
    # TODO отправить клавиатуру ушел/пришел с перерыва.
    # TODO Ушел: в списке на получение задач выставить статус перерыв.
    # TODO Пришел: в списке на получение задач выставить статус работаю.
    # TODO Фиксировать время перерыва.
    # TODO Отправка уведомления менеджеру о статусе перерыва.
    pass
