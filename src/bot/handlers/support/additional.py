import logging

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot import dialogs
from src.bot import services
from src.models import SDTask
from src.entities.Message import Message
from src.entities.FieldEngineer import FieldEngineer
from src.entities.SupportEngineer import SupportEngineer
from src.entities.Scheduler import Scheduler

logger = logging.getLogger('support_bot')
router = Router(name='additional_handlers')


@router.callback_query(F.data == 'additional')
async def process_additional_work(
        query: types.CallbackQuery,
        support_engineer: SupportEngineer,
        scheduler: Scheduler,
        state: FSMContext,
):
    """Передача заявки в чат доп работ"""
    logger.info('Обработчик передачи заявки на доп работы')
    await query.answer()
    data = await state.get_data()
    task: SDTask = data['close_task']
    docs = data['get_doc']
    external_task_number = await services.find_external_number_in_task(
        task.title,
    )
    if not external_task_number:
        logger.warning('Не смог найти номер в имени %s', task.title)
        await query.message.answer(await dialogs.error_task_not_found())
        return
    await query.message.delete()
    external_task_number = external_task_number[0]
    await support_engineer.close_sd_task_as_additional_work(task.id)
    await Message.send_notify_on_additional_work(
        FieldEngineer(task.new_applicant),
        support_engineer,
        str(task.id),
        external_task_number,
        task.title,
        docs,
    )
    job_id = f'job_{task.number}_deadline'
    await scheduler.delete_scheduler_job_by_id(job_id)
    await state.clear()
    logger.info('Работа обработчика завершена')
