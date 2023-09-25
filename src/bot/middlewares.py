import logging

import aiogram.utils.markdown as md

from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.dispatcher.middlewares import BaseMiddleware

from asgiref.sync import sync_to_async
from django.utils import timezone
from django.utils.dateformat import format

from src.bot import keyboards
from src.models import SyncReport, Employee, Right

logger = logging.getLogger('support_bot')


class SyncMiddleware(BaseMiddleware):

    async def on_pre_process_message(self, message: Message, _):
        if message.text in ('/sync_tr', '/sync_rest'):
            if not await check_right_in_employee(
                    message.from_user.id, 'Синхронизация'
            ):
                await message.answer('Нет прав на выполнение синхронизации')
                raise CancelHandler()

    async def on_pre_process_callback_query(self, callback: CallbackQuery, _):
        logger.debug('process_update callback %s', callback)
        report = await SyncReport.objects.select_related('employee')\
            .filter(user_choice__in=('all', ))\
            .order_by('-start_at')\
            .afirst()
        if (timezone.now() - report.start_at).total_seconds() < 900:
            logger.warning('С запуска синхронизации прошло меньше 15 минут')
            await callback.answer()
            report_start_at = format(report.start_at, 'd-m-Y H:i:s')
            await callback.message.answer(
                md.text(
                    'Запуск массовой синхронизации только раз в 15 минут\n\n',
                    'Последний запуск от: ' + md.hcode(report.employee.name),
                    '\n Время запуска: ' + md.hcode(report_start_at)
                ),
                reply_markup=await keyboards.get_report_keyboard(report.id)
            )
            raise CancelHandler()


@sync_to_async
def check_right_in_employee(employee_id: int, right_name: str) -> bool:
    logger.info('Проверка права у сотрудника')
    employee = Employee.objects.get(tg_id=employee_id)
    right = Right.objects.get(name=right_name)
    for group in employee.groups.all():
        if right in group.rights.all():
            logger.info(
                'У пользователя %s есть право %s',
                employee.name,
                right.name
            )
            return True
    logger.error('У пользователя %s нет права %s', employee.name, right.name)
    return False
