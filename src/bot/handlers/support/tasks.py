import logging
import re

from aiogram import F
from aiogram import Router
from aiogram import html
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.utils import timezone
from django.utils.dateformat import format

from src.models import Task
from src.models import Group
from src.models import Employee
from src.bot.keyboards import create_tg_keyboard_markup
from src.bot.keyboards import get_support_task_keyboard
from src.bot.keyboards import get_task_feedback_keyboard

logger = logging.getLogger('support_bot')
router = Router(name='support_task_handlers')


class TaskState(StatesGroup):
    show_info = State()
    close_task = State()


class AssignedTaskState(StatesGroup):
    task = State()
    engineers_on_shift = State()
    task_applicant = State()


@router.message(Command('get_task'))
async def get_task(message: types.Message, state: FSMContext):
    logger.info('Получаем список доступных задач')
    tasks = await sync_to_async(list)(
        Task.objects.filter(
            status='NEW',
            number__istartswith='sd',
        ).order_by('-id')
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
    task = await Task.objects.select_related('performer') \
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
        f'Информация по задаче {html.code(task_number)}\n\n'
        f'Заявитель: {task.applicant}\n'
        f'Тема обращения: {task.title}\n'
        f'Описание: {task.description}\n',
        reply_markup=await get_support_task_keyboard(task.id),
    )
    logger.info('Информация по задаче отправлена')
    ReplyKeyboardRemove()
    await state.clear()


@router.callback_query(F.data.startswith('stask_'))
async def process_start_task(query: types.CallbackQuery, employee: Employee):
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
    task_applicant = await Employee.objects.aget(name=task.applicant)
    task.performer = employee
    task.status = 'IN_WORK'
    await task.asave()
    await query.message.delete()
    await query.message.answer(
        f'Вы взяли задачу {html.bold(task.number)} в работу\n'
        'Для закрытия задачи, используйте команду /close_task',
        reply_markup=ReplyKeyboardRemove()
    )
    await query.bot.send_message(
        task_applicant.tg_id,
        f'Вашу задачу взял в работу инженер: {employee.name}\n'
        f'Телеграм для связи: {employee.tg_nickname}'
    )
    logger.info('Задачу взял в работу сотрудник %s', employee.name)


@router.callback_query(F.data.startswith('atask_'))
async def process_assigned_task(
        query: types.CallbackQuery,
        employee: Employee,
        state: FSMContext,
):
    logger.info('Назначить задачу на сотрудника')
    task_id = query.data.split('_')[1]
    task = await Task.objects.select_related('performer').aget(id=task_id)

    if task.performer:
        logger.warning('Заявку уже назначена на сотрудника')
        await query.answer()
        await query.message.answer(
            f'Заявку взял другой сотрудник: {task.performer.name}'
        )
        return

    employee_engineer_group = await employee.groups.aget(
        Q(name__icontains='Администратор') | Q(name__icontains='инженер'),
    )
    logger.debug('employee_engineer_group: %s', employee_engineer_group)
    engineers_on_shift = await get_engineers_for_assigned_task(
        employee_engineer_group,
        employee.id,
    )
    if not engineers_on_shift:
        await query.message.answer(
            'Нет инженеров на смене на которых вы можете назначить задачу'
        )
        return
    engineers_names = [engineer.name for engineer in engineers_on_shift]
    keyboard = await create_tg_keyboard_markup(engineers_names)
    task_applicant = await Employee.objects.aget(name=task.applicant)
    await state.update_data(
        task=task,
        engineers_on_shift=engineers_on_shift,
        task_applicant=task_applicant
    )
    await query.message.answer(
        'Выберите инженера на смене для назначения',
        reply_markup=keyboard,
    )
    await query.message.delete()
    await state.set_state(AssignedTaskState.task)


@router.message(AssignedTaskState.task)
async def process_assigned_task_step_2(
        message: types.Message,
        employee: Employee,
        state: FSMContext,
):
    logger.info('Назначения задачи на инженера шаг 2')
    data = await state.get_data()
    task = Task.objects.select_related('performer').aget(id=data['task'].id)
    if task.performer:
        await message.answer(
            f'Задачу взял другой инженер {task.performer.name}'
        )
        await state.clear()
        return
    selected_engineer_name = message.text
    engineers_on_shift = data['engineers_on_shift']
    task_applicant = data['task_applicant']
    selected_engineer = None

    for engineer in engineers_on_shift:
        if engineer.name == selected_engineer_name:
            selected_engineer = engineer
            break
    logger.debug('engineers_on_shift: %s', engineers_on_shift)
    logger.debug('selected_engineer: %s', selected_engineer)
    task.performer = selected_engineer
    await task.asave()
    logger.info(
        'Инженер %s назначен на задачу %s',
        selected_engineer.name,
        task.number,
    )
    logger.info('Отправляю уведомление назначившему инженеру')
    await message.answer(
        f'Задача {html.code(task.number)} '
        f'назначена инженеру {html.code(selected_engineer.name)}'
    )
    logger.info('Отправлено')
    logger.info('Отправка уведомления исполнителю')
    await message.bot.send_message(
        selected_engineer.tg_id,
        f'{employee.name} назначил на вас задачу {task.number}\n.'
        f'Контакт для связи {task_applicant.name} '
        f'({task_applicant.tg_nickname})'
    )
    logger.info('Отправлено')
    logger.info('Отправка уведомления постановщику задачи')
    await message.bot.send_message(
        task_applicant.tg_id,
        f'Задача взята в работу инженером {html.code(selected_engineer.name)}'
        f'\nТелеграм для связи: {selected_engineer.tg_nickname}'
    )
    logger.info('Отправлено')
    await state.clear()


