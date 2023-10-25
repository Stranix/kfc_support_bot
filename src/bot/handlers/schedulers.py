import logging

from datetime import timedelta

from asgiref.sync import sync_to_async

from django.utils import timezone
from django.conf import settings

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import F
from aiogram import Bot
from aiogram import html
from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup

from src.models import WorkShift
from src.models import Employee
from src.models import Group
from src.models import Task
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
        job_next_run_time = html.code(
            job.next_run_time.strftime('%d-%m-%Y %H:%M:%S'),
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


async def check_task_activate_step_1(
        bot: Bot,
        task_number: str,
        scheduler: AsyncIOScheduler,
):
    logger.debug('Проверка задачи %s первые 10 минут', task_number)
    notify = f'❗Внимание задачу {task_number} не взяли в работу спустя 10 мин'
    try:
        task = await Task.objects.select_related('performer')\
                                 .aget(number=task_number)
    except Task.DoesNotExist:
        logger.warning('Задачи %s не существует в БД', task_number)
        return

    if task.performer:
        logger.info('На задачу назначен инженер')
        return
    engineers_group = await Group.objects.aget(name='Инженеры')
    engineers = await sync_to_async(list)(
        Employee.objects.filter(
            groups=engineers_group,
            work_shifts__is_works=True,
        )
    )
    middle_engineers_group = await Group.objects.aget(name='Старшие инженеры')
    middle_engineers = await sync_to_async(list)(
        Employee.objects.filter(
            groups=middle_engineers_group,
            work_shifts__is_works=True,
        )
    )
    senior_engineers_group = await Group.objects.aget(name='Ведущие инженеры')
    senior_engineers = await sync_to_async(list)(
        Employee.objects.filter(
            groups=senior_engineers_group,
            work_shifts__is_works=True,
        )
    )
    logger.debug('middle_engineers: %s', middle_engineers)
    if not middle_engineers:
        logger.warning('На смене нет старших инженеров!')
        notify_for_senior = '‼Первая эскалация,на смене нет старших инженеров!'
        await send_notify(bot, senior_engineers, notify_for_senior)
        await send_notify(bot, engineers, notify)
        return
    await send_notify(bot, middle_engineers, notify)
    await send_notify(bot, engineers, notify)
    scheduler.add_job(
        check_task_activate_step_2,
        'date',
        run_date=timezone.now() + timedelta(minutes=settings.TASK_ESCALATION),
        timezone='Europe/Moscow',
        args=(bot, task_number),
        id=f'job_{task_number}_step2',
    )


async def check_task_activate_step_2(bot: Bot, task_number: str):
    logger.debug('Проверка задачи %s через 20 минут', task_number)
    notify = f'‼Задачу {task_number} не взяли работу в течении 20 минут'
    task = await Task.objects.select_related('performer')\
                             .aget(number=task_number)
    if task.performer:
        logger.info('На задачу назначен инженер')
        return
    senior_engineers = await get_senior_engineers()
    await send_notify(bot, senior_engineers, notify)


async def check_task_deadline(bot: Bot, task_number: str):
    logger.debug('Проверка задачи %s через два часа', task_number)
    notify = f'🆘Задача {html.code(task_number)} не закрыта за два часа'
    task = await Task.objects.select_related('performer')\
                             .aget(number=task_number)
    senior_engineers = await get_senior_engineers()
    if not task.performer:
        logger.warning(
            'Прошло два часа, а на задаче %s нет инженера',
            task_number,
        )
        notify = f'🧨Прошло два часа, а на задаче {task_number} нет инженера!'
        await send_notify(bot, senior_engineers, notify)
        return
    if task.finish_at:
        logger.debug('Задача завершена')
        return
    engineer = task.performer
    managers = await sync_to_async(list)(engineer.managers.all())
    recipients_notification = [*managers, *senior_engineers]
    recipients_notification = list(set(recipients_notification))
    logger.debug('recipients_notification: %s', recipients_notification)
    await send_notify(bot, recipients_notification, notify)


async def check_end_of_shift(bot: Bot, shift_id: int):
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
    await send_notify(bot, managers, notify)
    notify_to_engineer = '🔴 Прошло 9 часов, а у тебя не закрыта смена.\n\n' \
                         'Для закрытия смены используй команду /end_shift'
    await send_notify(bot, list(engineer), notify_to_engineer)
    logger.debug('Проверка завершена')
