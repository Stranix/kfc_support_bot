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

from asgiref.sync import sync_to_async

from src.bot.keyboards import get_support_task_keyboard
from src.bot.keyboards import get_approved_task_keyboard
from src.models import Task
from src.models import Employee
from src.models import WorkShift

logger = logging.getLogger('support_bot')
router = Router(name='field_engineers_handlers')


class NewTaskState(StatesGroup):
    get_gsd_number = State()
    descriptions = State()
    approved = State()


@router.message(Command('support_help'))
async def new_task(message: types.Message, state: FSMContext):
    logger.info('Запрос на создание новой задачи')
    await message.answer(
        'Напишите номер заявки по которой вы приехали\n'
        f'Например: {md.hcode("1395412")}'
    )
    await state.set_state(NewTaskState.get_gsd_number)


@router.message(NewTaskState.get_gsd_number)
async def process_get_gsd_number(message: types.Message, state: FSMContext):
    logger.info('Обработка номера задачи от инженера')
    task_number = re.match(r'(\d{7})+', message.text)
    if not task_number:
        logger.warning('Не правильный номер задачи')
        await message.answer(
            'Не правильный формат номера задачи\n'
            f'Пример: {md.hcode("1395412")} \n\n' +
            md.hitalic('Если передумал - используй команду отмены /cancel')
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


@router.callback_query(F.data.startswith('approved_new_task'))
async def process_task_approved(query: types.CallbackQuery, state: FSMContext):
    logger.info('Процесс подтверждения и создания новой заявки')
    data = await state.get_data()
    logger.debug('state_data: %s', data)
    employee = await Employee.objects.aget(tg_id=query.from_user.id)
    task = await Task.objects.acreate(
        number=f'SD-{data["get_gsd_number"]}',
        applicant=employee.name,
        service='Локальная поддержка инженеров',
        title=f'Помощь по заявке SС-{data["get_gsd_number"]}',
        description=data['descriptions']
    )
    await sending_new_task_notify(query, task, employee)
    await query.message.answer(
        'Заявка принята. \n'
        'Инженерам отправлено уведомление\n\n' +
        md.hitalic('Регламентное время связи 10 минут')
    )
    await query.message.delete()
    await state.clear()
    logger.info('Процесс завершен')


@router.callback_query(F.data.startswith('rating_'))
async def task_feedback(query: types.CallbackQuery):
    logger.info('Оценка задачи')
    rating = query.data.split('_')[1]
    task_id = query.data.split('_')[2]
    task = await Task.objects.aget(id=task_id)
    task.rating = int(rating)
    await task.asave()
    await query.message.delete()
    await query.message.answer(f'Спасибо за оценку задачи {task.number}')
    logger.info('Оценка проставлена')


async def sending_new_task_notify(
        query: types.CallbackQuery,
        task: Task,
        employee: Employee,
):
    logger.info('Отправка уведомления по задачам инженерам на смене')
    work_shifts = await sync_to_async(list)(
        WorkShift.objects.prefetch_related('employee').filter(
            is_works=True,
        )
    )
    recipients = [work.employee.tg_id for work in work_shifts]
    logger.debug('Список tg_id сотрудников на работе: %s', recipients)
    message_for_send = md.text(
        'Инженеру требуется помощь по задаче',
        '\n\nОписание: ' + md.hcode(task.description),
        '\ntelegram: ' + employee.tg_nickname,
    )
    if not recipients:
        logger.warning('На смене нет инженеров')
        senior_engineers = await sync_to_async(list)(
            Employee.objects.prefetch_related('groups').filter(
                groups__name__contains='Ведущие инженеры'
            )
        )
        for senior_engineer in senior_engineers:
            await query.bot.send_message(
                senior_engineer.tg_id,
                'Поступил запрос на помощь, но нет инженеров на смене\n'
                'Номер обращения: ' + md.hcode(task.number)
            )
        return
    for recipient in recipients:
        await query.bot.send_message(
            recipient,
            message_for_send,
            reply_markup=await get_support_task_keyboard(task.id)
        )
    logger.info('Отправка завершена')
