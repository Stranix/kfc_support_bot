import logging

from datetime import timedelta

from asgiref.sync import sync_to_async

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import F
from aiogram import html
from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup

from src.models import WorkShift
from src.models import Employee
from src.models import SDTask
from src.bot.utils import send_notify
from src.bot.utils import get_senior_engineers

logger = logging.getLogger('support_bot')
router = Router(name='scheduler_handlers')


class SchedulerJobState(StatesGroup):
    job_choice = State()


@router.message(Command('scheduler_jobs'))
async def get_scheduler_jobs(
        message: types.Message,
        scheduler: AsyncIOScheduler,
):
    jobs = scheduler.get_jobs()
    message_for_send = ['Активные задачи scheduler:\n']
    for job in jobs:
        job_next_run_time = job.next_run_time + timedelta(hours=3)
        job_next_run_time = html.code(
            job_next_run_time.strftime('%d-%m-%Y %H:%M:%S'),
        )
        job_info = f'<b>Job id:</b> {html.code(job.id)}\n' \
                   f'<b>Job next_run_time:</b> {job_next_run_time}\n'
        message_for_send.append(job_info)
    await message.answer('\n'.join(message_for_send))


@router.message(Command('close_scheduler_job'))
async def close_scheduler_job(
        message: types.Message,
        state: FSMContext,
):
    await message.answer('Какой job будем удалять?')
    await state.set_state(SchedulerJobState.job_choice)


@router.message(F.text.startswith('job_'))
async def process_close_scheduler_job(
        message: types.Message,
        scheduler: AsyncIOScheduler,
        state: FSMContext,
):
    scheduler.remove_job(message.text)
    await message.answer(f'Job {message.text} удален')
    await state.clear()


async def check_task_activate_step_1(task_number: str):
    logger.debug('Проверка задачи %s первые 10 минут', task_number)
    notify = f'❗Внимание задачу {task_number} не взяли в работу спустя 10 мин'
    try:
        task = await SDTask.objects.select_related(
            'performer',
            'applicant',
        ).aget(number=task_number)
    except SDTask.DoesNotExist:
        logger.warning('Задачи %s не существует в БД', task_number)
        return

    if task.performer:
        logger.info('На задачу назначен инженер')
        return
    engineers = await Employee.objects.employees_on_work_by_group_name(
        group_name='Инженеры',
    )
    middle_engineers = await Employee.objects.employees_on_work_by_group_name(
        group_name='Старшие инженеры',
    )
    senior_engineers = await Employee.objects.employees_on_work_by_group_name(
        group_name='Ведущие инженеры',
    )
    logger.debug('middle_engineers: %s', middle_engineers)
    if not middle_engineers:
        logger.warning('На смене нет старших инженеров!')
        notify_for_senior = '‼Первая эскалация,на смене нет старших инженеров!'
        await send_notify(senior_engineers, notify_for_senior)
    await send_notify([*engineers, *middle_engineers], notify)
    await send_notify(
        [task.applicant],
        f'Не взяли в работу задачу {task.number} за 10 минут.\nСообщил старшим'
    )


async def check_task_activate_step_2(task_number: str):
    logger.debug('Проверка задачи %s через 20 минут', task_number)
    notify = f'‼Задачу {task_number} не взяли работу в течении 20 минут'
    task = await SDTask.objects.select_related('applicant', 'performer')\
                               .aget(number=task_number)
    if task.performer:
        logger.info('На задачу назначен инженер')
        return
    senior_engineers = await get_senior_engineers()
    await send_notify(senior_engineers, notify)
    await send_notify(
        [task.applicant],
        f'Не взяли в работу задачу {task.number} за 20 минут.\n'
        f'Сообщил Ведущим'
        f'\n\n{html.italic("Инженеры работают, как правило с 8 утра")}'
    )


async def check_task_deadline(task_number: str):
    logger.debug('Проверка задачи %s через два часа', task_number)
    notify = f'🆘Задача {html.code(task_number)} не закрыта за два часа'
    task = await SDTask.objects.select_related('performer')\
                               .aget(number=task_number)
    senior_engineers = await get_senior_engineers()
    if not task.performer:
        logger.warning(
            'Прошло два часа, а на задаче %s нет инженера',
            task_number,
        )
        notify = f'🧨Прошло два часа, а на задаче {task_number} нет инженера!'
        await send_notify(senior_engineers, notify)
        return
    if task.finish_at:
        logger.debug('Задача завершена')
        return
    engineer = task.performer
    managers = await sync_to_async(list)(engineer.managers.all())
    recipients_notification = [*managers, *senior_engineers]
    recipients_notification = list(set(recipients_notification))
    logger.debug('recipients_notification: %s', recipients_notification)
    await send_notify(recipients_notification, notify)


async def check_end_of_shift(shift_id: int):
    logger.debug('Проверка завершении смены сотрудником после 9 часов')
    shift = await WorkShift.objects.select_related('employee')\
                                   .aget(id=shift_id)
    engineer = shift.employee
    notify = f'🔴 У сотрудника {engineer.name} не закрыта смена спустя 9 часов'
    if shift.shift_end_at:
        logger.debug(
            'Смена %s сотрудника %s, закрыта в %s',
            shift.id,
            engineer.name,
            shift.shift_end_at.strftime('%d-%m-%Y %H:%M:%S'),
        )
        return
    logger.warning(
        'У сотрудника %s не закрыта смена %s',
        engineer.name,
        shift.id,
    )
    logger.debug('Отправка уведомления менеджерам')
    managers = await sync_to_async(list)(engineer.managers.all())
    logger.debug('managers: %s', managers)
    await send_notify(managers, notify)
    logger.debug('Отправка уведомления инженеру')
    notify_to_engineer = '🔴 Прошло 9 часов, а у тебя не закрыта смена.\n\n' \
                         'Для закрытия смены используй команду /end_shift'
    await send_notify([engineer], notify_to_engineer)
    logger.debug('Проверка завершена')
