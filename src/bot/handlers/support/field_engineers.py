import re
import logging

from datetime import timedelta

from aiogram import F
from aiogram import Router
from aiogram import html
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from django.db.models import Q
from django.conf import settings
from django.utils import timezone

from src.models import SDTask
from src.models import Employee
from src.bot.utils import send_notify
from src.bot.utils import send_notify_to_seniors_engineers
from src.bot.keyboards import get_support_task_keyboard
from src.bot.keyboards import get_choice_support_group_keyboard
from src.bot.keyboards import get_approved_task_keyboard
from src.bot.handlers.schedulers import check_task_deadline
from src.bot.handlers.schedulers import check_task_activate_step_1
from src.bot.handlers.schedulers import check_task_activate_step_2

logger = logging.getLogger('support_bot')
router = Router(name='field_engineers_handlers')


class NewTaskState(StatesGroup):
    support_group = State()
    get_gsd_number = State()
    descriptions = State()
    approved = State()


@router.message(Command('support_help'))
async def start_new_support_task(
        message: types.Message,
        employee: Employee,
        state: FSMContext,
):
    logger.info('Запрос на создание новой выездной задачи')
    if not await employee.groups.filter(
            Q(name__contains='Подрядчик') | Q(name='Администраторы')
    ).afirst():
        logger.warning(
            'Пользователь %s не состоит в группе Подрядчики',
            employee.name,
        )
        await message.answer('Нет прав на использование команды')
        return
    keyboard = await get_choice_support_group_keyboard()
    await message.answer(
        'Чья помощь требуется',
        reply_markup=keyboard,
    )
    await state.set_state(NewTaskState.support_group)


@router.callback_query(
    NewTaskState.support_group,
    F.data.startswith('engineer') | F.data.startswith('dispatcher')
)
async def new_task_engineer(query: types.CallbackQuery, state: FSMContext):
    logger.info('Запрос на создание новой задачи поддержки')
    await query.message.delete()
    await state.update_data(support_group=query.data)
    await query.message.answer(
        'Напишите номер заявки по которой вы приехали\n'
        f'Например: {html.code("1395412")}'
    )
    await state.set_state(NewTaskState.get_gsd_number)


@router.message(NewTaskState.get_gsd_number)
async def process_get_gsd_number(message: types.Message, state: FSMContext):
    logger.info('Обработка номера задачи от инженера')
    task_number = re.match(r'(\d{6,7})+', message.text)
    if not task_number:
        logger.warning('Не правильный номер задачи')
        await message.answer(
            'Не правильный формат номера задачи\n'
            'Номер задачи должен быть от 6 до 7 цифр\n'
            f'Пример: {html.code("1395412")} \n\n'
            + html.italic('Если передумал - используй команду отмены /cancel')
        )
        return
    await state.update_data(get_gsd_number=task_number.group())
    await message.answer('Напиши с чем нужна помощь?')
    await state.set_state(NewTaskState.descriptions)
    logger.info('Обработано')


@router.message(NewTaskState.descriptions)
async def process_task_descriptions(message: types.Message, state: FSMContext):
    logger.info('Получение описание по задаче')
    task_description = message.text
    if not task_description:
        await message.answer(
            f'Нет описания по задаче. Чем помочь?\n\n'
            f'{html.italic("описание только в виде текста")}'
        )
        return
    data = await state.get_data()
    task_number = data['get_gsd_number']
    await state.update_data(descriptions=task_description)
    await message.answer(
        'Подводим итог: \n'
        f'Требуется помощь по задаче: SC-{task_number}\n'
        f'Детали: {task_description}\n\n'
        'Все верно?',
        reply_markup=await get_approved_task_keyboard(task_number)
    )
    await state.set_state(NewTaskState.approved)
    logger.info('Описание получено')


