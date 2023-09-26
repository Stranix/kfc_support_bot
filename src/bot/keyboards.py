import logging

from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger('support_bot')


async def get_choice_tr_keyboard():
    logger.debug('Создаю клавиатуру выбора транзитов для синхронизации')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='YUM!', callback_data='yum'),
            InlineKeyboardButton(text='IRB', callback_data='irb'),
            InlineKeyboardButton(text='FZ', callback_data='fz'),
        ],
        [
            InlineKeyboardButton(text='Все', callback_data='all'),
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_rest_sync_keyboard():
    logger.debug('Создаю клавиатуру выбора синхронизации ресторанов')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='По Списку', callback_data='rest_list'),
            InlineKeyboardButton(text='Группу', callback_data='rest_group'),
            InlineKeyboardButton(text='Все', callback_data='rest_all'),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_rest_owner_keyboard():
    logger.debug('Создаю клавиатуру для выбора группы ресторанов для синхры')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='YUM!', callback_data='rest_yum'),
            InlineKeyboardButton(text='IRB', callback_data='rest_irb'),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_report_keyboard(report_id: int):
    logger.debug('Создаю кнопку для показа отчета по синхронизации')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='📋 Показать отчет',
                callback_data=f'report_{report_id}',
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_task_keyboard(task_id: int):
    logger.debug('Создаю кнопку для показа задач')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='📄 Показать всё письмо',
                callback_data=f'task_{task_id}',
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_user_activate_keyboard(user_id: int):
    logger.debug('Создаю кнопку для активации  нового пользователя')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='👤 Активировать?',
                callback_data=f'user_{user_id}',
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
