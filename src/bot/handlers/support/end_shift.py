import logging

from aiogram import Router
from aiogram import types
from aiogram.filters import Command

from src.bot import dialogs
from src.models import WorkShift
from src.entities.Message import Message
from src.entities.Service import Service
from src.entities.SupportEngineer import SupportEngineer


logger = logging.getLogger('support_bot')
router = Router(name='end_shift_handlers')


@router.message(Command('end_shift'))
async def end_shift(
        message: types.Message,
        support_engineer: SupportEngineer,
        service: Service,
):
    logger.info('Старт процесса завершения смены')
    try:
        work_shift = await support_engineer.end_work_shift()
        logger.debug('Удаляю scheduler проверки смены')
        await service.delete_scheduler_job_by_id(
            f'job_{work_shift.id}_end_shift')
        await message.answer(await dialogs.end_work_shift())
        if await support_engineer.is_middle_engineer:
            await Message.send_new_tasks_notify_for_middle(support_engineer)
        logger.info('Отправляю уведомление менеджеру')
        await Message.send_notify_to_group_managers(
            await support_engineer.group_id,
            await dialogs.engineer_end_shift(support_engineer.user.name),
        )
    except WorkShift.DoesNotExist:
        logger.warning('Не нашел открытую смену у сотрудника')
        await message.answer(await dialogs.error_no_active_shift())
        return
