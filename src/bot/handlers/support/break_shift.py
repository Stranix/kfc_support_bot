import logging

from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup

from src.bot import dialogs
from src.models import WorkShift
from src.models import BreakShift
from src.exceptions import BreakShiftError
from src.entities.Message import Message
from src.entities.SupportEngineer import SupportEngineer

logger = logging.getLogger('support_bot')
router = Router(name='break_shift_handlers')


class WorkShiftBreakState(StatesGroup):
    break_status: State()


@router.message(Command('break_start'))
async def start_break_shift(
        message: types.Message,
        support_engineer: SupportEngineer,
):
    logger.info('/break_start. Пользователь: %s', support_engineer.user.name)
    try:
        await support_engineer.start_break()
        logger.info('Отправляю уведомление менеджеру и пользователю')
        await message.answer(await dialogs.start_break_message())
        await Message.send_notify_to_group_managers(
            await support_engineer.group_id,
            await dialogs.engineer_start_break(support_engineer.user.name),
        )
    except WorkShift.DoesNotExist:
        logger.warning('Не нашел открытую смену у сотрудника')
        await message.answer(await dialogs.error_no_active_shift())
    except BreakShiftError:
        logger.warning('Сотрудник %s уже на перерыве', support_engineer.user)
        await message.answer(await dialogs.error_active_break_exist())


@router.message(Command('break_stop'))
async def stop_break_shift(
        message: types.Message,
        support_engineer: SupportEngineer,
):
    logger.info('/break_stop. Пользователь: %s', support_engineer.user.name)
    try:
        await support_engineer.stop_break()
        logger.info('Отправляю уведомление менеджеру и пользователю')
        await message.answer(await dialogs.stop_break_message())
        await Message.send_notify_to_group_managers(
            await support_engineer.group_id,
            await dialogs.engineer_stop_break(support_engineer.user.name),
        )
    except WorkShift.DoesNotExist:
        logger.warning('Не нашел активный перерыв')
        await message.answer(await dialogs.error_no_active_breaks())
        return
    except BreakShift.DoesNotExist:
        await message.answer(await dialogs.error_active_break_not_exist())
        return
