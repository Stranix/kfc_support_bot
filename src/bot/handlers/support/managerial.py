# TODO пока не используется, перекидывать на TelegramAppWeb?
import json
import pytz
import logging

from datetime import time
from datetime import datetime
from datetime import timedelta

from asgiref.sync import sync_to_async

from aiogram import Router
from aiogram import types
from aiogram.filters import Command

from django.utils import timezone

from src.models import SDTask
from src.models import CustomUser
from src.models import WorkShift

logger = logging.getLogger('support_bot')
router = Router(name='managerial_handlers')


@router.message(Command('unclosed_tasks'))
async def cmd_unclosed_tasks(message: types.Message, employee: CustomUser):
    logger.info('Запрос на показ всех не закрытых задач')
    report = {}
    unclosed_tasks = await sync_to_async(list)(
        SDTask.objects.prefetch_related(
            'new_applicant',
            'new_performer',
        ).filter(
            finish_at__isnull=True,
        )
    )
    report['count'] = len(unclosed_tasks)
    report['unclosed_tasks'] = []
    use_timezone = pytz.timezone('Europe/Moscow')
    time_format = '%d-%m-%Y %H:%M:%S'
    for task in unclosed_tasks:
        task_start_at = timezone.localtime(task.start_at, use_timezone)
        report['unclosed_tasks'].append({
            'number': task.number,
            'support_group': task.support_group,
            'applicant': task.new_applicant.name if task.new_applicant else '',
            'performer': task.new_performer.name if task.new_performer else '',
            'start_at': task_start_at.strftime(time_format),
            'title': task.title,
            'description': task.description,
        })
    report_as_doc = await prepare_report_as_file(report, 'unclosed_tasks.json')
    await message.answer_document(
        report_as_doc,
        caption='Все незакрытые задачи',
    )
    logger.info('Отчет отправлен %s', employee.name)


@router.message(Command('report'))
async def cmd_report(message: types.Message, employee: CustomUser):
    logger.info('Обработчик команды report')
    check_groups = await employee.groups.filter(
        name__in=('Ведущие инженеры', 'Администратор')
    ).afirst()
    if not check_groups:
        logger.warning(
            'Пользователь %s не может смотреть отчет',
            employee.name
        )
        await message.answer('🙅‍♂Нет прав на просмотр отчета')
        return
    today = timezone.now().date()
    tomorrow = today + timedelta(1)
    shift_start_at = datetime.combine(today, time(), tzinfo=pytz.UTC)
    shift_end_at = datetime.combine(tomorrow, time(), tzinfo=pytz.UTC)
    shift_end_at -= timedelta(seconds=1)
    shift_report = await get_current_shift_report(shift_start_at, shift_end_at)
    shift_report_as_doc = await prepare_report_as_file(shift_report)
    await message.answer_document(
        shift_report_as_doc,
        caption=f'Отчет по смене {shift_report["shift_date"]}',
    )
    logger.info('Отчет отправлен %s', employee.name)


async def prepare_report_as_file(
        shift_report: dict,
        file_name: str = 'shift_report.json',
) -> types.BufferedInputFile:
    logger.info('Подготовка отчета по сменам для отправки')
    dumps = json.dumps(shift_report, ensure_ascii=False, indent=4)
    file = dumps.encode('utf-8')
    logger.info('Подготовка завершена')
    return types.BufferedInputFile(file, filename=file_name)


async def get_current_shift_report(
        shift_start_at: datetime,
        shift_end_at: datetime,
) -> dict:
    logger.info('Собираю информацию по смене %s', shift_start_at.date())
    report = {
        'shift_date': shift_start_at.date().strftime('%d-%m-%Y'),
        'engineers_on_shift': await get_info_for_engineers_on_shift(
            shift_start_at,
            shift_end_at,
        ),
        'tasks': await get_task_by_shift(shift_start_at, shift_end_at)
    }
    logger.debug('report: %s', report)
    logger.info('Сбор информации по смене %s окончен', shift_start_at.date())
    return report


