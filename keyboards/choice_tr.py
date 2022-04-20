from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

choice_tr = InlineKeyboardMarkup(row_width=3,
                                 inline_keyboard=[
                                     [
                                       InlineKeyboardButton(text='YUM!', callback_data='yum'),
                                     ],
                                     [
                                       InlineKeyboardButton(text='Отмена', callback_data='cancel')
                                     ]
                                 ])
