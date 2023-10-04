import logging
import re

import aiogram.utils.markdown as md

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from asgiref.sync import sync_to_async
from django.utils import timezone

from src.models import Task
from src.models import Employee
from src.bot.keyboards import create_tg_keyboard_markup
from src.bot.keyboards import get_support_task_keyboard
from src.bot.keyboards import get_task_feedback_keyboard


logger = logging.getLogger('support_bot')
router = Router(name='support_task_handlers')


class TaskState(StatesGroup):
    show_info = State()
    close_task = State()


@router.message(Command('get_task'))
async def gel_task(message: types.Message, state: FSMContext):
    logger.info('Получаем список доступных задач')
    tasks = await sync_to_async(list)(
        Task.objects.filter(
            status='NEW',
            number__istartswith='sd',
        )
    )
    if not tasks:
        logger.warning('Нет новых задач')
        await message.answer('Нет новых задач 🥹')
        return
    tasks_numbers = [task.number for task in tasks]
    tasks_keyboard = await create_tg_keyboard_markup(tasks_numbers)
    await message.answer(
        'По какой задаче показать информацию?',
        reply_markup=tasks_keyboard,
    )
    await state.set_state(TaskState.show_info)
    logger.info('Список доступных задач отправлен')


@router.message(
    TaskState.show_info,
    F.text.regexp(r'SD-(\d{7})+').as_('regexp'),
)
async def show_task_info(
        message: types.Message,
        regexp: re.Match[str],
        state: FSMContext,
):
    logger.info(f'Запрос показа информации по задаче: {regexp.group()}')
    task_number = regexp.group()
    task = await Task.objects.select_related('performer')\
                             .aget(number=task_number)
    if task.performer:
        logger.warning('Заявку уже назначена на сотрудника')
        await message.answer(
            'Заявку взял другой сотрудник. Выберете другую. \n'
            'Поможет команда: /get_task',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

    await message.answer(
        f'Информация по задаче {md.hcode(task_number)}\n\n'
        f'Заявитель: {task.applicant}\n'
        f'Тема обращения: {task.title}\n'
        f'Описание: {task.description}\n',
        reply_markup=await get_support_task_keyboard(task.id),
    )
    logger.info('Информация по задаче отправлена')
    ReplyKeyboardRemove()
    await state.clear()


@router.callback_query(F.data.startswith('stask_'))
async def process_start_task(query: types.CallbackQuery):
    logger.info('Берем задачу в работу')
    task_id = query.data.split('_')[1]
    task = await Task.objects.select_related('performer').aget(id=task_id)
    if task.performer:
        logger.warning('Заявку уже назначена на сотрудника')
        await query.answer()
        await query.message.answer(
            'Заявку взял другой сотрудник. Выберете другую. \n'
            'Поможет команда: /get_task'
        )
        return
    employee = await Employee.objects.aget(tg_id=query.from_user.id)
    task.performer = employee
    task.status = 'IN_WORK'
    await task.asave()
    await query.message.delete()
    await query.message.answer(
        f'Вы взяли задачу {md.hbold(task.number)} в работу\n'
        'Для закрытия задачи, используйте команду /close_task',
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info('Задачу взял в работу сотрудник %s', employee.name)


@router.message(Command('close_task'))
async def close_task(message: types.Message, state: FSMContext):
    logger.info('Запрос на закрытие задачи')
    tasks = await sync_to_async(list)(
        Task.objects.prefetch_related('performer').filter(
            performer__tg_id=message.from_user.id,
            status='IN_WORK',
        )
    )
    if not tasks:
        logger.warning(
            'У сотрудника %s нет задач в работе',
            message.from_user.id,
        )
        await message.answer(
            'У вас нет задач в работе. \n'
            'Чтобы взять задачу в работу используйте команду /start_task \n'
            'Или можно выбрать задачу используя команду /get_task'
        )
        return
    task_number = [task.number for task in tasks]
    await message.answer(
        'Какую задачу будем закрывать?',
        reply_markup=await create_tg_keyboard_markup(task_number)
    )
    await state.set_state(TaskState.close_task)


@router.message(
    TaskState.close_task,
    F.text.regexp(r'SD-(\d{7})+').as_('regexp'),
)
async def process_close_task(
        message: types.Message,
        regexp: re.Match[str],
        state: FSMContext,
):
    logger.info(f'Закрываем задачу: {regexp.group()}')
    task_number = regexp.group()
    task = await Task.objects.select_related('performer')\
                             .aget(number=task_number)
    employee = await Employee.objects.aget(tg_id=message.from_user.id)
    task_applicant = await Employee.objects.aget(name=task.applicant)
    if task.performer.name != employee.name:
        logger.warning('Исполнитель и закрывающий отличаются')
        await message.answer(
            f'Это не ваша задача. Ответственный по задаче {task.performer} ',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    task.status = 'COMPLETED'
    task.finish_at = timezone.now()
    await task.asave()
    await message.bot.send_message(
        task_applicant.tg_id,
        'Ваше обращение закрыто.\n'
        'Оцените пожалуйста работу от 1 до 5',
        reply_markup=await get_task_feedback_keyboard(task.id)
    )
    await message.answer(
        'Задача завершена.\n'
        'Посмотреть список открытых задач: /get_task',
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
    logger.info('Задача %s закрыта', task.number)
