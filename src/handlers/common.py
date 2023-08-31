import logging

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

logger = logging.getLogger('support_bot')


def register_handlers_common(dp: Dispatcher):
    logger.info('Регистрация общих команд')
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_start, commands="help")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(
        cmd_cancel,
        Text(equals="отмена", ignore_case=True),
        state="*",
    )
    dp.register_callback_query_handler(
        callback_cmd_cancel,
        lambda call: call.data == 'cancel',
        state='*',
    )


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        'Приветствую вас',
        reply_markup=types.ReplyKeyboardRemove()
    )


async def cmd_help(message: types.Message):
    text = [
        'Список команд: ',
        '/help - Получить справку',
        '/sync_tr - Синхронизация транзитов',
        '/sync_rest - Синхронизация ресторана(ов)',
        '/sync_all - Синхронизация всех ресторанов с выбором Юр лица',
    ]
    await message.answer('\n'.join(text))


async def cmd_cancel(message: types.Message, state: FSMContext):
    await message.answer(
        'Действие отменено',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.finish()


async def callback_cmd_cancel(query: types.CallbackQuery, state: FSMContext):
    await query.answer('Действие отменено', show_alert=True)
    await query.message.delete()
    await state.finish()
