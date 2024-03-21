import logging

from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
)

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


async def get_gsd_task_keyboard(task_id: int):
    logger.debug('Создаю Кнопку запроса доп информации по задаче GSD')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='📄 Показать всё письмо',
                callback_data=f'gsd_task_{task_id}',
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


async def assign_task_keyboard(task_id: int):
    logger.debug('Создаю клавиатуру назначения задачи на инженера')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='Назначить на инженера',
                callback_data=f'atask_{task_id}'
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


async def get_task_feedback_keyboard(task_id: int):
    logger.debug('Создаю клавиатуру для оценки задачи')
    buttons = []
    for button_number in range(1, 6):
        buttons.append(
            InlineKeyboardButton(
                text=str(button_number),
                callback_data=f'rating_{button_number}_{task_id}'
            )
        )
    inline_keyboard = [buttons]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_support_group_keyboard():
    logger.debug('Создаю клавиатуру выбора группы поддержки')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='🦹‍♂Диспетчера. Команда HelpD',
                callback_data='dispatcher',
            ),
        ],
        [
            InlineKeyboardButton(text='🥷Инженера', callback_data='engineer'),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_task_doc_approved_keyboard():
    logger.debug('Создаю клавиатуру для подтверждения набора документов')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='Да', callback_data='doc_apr_yes'),
            InlineKeyboardButton(text='Нет', callback_data='doc_apr_no'),
        ],
        [
            InlineKeyboardButton(
                text='🛠Доп/Ремонты',
                callback_data='additional',
            )
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_task_closed_approved_keyboard():
    logger.debug('Создаю клавиатуру для закрытия задачи диспетчером')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='Все верно',
                callback_data='apr_close_task',
            ),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_dispatcher_task_closed_keyboard(task_id: int):
    logger.debug('Создаю клавиатуру для закрытия задачи из диспетчера')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='Да',
                callback_data=f'disp_task_{task_id}',
            ),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_check_docks_keyboard():
    logger.debug('Создаю клавиатуру для запроса проверки документов')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='Проверить',
                callback_data='show_doc_yes',
            ),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_yes_no_cancel_keyboard():
    logger.debug('Создаю клавиатуру да-нет-отмена')
    inline_keyboard = [
        [
            InlineKeyboardButton(text='Да', callback_data='uni_yes'),
            InlineKeyboardButton(text='Нет', callback_data='uni_no'),
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_sd_task_keyboard(
        task_id: int,
        *,
        short: bool = True,
        assign: bool = False,
):
    logger.debug('Создаю Кнопку запроса доп информации по задаче SD')
    inline_keyboard = []
    if short:
        inline_keyboard.append([
            InlineKeyboardButton(
                text='📄 Показать полную информацию',
                callback_data=f'sd_task_{task_id}',
            ),
        ])
    if assign:
        inline_keyboard.append([
            InlineKeyboardButton(
                text='Назначить на инженера',
                callback_data=f'atask_{task_id}'
            ),
        ])
    if not inline_keyboard:
        return None
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_simpleone_task_keyboard(task_id: int):
    logger.debug('Создаю Кнопку запроса доп информации по задаче SimpleOne')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='📄 Показать полную информацию',
                callback_data=f'simpleone_task_{task_id}',
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_choice_legal_entity_keyboard():
    logger.debug('Создаю клавиатуру выбора юр лица')
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text='IRB+Unirest',
                callback_data='legal_irb',
            ),
        ],
        [
            InlineKeyboardButton(text='Myrest', callback_data='legal_am'),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
