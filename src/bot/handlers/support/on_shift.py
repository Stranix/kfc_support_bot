import logging

import aiogram.utils.markdown as md

from aiogram import types
from aiogram.dispatcher import FSMContext

from django.utils import timezone

from src.models import Employee
from src.models import WorkShift

logger = logging.getLogger('support_bot')


async def on_shift(message: types.Message, state: FSMContext):
    logger.info('Сотрудник заступает на смену')
    employee = await Employee.objects.aget(tg_id=message.from_user.id)
    logger.debug('Фиксируем старт смены в БД')
    shift = await WorkShift.objects.acreate(
        employee=employee,
        shift_start_at=timezone.now(),
    )
    logger.debug('Сохраняем информацию в store')
    await state.set_data(
        {
            message.from_user.id: {
                'shift': shift
            }
        }
    )
    logger.info('Отправляю уведомление менеджеру и пользователю')
    await message.answer('Вы добавлены в очередь на получение задач')
    for manager in employee.managers.all():
        await message.bot.send_message(
            manager.tg_id,
            md.text(
                'Сотрудник: ' + md.hcode(employee.name),
                '\nЗаступил на смену',
            ),
        )
