import logging

from aiogram import F
from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from django.conf import settings

from src.models import Employee
from src.bot.utils import user_registration

logger = logging.getLogger('support_bot')
router = Router(name='common_handlers')


@router.message(Command('start'))
async def cmd_start(message: types.Message, employee: Employee):
    logger.debug('Обработчик команды /start')
    if not employee:
        logger.info('Новый пользователь')
        await user_registration(message)
        return
    emp_status = 'Активна' if employee.is_active else 'Не активна'
    await message.answer(
        f'Приветствую {employee.name}!\n'
        f'Статус учетной записи: {emp_status}'
    )


@router.callback_query(F.data.startswith('activate_'))
async def activate_user(query: types.CallbackQuery):
    logger.info('Активация пользователя')
    user_id = query.data.split('_')[1]
    employee = await Employee.objects.aget(id=user_id)
    employee.is_active = True
    await employee.asave()
    await query.answer()
    await query.bot.send_message(
        chat_id=settings.TG_BOT_ADMIN,
        text='Активировал'
    )
    await query.bot.send_message(
        chat_id=employee.tg_id,
        text='Учетная запись активирована. \n'
             'При возникновении проблем обращайтесь к @SmurovK',
    )


@router.message(Command('help'))
async def cmd_help(message: types.Message):
    text = [
        'Список команд: ',
        '/help - Получить справку',
        '/sync_tr - Синхронизация транзитов',
        '/sync_rest - Синхронизация ресторана(ов)',
    ]
    await message.answer('\n'.join(text))


@router.message(Command('cancel'))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await message.answer(
        'Действие отменено',
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()


@router.callback_query(F.data == 'cancel')
async def callback_cmd_cancel(query: types.CallbackQuery, state: FSMContext):
    await query.answer('Действие отменено', show_alert=True)
    await query.message.delete()
    await state.clear()