@sync_to_async
def get_engineers_for_assigned_task(
        current_employee_group: Group,
        current_employee_id: int,
):
    engineers_on_shift = Employee.objects.filter(work_shifts__is_works=True)
    logger.debug('Текущая группа сотрудника: %s', current_employee_group)
    if current_employee_group.name == 'Администраторы':
        logger.debug('Поиск всех инженеров на смене')
        engineers_on_shift = engineers_on_shift.filter(
            groups__name__in=(
                'Ведущие инженеры',
                'Старшие инженеры',
                'Инженеры',
            ),
        )
    if current_employee_group.name == 'Ведущие инженеры':
        logger.debug('Поиск Старших и обычных инженеров на смене')
        engineers_on_shift = engineers_on_shift.filter(
            groups__name__in=('Старшие инженеры', 'Инженеры'),
        )
    if current_employee_group.name == 'Старшие инженеры':
        logger.debug('Поиск обычных инженеров на смене')
        engineers_on_shift = engineers_on_shift.filter(groups__name='Инженеры')

    if not engineers_on_shift.exclude(id=current_employee_id):
        logger.warning('Нет инженеров на смене')
        return
    logger.debug('engineers_on_shift: %s', engineers_on_shift)
    logger.info('Нашел подходящих инженеров')
    return list(engineers_on_shift)


@router.message(Command('close_task'))
async def close_task(message: types.Message, state: FSMContext):
    logger.info('Запрос на закрытие задачи')
    tasks = await get_task_in_work_by_employee(message.from_user.id)
    if not tasks:
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
        employee: Employee,
        regexp: re.Match[str],
        state: FSMContext,
):
    logger.info(f'Закрываем задачу: {regexp.group()}')
    task_number = regexp.group()
    task = await Task.objects.select_related('performer') \
        .aget(number=task_number)
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


@router.message(Command('my_active_tasks'))
async def get_employee_active_tasks(
        message: types.Message,
):
    logger.info('Получение назначенных задач')
    tasks = await get_task_in_work_by_employee(message.from_user.id)
    if not tasks:
        await message.answer('У вас нет задач в работе')
        return
    file_to_send = await prepare_active_tasks_as_file(tasks)
    await message.answer_document(
        file_to_send,
        caption='Задачи в работе',
    )


@router.message(Command('new_tasks'))
async def get_new_tasks(
        message: types.Message,
):
    logger.info('Получение всех не назначенных задач')
    tasks = await sync_to_async(list)(
        Task.objects.filter(
            number__startswith='SD-',
            performer__isnull=True,
        )
    )
    logger.debug('Список найденных новых задач: %s', tasks)
    if not tasks:
        await message.answer('Нет новый задач')
        return
    file_to_send = await prepare_new_tasks_as_file(tasks)
    await message.answer_document(
        file_to_send,
        caption='Задачи в работе',
    )


async def prepare_active_tasks_as_file(
        tasks: list[Task]
) -> types.BufferedInputFile:
    logger.info('Подготовка  списка задач на пользователе в виде файла')
    report = ['У вас в работе следующие задачи: \n']
    time_formatted_mask = 'd-m-Y H:i:s'
    for task in tasks:
        start_at = format(task.start_at, time_formatted_mask)
        text = f'{task.number}\n\n' \
               f'Заявитель: {task.applicant}\n' \
               f'Тип обращения: {task.title}\n' \
               f'Дата регистрации: {start_at}\n' \
               f'Текст обращения: {task.description}'
        report.append(text)

    file = '\n\n'.join(report).encode('utf-8')
    file_name = format(timezone.now(), 'd-m-Y') + '_tasks.txt'
    logger.info('Подготовка завершена')
    return types.BufferedInputFile(file, filename=file_name)


async def prepare_new_tasks_as_file(
        tasks: list[Task]
) -> types.BufferedInputFile:
    logger.info('Подготовка  списка не назначенных задач в виде файла')
    report = ['Новые задачи: \n']
    time_formatted_mask = 'd-m-Y H:i:s'
    for task in tasks:
        start_at = format(task.start_at, time_formatted_mask)
        text = f'{task.number}\n\n' \
               f'Заявитель: {task.applicant}\n' \
               f'Тип обращения: {task.title}\n' \
               f'Дата регистрации: {start_at}\n' \
               f'Текст обращения: {task.description}'
        report.append(text)

    file = '\n\n'.join(report).encode('utf-8')
    file_name = format(timezone.now(), 'd-m-Y') + '_new_tasks.txt'
    logger.info('Подготовка завершена')
    return types.BufferedInputFile(file, filename=file_name)


async def get_task_in_work_by_employee(employee_id: id) -> list[Task] | None:
    logger.info('Получение задач в работе по сотруднику с id: %s', employee_id)
    tasks = await sync_to_async(list)(
        Task.objects.prefetch_related('performer').filter(
            performer__tg_id=employee_id,
            status='IN_WORK',
        )
    )
    if not tasks:
        logger.warning(
            'У сотрудника %s нет задач в работе',
            employee_id,
        )
        return
    logger.info('Задачи получены')
    return tasks
