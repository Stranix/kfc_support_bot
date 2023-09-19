import io
import json
import logging
import dataclasses

from aiogram.types import InputFile

from src.bot.scheme import SyncStatus
from src.models import Employee
from src.models import SyncReport
from src.models import ServerType

logger = logging.getLogger('support_bot')


async def prepare_report_as_file(sync_report: dict) -> InputFile:
    sync_errors = [dataclasses.asdict(report) for report in sync_report['error']]
    logger.debug(sync_errors)
    dumps = json.dumps(sync_errors, ensure_ascii=False, indent=4)
    stream_str = io.BytesIO(dumps.encode('utf-8'))
    return InputFile(stream_str, filename='sync_report.txt')


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
