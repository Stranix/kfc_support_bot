import logging

from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger('support_bot')


def get_choice_tr_keyboard():
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


def get_choice_rest_sync_keyboard():
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


def get_choice_rest_owner_keyboard():
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
