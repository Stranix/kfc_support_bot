from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

choice_rep_sync = InlineKeyboardMarkup(row_width=3,
                                       inline_keyboard=[
                                           [
                                               InlineKeyboardButton(text='YUM!', callback_data='sync_yum'),
                                               InlineKeyboardButton(text='IRB', callback_data='sync_irb'),
                                               InlineKeyboardButton(text='Все', callback_data='sync_all'),
                                           ],
                                           [
                                               InlineKeyboardButton(text='Отмена', callback_data='sync_cancel')
                                           ]
                                       ])
