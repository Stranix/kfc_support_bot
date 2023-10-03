import logging

import aiogram.utils.markdown as md

from aiogram import Router
from aiogram import types
from aiogram.filters import Command

from django.utils import timezone

from src.models import Employee
from src.models import WorkShift

logger = logging.getLogger('support_bot')
router = Router(name='on_shift_handlers')


@router.message(Command('on_shift'))
async def on_shift(message: types.Message):
    logger.info('Сотрудник заступает на смену')
    employee = await Employee.objects.prefetch_related('managers')\
                                     .aget(tg_id=message.from_user.id)
    if await is_active_shift(employee):
        await message.answer('У вас уже есть открытая смена')
        return
    logger.debug('Фиксируем старт смены в БД')
    await WorkShift.objects.acreate(
        employee=employee,
        shift_start_at=timezone.now(),
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


async def is_active_shift(employee: Employee) -> bool:
    logger.info('Проверяем есть ли у пользователя не завершенные смены')
    try:
        await employee.work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
        )
        logger.info('У пользователя есть активная смена')
        return True
    except WorkShift.DoesNotExist:
        logger.warning('У пользователя нет активной смены')
        return False
