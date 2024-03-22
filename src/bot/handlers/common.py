import logging

from aiogram import F
from aiogram import types
from aiogram import Router
from aiogram import html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from asgiref.sync import sync_to_async

from django.conf import settings

from src.bot import dialogs
from src.bot.services import prepare_restaurant_as_file_for_send
from src.models import CustomGroup, Restaurant
from src.models import CustomUser
from src.models import BotCommand
from src.bot.keyboards import create_tg_keyboard_markup

logger = logging.getLogger('support_bot')
router = Router(name='common_handlers')


class UserActivationState(StatesGroup):
    employee = State()


class UserFeedBackState(StatesGroup):
    feedback = State()


class RestaurantInfoState(StatesGroup):
    rest_name = State()


@router.message(Command('start'))
async def cmd_start(message: types.Message, employee: CustomUser):
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
    employee = await CustomUser.objects.aget(id=user_id)
    employee.is_active = True
    await query.message.delete()
    await employee.asave()
    await state.update_data(employee=employee)
    groups = await sync_to_async(list)(
        CustomGroup.objects.all()
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
    try:
        group = await CustomGroup.objects.aget(name=group_name)
    except CustomGroup.DoesNotExist:
        logger.warning('Не найдена группа %s', group_name)
        await state.clear()
        return
    new_employee: CustomUser = data['employee']
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
async def cmd_help(message: types.Message, employee: CustomUser):
    logger.debug('Обработчик команды /help')
    emp_groups = employee.groups.all()
    logger.debug('emp_groups: %s', emp_groups)
    bot_commands = await sync_to_async(list)(
        BotCommand.objects.prefetch_related('new_groups', 'category').filter(
            new_groups__in=emp_groups,
        )
    )
    available_commands = {}
    for command in set(bot_commands):
        text = f'{command.name} - {command.description}'
        try:
            available_commands[command.category.name]['commands'].append(text)
        except KeyError:
            available_commands[command.category.name] = {'commands': [text]}

    help_massage = ''
    for command_category, commands in available_commands.items():
        help_massage += f'{html.bold(command_category)}\n'
        for command in commands['commands']:
            help_massage += f'{command}\n'
        help_massage += '\n\n'
    if not help_massage:
        await message.answer('Нет доступных команд')
        return
    await message.answer(help_massage)


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
        employee: CustomUser,
        state: FSMContext,
):
    feedback = message.text
    await message.bot.send_message(
        settings.TG_BOT_ADMIN,
        f'Фидбек от пользователя {employee.name}\n\n{feedback}\n\n\n#feedback')
    await message.answer('FeedBack отправлен. Спасибо за обратную связь!')
    await state.clear()


@router.message(Command('rest_info'))
async def cmd_rest_info_step_1(message: types.Message, state: FSMContext):
    """Поиск информации по ресторану (поиск в имени)"""
    await message.answer(await dialogs.request_rest_name())
    await state.set_state(RestaurantInfoState.rest_name)


@router.message(RestaurantInfoState.rest_name)
async def cmd_rest_info_step_2(message: types.Message, state: FSMContext):
    """Поиск информации по ресторану (поиск в имени). Шаг 2"""
    restaurants = await Restaurant.objects.by_name(message.text)
    logger.debug('restaurants: %s', restaurants)
    if not restaurants:
        await message.reply(await dialogs.error_restaurant_not_found())
        await state.clear()
        return
    if len(restaurants) > 2:
        file_to_send = await prepare_restaurant_as_file_for_send(
            'Найденные рестораны',
            restaurants,
            'rests_info.txt'
        )
        await message.answer_document(file_to_send, caption='Рестораны')
        await state.clear()
        return
    for restaurant in restaurants:
        await message.reply(await dialogs.restaurant_info(restaurant))
