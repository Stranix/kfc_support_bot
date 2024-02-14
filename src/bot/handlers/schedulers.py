import logging

from datetime import timedelta

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
from src.models import CustomGroup
from src.models import SDTask
from src.bot.utils import send_notify, send_notify_to_seniors_engineers
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
        print(job)
        job_next_run_time = job.trigger.run_date + timedelta(hours=3)
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
    managers = []
    try:
        task = await SDTask.objects.select_related(
            'new_performer',
            'new_applicant',
        ).aget(number=task_number)
    except SDTask.DoesNotExist:
        logger.warning('Задачи %s не существует в БД', task_number)
        return

    if task.new_performer:
        logger.info('На задачу назначен инженер')
        return

    if task.support_group == 'DISPATCHER':
        dispatcher_group = await CustomGroup.objects.select_related(
            'managers',
        ).aget(name='Диспетчеры')
        managers = dispatcher_group.managers.all()
    if task.support_group == 'ENGINEER':
        engineer_group = await CustomGroup.objects.select_related(
            'managers',
        ).aget(name='Инженеры')
        managers = engineer_group.managers.all()
    await send_notify(managers, notify)
    await send_notify(
        [task.new_applicant],
        f'Не взяли в работу задачу {task.number} за 10 минут.\nСообщил старшим'
    )


async def check_task_activate_step_2(task_number: str):
    logger.debug('Проверка задачи %s через 20 минут', task_number)
    notify = f'‼Задачу {task_number} не взяли работу в течении 20 минут'
    task = await SDTask.objects.select_related(
        'new_applicant',
        'new_performer',
    ).aget(number=task_number)
    if task.new_performer:
        logger.info('На задачу назначен инженер')
        return
    await send_notify_to_seniors_engineers(notify)
    await send_notify(
        [task.new_applicant],
        f'Не взяли в работу задачу {task.number} за 20 минут.\n'
        f'Сообщил Ведущим'
        f'\n\n{html.italic("Инженеры работают, как правило с 8 утра")}'
    )


async def check_task_deadline(task_number: str):
    logger.debug('Проверка задачи %s через два часа', task_number)
    notify = f'🆘Задача {html.code(task_number)} не закрыта за два часа'
    task = await SDTask.objects.select_related(
        'new_performer',
    ).aget(number=task_number)

    if task.finish_at:
        logger.debug('Задача завершена')
        return

    if not task.performer:
        logger.info(
            'Прошло два часа, а на задаче %s нет инженера',
            task_number,
        )
        notify = f'🧨Прошло два часа, а на задаче {task_number} нет инженера!'
        await send_notify_to_seniors_engineers(notify)
        return

    engineer = task.new_performer
    managers = []
    for group in engineer.groups.all():
        managers.extend(group.managers.all())

    recipients_notification = [*managers, *await get_senior_engineers()]
    recipients_notification = list(set(recipients_notification))
    logger.debug('recipients_notification: %s', recipients_notification)
    await send_notify(recipients_notification, notify)


async def check_end_of_shift(shift_id: int):
    logger.debug('Проверка завершении смены сотрудником после 9 часов')
    shift = await WorkShift.objects.select_related(
        'new_employee',
    ).aget(id=shift_id)
    engineer = shift.new_employee
    notify = f'🔴 У сотрудника {engineer.name} не закрыта смена спустя 9 часов'
    if shift.shift_end_at:
        logger.debug(
            'Смена %s сотрудника %s, закрыта в %s',
            shift.id,
            engineer.name,
            shift.shift_end_at.strftime('%d-%m-%Y %H:%M:%S'),
        )
        return
    logger.debug(
        'У сотрудника %s не закрыта смена %s',
        engineer.name,
        shift.id,
    )
    logger.debug('Отправка уведомления менеджерам')
    managers = []
    for group in engineer.groups.all():
        managers.extend(group.managers.all())
    logger.debug('managers: %s', managers)
    await send_notify(managers, notify)
    logger.debug('Отправка уведомления инженеру')
    notify_to_engineer = '🔴 Прошло 9 часов, а у тебя не закрыта смена.\n\n' \
                         'Для закрытия смены используй команду /end_shift'
    await send_notify([engineer], notify_to_engineer)
    logger.debug('Проверка завершена')
