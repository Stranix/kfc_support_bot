import io
import json
import logging
import dataclasses

import aiogram.utils.markdown as md
from aiogram import types
from aiogram.types import InputFile

from src.bot.scheme import SyncStatus
from src.models import Employee
from src.models import SyncReport
from src.models import ServerType

logger = logging.getLogger('support_bot')


async def prepare_report_as_file(report_id: int) -> InputFile:
    logger.info('Подготовка отчета для отправки')
    sync_report = await SyncReport.objects.select_related(
        'employee', 'server_type'
    ).aget(id=report_id)
    final_report = {
        'initiator': sync_report.employee.name,
        'start_at': sync_report.start_at.strftime('%m-%d-%Y %H:%M:%S'),
        'server_type': sync_report.server_type.name,
        'report': {
            'errors': [],
            'completed': [],
        },
    }
    logger.debug('final_report: %s', final_report)
    logger.debug('sync_report.report: %s', sync_report.report)

    for item in sync_report.report:
        if item['status'] == 'error':
            final_report['report']['errors'].append(item)
        if item['status'] == 'ok':
            final_report['report']['completed'].append(item)

    dumps = json.dumps(final_report, ensure_ascii=False, indent=4)
    stream_str = io.BytesIO(dumps.encode('utf-8'))
    logger.info('Подготовка завершена')
    return InputFile(stream_str, filename='sync_report.json')


async def report_save_in_db(
        from_user_id: int,
        server_type_name: str,
        sync_statuses: list[SyncStatus],
) -> SyncReport:
    logger.info('Сохраняю отчет о синхронизации в БД')
    emp = await Employee.objects.aget(tg_id=from_user_id)
    server_type = await ServerType.objects.aget(name=server_type_name)
    report = [dataclasses.asdict(st) for st in sync_statuses]
    sync_report = await SyncReport.objects.acreate(
        employee=emp,
        server_type=server_type,
        report=report,
    )
    logger.info('Готово')
    return sync_report


async def create_sync_report(
        sync_statuses: list[SyncStatus]
) -> tuple[str, dict]:
    logger.info('Подготовка отчета по синхронизации')
    sync_report = {
        'ok': [],
        'error': [],
    }

    for sync_status in sync_statuses:
        if sync_status.status == 'ok':
            sync_report['ok'].append(sync_status)
        else:
            sync_report['error'].append(sync_status)
    message_report = md.text(
        'Результат синхронизации:\n',
        md.text('Успешно: ', md.hcode(len(sync_report['ok']))),
        md.text('Ошибок: ', md.hcode(len(sync_report['error'])))
    )
    return message_report, sync_report


async def send_report(query: types.CallbackQuery):
    report_id = query.data.split('_')[1]
    logger.debug('report_id: %s', report_id)
    report_as_doc = await prepare_report_as_file(int(report_id))
    await query.answer()
    await query.message.answer_document(
        report_as_doc,
        caption='Отчет по синхронизации',
    )
