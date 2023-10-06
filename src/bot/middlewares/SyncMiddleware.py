import logging

from typing import Any
from typing import Dict
from typing import Callable
from typing import Awaitable

from aiogram import BaseMiddleware
from aiogram import html
from aiogram.types import CallbackQuery

from django.utils import timezone
from django.utils.dateformat import format

from src.models import Employee
from src.models import SyncReport
from src.bot.keyboards import get_report_keyboard

logger = logging.getLogger('support_bot')


class SyncMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        trust_groups = [
            'Администраторы',
            'Ведущие инженеры',
            'Старшие инженеры',
        ]
        employee: Employee = data['employee']
        if event.data not in ('tr_all', 'rest_all'):
            return await handler(event, data)

        if not await employee.groups.filter(name__in=trust_groups).aexists():
            await event.message.delete()
            await event.message.answer('Нет прав на выполнения масс синхры')
            return

        report = await SyncReport.objects.select_related('employee') \
            .filter(user_choice__in=('all', 'rest_all')) \
            .order_by('-start_at') \
            .afirst()

        if not report:
            logger.debug('нет подходящего отчета по синхронизации')
            return await handler(event, data)

        if (timezone.now() - report.start_at).total_seconds() < 600:
            logger.warning('С запуска синхронизации прошло меньше 10 минут')
            await event.message.delete()
            report_start_at = format(report.start_at, 'd-m-Y H:i:s')
            await event.message.answer(
                'Запуск массовой синхронизации только раз в 10 минут\n\n'
                f'Последний запуск от:  {html.code(report.employee.name)}\n'
                f'Время запуска: {html.code(report_start_at)}',
                reply_markup=await get_report_keyboard(report.id)
            )
            return
        return await handler(event, data)
