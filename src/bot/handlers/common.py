import re
import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from django.conf import settings

from src.bot.keyboards import get_user_activate_keyboard
from src.models import Employee

logger = logging.getLogger('support_bot')


def register_handlers_common(dp: Dispatcher):
    logger.info('Регистрация общих команд')
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_help, commands="help")
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
    dp.register_callback_query_handler(
        callback_cmd_cancel,
        lambda call: re.match('user_', call.data),
        state='*',
    )


async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    try:
        employee = await Employee.objects.aget(tg_id=user_id)
        emp_status = 'Активна' if employee.is_active else 'Не активна'
        await message.answer(
            f'Приветствую {employee.name}!\n'
            f'Статус учетной записи: {emp_status}'
        )
    except Employee.DoesNotExist:
        employee = await Employee.objects.acreate(
            name=message.from_user.full_name,
            tg_id=user_id,
        )
        await message.bot.send_message(
            chat_id=settings.TG_BOT_ADMIN,
            text=md.text(
                'Новый пользователь \n\n',
                'Данные: \n' + md.hcode(message),
            ),
            reply_markup=await get_user_activate_keyboard(employee.id)
        )
        await message.answer('Заявка на регистрацию отправлена.')


async def activate_user(query: types.CallbackQuery):
    logger.info('Активация пользователя')
    user_id = query.data.split('_')[1]
    employee = await Employee.objects.aget(id=user_id)
    employee.is_active = True
    await employee.asave()
    await query.bot.send_message(
        chat_id=settings.TG_BOT_ADMIN,
        text='Активировал'
    )
    await query.bot.send_message(
        chat_id=settings.TG_BOT_ADMIN,
        text='Учетная запись активирована. '
             'При возникновении проблем обращайтесь к @SmurovK',
    )


async def cmd_help(message: types.Message):
    text = [
        'Список команд: ',
        '/help - Получить справку',
        '/sync_tr - Синхронизация транзитов',
        '/sync_rest - Синхронизация ресторана(ов)',
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
