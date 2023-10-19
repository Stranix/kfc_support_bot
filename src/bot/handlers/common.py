import logging

from aiogram import F
from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from asgiref.sync import sync_to_async
from django.conf import settings

from src.models import Group
from src.models import Employee
from src.models import BotCommand
from src.bot.keyboards import create_tg_keyboard_markup

logger = logging.getLogger('support_bot')
router = Router(name='common_handlers')


class UserActivationState(StatesGroup):
    employee = State()


class UserFeedBackState(StatesGroup):
    feedback = State()


@router.message(Command('start'))
async def cmd_start(message: types.Message, employee: Employee):
    logger.debug('Обработчик команды /start')
    emp_status = 'Активна' if employee.is_active else 'Не активна'
    await message.answer(
        f'Приветствую {employee.name}!\n'
        f'Статус учетной записи: {emp_status}'
    )


@router.callback_query(F.data.startswith('activate_'))
async def activate_user(query: types.CallbackQuery, state: FSMContext):
    logger.info('Активация пользователя')
    user_id = query.data.split('_')[1]
    employee = await Employee.objects.aget(id=user_id)
    employee.is_active = True
    await query.message.delete()
    await employee.asave()
    await state.update_data(employee=employee)
    groups = await sync_to_async(list)(
        Group.objects.exclude(name__contains='Администратор')
    )
    available_groups_name = [group.name for group in groups]
    await query.message.answer(
        'В какую группу добавить пользователя?',
        reply_markup=await create_tg_keyboard_markup(
            available_groups_name,
        )
    )
    await state.set_state(UserActivationState.employee)


@router.message(UserActivationState.employee)
async def activate_user_step_2(message: types.Message, state: FSMContext):
    logger.info('Активация пользователя шаг 2')
    data = await state.get_data()
    group_name = message.text
    group = await Group.objects.aget(name=group_name)
    new_employee: Employee = data['employee']
    await sync_to_async(new_employee.groups.add)(group)
    await new_employee.asave()
    await message.answer(f'Активировал пользователя {new_employee.name}')
    await message.bot.send_message(
        chat_id=new_employee.tg_id,
        text='Учетная запись активирована. \n'
             'При возникновении проблем обращайтесь к @SmurovK',
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.delete()
    await state.clear()


@router.message(Command('help'))
async def cmd_help(message: types.Message, employee: Employee):
    logger.debug('Обработчик команды /help')
    emp_groups = employee.groups.all()
    logger.debug('emp_groups: %s', emp_groups)
    bot_commands = await sync_to_async(list)(
        BotCommand.objects.prefetch_related('groups').filter(
            groups__in=emp_groups,
        )
    )
    available_commands = []
    for command in bot_commands:
        text = f'{command.name} - {command.description}'
        available_commands.append(text)

    await message.answer(
        'Список доступных команд:\n\n'
        + '\n'.join(set(available_commands))
    )


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


@router.message(Command('feedback'))
async def cmd_feedback(message: types.Message, state: FSMContext):
    await message.answer(
        'Оставьте пожелания по работе бота\n'
        'Для отмены используйте команду /cancel'
    )
    await state.set_state(UserFeedBackState.feedback)


@router.message(UserFeedBackState.feedback)
async def process_feedback(
        message: types.Message,
        employee: Employee,
        state: FSMContext,
):
    feedback = message.text
    await message.bot.send_message(
        settings.TG_BOT_ADMIN,
        f'Фидбек от пользователя {employee.name}\n\n{feedback}\n\n\n#feedback')
    await message.answer('FeedBack отправлен. Спасибо за обратную связь!')
    await state.clear()
