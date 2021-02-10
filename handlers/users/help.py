from aiogram import types
from aiogram.dispatcher.filters import CommandHelp

from loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = [
        'Список команд: ',
        '/help - Получить справку',
        '/sync_tr - Синхронизация транзитов',
        '/sync_rest - Синхронизация ресторана(ов)',
        '/sync_all - Синхронизация всех ресторанов с выбором Юр лица',
    ]
    await message.answer('\n'.join(text))
