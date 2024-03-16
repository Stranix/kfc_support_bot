import logging

from datetime import timedelta

from aiogram import F
from aiogram import html
from aiogram import types
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup

from src.entities.Scheduler import Scheduler

logger = logging.getLogger('support_bot')
router = Router(name='scheduler_handlers')


class SchedulerJobState(StatesGroup):
    job_choice = State()


@router.message(Command('scheduler_jobs'))
async def get_scheduler_jobs(
        message: types.Message,
        scheduler: Scheduler,
):
    jobs = scheduler.aio_scheduler.get_jobs()
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
        scheduler: Scheduler,
        state: FSMContext,
):
    scheduler.aio_scheduler.remove_job(message.text)
    await message.answer(f'Job {message.text} удален')
    await state.clear()
