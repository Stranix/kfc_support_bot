from aiogram import types
from aiogram.dispatcher.filters import CommandHelp

from loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = [
        'Список команд: ',
        '/start - Старт бота',
        '/help - Получить справку',
        '/sync_tr - Синхронизация транзитов',
        '/sync_rest - Синхронизация ресторана(ов)',
        '/rest_info - Информация по ресторану',
        '/cash_info - Информация по кассе',
        '/sync_check - Проверка синхронизации в ресторане(ах)',
    ]
    await message.answer('\n'.join(text))