# TODO продумать логику уведомлений если задача уже в работе
@router.callback_query(F.data.startswith('approved_new_task'))
async def process_task_approved(
        query: types.CallbackQuery,
        employee: Employee,
        scheduler: AsyncIOScheduler,
        state: FSMContext,
):
    logger.info('Процесс подтверждения и создания новой заявки')
    await query.message.edit_text('Формирую задачу. Ожидайте...')
    data = await state.get_data()
    logger.debug('state_data: %s', data)
    task = await SDTask.objects.acreate(
        applicant=employee.name,
        title=f'Помощь по заявке SС-{data["get_gsd_number"]}',
        support_group=data['support_group'].upper(),
        description=data['descriptions'],
    )
    task.number = f'SD-{task.id}'
    await task.asave()
    logger.debug('Задача зафиксирована в БД. Номер: %s', task.number)
    await add_tasks_schedulers(task, scheduler)
    await sending_new_task_notify(query, task, employee)
    await query.message.answer(
        f'Заявка принята. \n'
        f'Внутренний номер: {html.code(task.number)}\n'
        f'Инженерам отправлено уведомление\n\n'
        + html.italic('Регламентное время связи 10 минут')
    )
    await query.message.delete()
    await state.clear()
    logger.info('Процесс завершен')


@router.callback_query(F.data.startswith('rating_'))
async def task_feedback(query: types.CallbackQuery):
    logger.info('Оценка задачи')
    rating = query.data.split('_')[1]
    task_id = query.data.split('_')[2]
    task = await SDTask.objects.aget(id=task_id)
    task.rating = int(rating)
    await task.asave()
    await query.message.delete()
    await query.message.answer(f'Спасибо за оценку задачи {task.number}')
    logger.info('Оценка проставлена')


async def sending_new_task_notify(
        query: types.CallbackQuery,
        task: SDTask,
        employee: Employee,
):
    logger.info('Отправка уведомления по задачам инженерам на смене')
    message_for_send = f'Инженеру требуется помощь ' \
                       f'по задаче {html.code(task.number)}\n\n' \
                       f'Описание: {html.code(task.description)}\n' \
                       f'Телеграм для связи: {employee.tg_nickname}\n\n'
    if task.support_group == 'DISPATCHER':
        message_for_send += html.italic(
            '‼Не забудь запросить акт и заключение (если требуется)',
        )
    recipients = await get_recipients_on_shift_by_task_support_group(task)

    if not recipients:
        logger.warning('На смене нет инженеров или диспетчеров')
        notify = f'Поступил запрос на помощь, но нет инженеров на смене\n' \
                 f'Номер обращения: {html.code(task.number)}'
        await send_notify_to_seniors_engineers(notify)
        return

    keyboard = await get_support_task_keyboard(task.id)
    await send_notify(query.bot, recipients, message_for_send, keyboard)
    logger.info('Завершено')


async def get_recipients_on_shift_by_task_support_group(task: SDTask):
    logger.info('Получение сотрудников по группе поддержки')
    if task.support_group == 'DISPATCHER':
        dispatchers = await Employee.objects.dispatchers_on_work()
        logger.debug('dispatchers: %s', dispatchers)
        return dispatchers

    if task.support_group == 'ENGINEER':
        engineers = await Employee.objects.engineers_on_work()
        logger.debug('engineers: %s', engineers)
        return engineers


async def add_tasks_schedulers(task: SDTask, scheduler: AsyncIOScheduler):
    logger.debug('Добавление временных проверок по задаче')
    task_escalation = settings.TASK_ESCALATION
    task_deadline = settings.TASK_DEADLINE

    scheduler.add_job(
        check_task_activate_step_1,
        'date',
        run_date=timezone.now() + timedelta(minutes=task_escalation),
        timezone='Europe/Moscow',
        args=(task.number,),
        id=f'job_{task.number}_step1',
    )
    scheduler.add_job(
        check_task_activate_step_2,
        'date',
        run_date=timezone.now() + timedelta(minutes=task_escalation * 2),
        timezone='Europe/Moscow',
        args=(task.number,),
        id=f'job_{task.number}_step2',
    )
    scheduler.add_job(
        check_task_deadline,
        'date',
        run_date=timezone.now() + timedelta(minutes=task_deadline),
        timezone='Europe/Moscow',
        args=(task.number,),
        id=f'job_{task.number}_deadline',
    )
    logger.debug('Проверки добавлены')
