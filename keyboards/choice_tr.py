from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

choice_tr = InlineKeyboardMarkup(row_width = 3,
                                 inline_keyboard=[
                                     [
                                       InlineKeyboardButton(text='YUM!', callback_data='yum'),
                                       InlineKeyboardButton(text='IRB', callback_data='irb'),
                                       InlineKeyboardButton(text='FZ', callback_data='fz'),
                                     ],
                                     [
                                       InlineKeyboardButton(text='Все', callback_data='all'),
                                       InlineKeyboardButton(text='Отмена', callback_data='cancel')
                                     ],
                                 ])