async def get_task_by_shift(
        shift_start_at: datetime,
        shift_end_at: datetime,
) -> dict:
    logger.info('Получаем информацию по задачам смены')
    tasks = {}
    tasks_db = await sync_to_async(
        SDTask.objects.prefetch_related(
            'new_applicant',
            'new_performer',
        ).filter
    )(
        start_at__lte=shift_end_at,
        start_at__gte=shift_start_at,
    )
    tasks_new = await sync_to_async(list)(
        tasks_db.filter(status='NEW', finish_at__isnull=True)
    )
    tasks_in_work = await sync_to_async(list)(
        tasks_db.filter(status='IN_WORK', finish_at__isnull=True)
    )
    tasks_closed = await sync_to_async(list)(
        tasks_db.filter(finish_at__isnull=False)
    )
    tasks['count'] = await tasks_db.acount()
    tasks['new'] = {
        'count': len(tasks_new),
        'numbers': [task.number for task in tasks_new if tasks_new]
    }
    tasks['in_work'] = {
        'count': len(tasks_in_work),
        'numbers': [task.number for task in tasks_in_work if tasks_in_work]
    }
    tasks['closed'] = {
        'count': len(tasks_closed),
        'numbers': [task.number for task in tasks_closed if tasks_closed]
    }
    tasks_info = []
    use_timezone = pytz.timezone('Europe/Moscow')
    time_format = '%d-%m-%Y %H:%M:%S'
    for task in await sync_to_async(list)(tasks_db.all()):
        task_finish_at = ''
        task_start_at = timezone.localtime(task.start_at, use_timezone)
        if task.finish_at:
            task_finish_at = timezone.localtime(task.finish_at, use_timezone)
            task_finish_at = task_finish_at.strftime(time_format)
        tasks_info.append({
            'number': task.number,
            'support_group': task.support_group,
            'applicant': task.new_applicant.name,
            'performer': task.new_performer.name if task.new_performer else '',
            'start_at': task_start_at.strftime(time_format),
            'closed_at': task_finish_at,
            'title': task.title,
            'description': task.description,
            'closing_comment': task.closing_comment,
            'sub_task_number': task.sub_task_number,
            'rating': task.rating if task.rating else 'Нет Оценки',
        })
    tasks['tasks_info'] = tasks_info
    logger.debug('tasks: %s', tasks)
    logger.info('Информация по задачам получена')
    return tasks


async def get_info_for_engineers_on_shift(
        shift_start_at,
        shift_end_at,
) -> dict:
    logger.info('Ищу инженеров на смене')
    engineers = []
    middle_engineers = []
    dispatchers = []
    works_shifts: list[WorkShift] = await sync_to_async(list)(
        WorkShift.objects.prefetch_related('new_employee').filter(
            shift_start_at__lte=shift_end_at,
            shift_start_at__gte=shift_start_at,
            shift_end_at__isnull=True,
        ).order_by('shift_start_at')
    )
    if not works_shifts:
        logger.warning(
            'Нет информации по инженерам за смену %s',
            shift_start_at.date(),
        )
    # TODO не правильная логика, переписать
    for work_shift in works_shifts:
        is_engineer = await work_shift.new_employee.groups.filter(
            name='Инженеры'
        ).afirst()
        is_middle_engineer = await work_shift.new_employee.groups.filter(
            name='Старшие инженеры'
        ).afirst()
        is_dispatchers = await work_shift.new_employee.groups.filter(
            name='Диспетчеры'
        ).afirst()
        if is_engineer:
            engineers.append(work_shift.new_employee)
            continue
        if is_middle_engineer:
            middle_engineers.append(work_shift.new_employee)
        if is_dispatchers:
            dispatchers.append(work_shift.new_employee)
    engineers_on_shift = {
        'count': len(works_shifts),
        'engineers': {
            'count': len(engineers),
            'names': [engineer.name for engineer in engineers],
        },
        'middle_engineers': {
            'count': len(middle_engineers),
            'names': [engineer.name for engineer in middle_engineers],
        },
        'dispatchers': {
            'count': len(dispatchers),
            'names': [dispatcher.name for dispatcher in dispatchers],
        },
    }
    logger.debug('engineers_on_shift: %s', engineers_on_shift)
    logger.info('Информация по инженерам на смене собрана')
    return engineers_on_shift
