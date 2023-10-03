import logging

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    KeyboardButton
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger('support_bot')


async def get_choice_tr_keyboard():
    logger.debug('Создаю клавиатуру выбора транзитов для синхронизации')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='YUM!', callback_data='tr_yum'),
            InlineKeyboardButton(text='IRB', callback_data='tr_irb'),
            InlineKeyboardButton(text='FZ', callback_data='tr_fz'),
        ],
        [
            InlineKeyboardButton(text='Все', callback_data='tr_all'),
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
                callback_data=f'activate_{user_id}',
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_shift_management_keyboard():
    logger.debug('Создаю клавиатуру для управления сменой')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='Начать', callback_data='break_start'),
            InlineKeyboardButton(text='Завершить', callback_data='break_stop'),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def create_tg_keyboard_markup(
        buttons_text: list,
        buttons_per_row: int = 3,
) -> ReplyKeyboardMarkup:
    keyboard_buttons = [KeyboardButton(text=text) for text in buttons_text]

    rows = [
        keyboard_buttons[i:i + buttons_per_row] for i in
        range(0, len(keyboard_buttons), buttons_per_row)
    ]

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def get_support_task_keyboard(task_id: int):
    logger.debug('Создаю клавиатуру для инженера поддержки')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='Взять в работу',
                callback_data=f'stask_{task_id}'
            ),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_approved_task_keyboard(task_number: str):
    logger.debug('Создаю клавиатуру для подтверждения новой задачи')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='Подтвердить',
                callback_data=f'approved_new_task-{task_number}',
            ),
            InlineKeyboardButton(text='Отмена', callback_data='cancel'),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
