import logging

from aiogram import Router
from aiogram import types
from aiogram.filters import Command

from src.bot import dialogs
from src.entities.Message import Message
from src.entities.Service import Service
from src.entities.SupportEngineer import SupportEngineer

logger = logging.getLogger('support_bot')
router = Router(name='on_shift_handlers')


@router.message(Command('on_shift'))
async def on_shift(
        message: types.Message,
        support_engineer: SupportEngineer,
        service: Service,
):
    logger.info('Сотрудник заступает на смену')
    if await support_engineer.is_active_shift:
        await message.answer(await dialogs.work_shift_exist())
        return

    logger.debug('Фиксируем старт смены в БД')
    shift = await support_engineer.start_work_shift()
    await service.add_check_shift(shift.id)

    logger.info('Отправляю уведомление менеджеру и пользователю')
    await message.answer(await dialogs.start_work_shift())
    if support_engineer.is_middle_engineer:
        await Message.send_new_tasks_notify_for_middle(support_engineer)
    await Message.send_notify_to_group_managers(
        await support_engineer.group_id,
        await dialogs.engineer_on_shift(support_engineer.user.name),
    )
