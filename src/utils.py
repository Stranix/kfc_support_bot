import pytz
import json
import logging

from datetime import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from src.bot.scheme import TasksOnShift
from src.bot.scheme import EngineersOnShift
from src.bot.scheme import EngineerShiftInfo

from src.models import Task
from src.models import WorkShift

logger = logging.getLogger(__name__)


def configure_logging():
    """Загружаем конфигурация логирования из json. """
    try:
        with open('config/logging_config.json', 'r', encoding='utf-8') as file:
            logging.config.dictConfig(json.load(file))
    except FileNotFoundError:
        logger.warning(
            'Для настройки логирования нужен logging_config.json '
            'в корне проекта'
        )


def get_start_end_datetime_on_date(
        shift_date: date
) -> tuple[datetime, datetime]:
    today = shift_date
    tomorrow = today + timedelta(1)
    start_at = datetime.combine(today, time(), tzinfo=pytz.UTC)
    end_at = datetime.combine(tomorrow, time(), tzinfo=pytz.UTC)
    end_at -= timedelta(seconds=1)
    return start_at, end_at


def get_info_for_engineers_on_shift(
        shift_date: date,
) -> EngineersOnShift:
    shift_start_at, shift_end_at = get_start_end_datetime_on_date(shift_date)
    logger.debug('Получаю информацию по сменам за выбранную дату')
    works_shifts = WorkShift.objects.prefetch_related('employee').filter(
        shift_start_at__lte=shift_end_at,
        shift_start_at__gte=shift_start_at,
    )
    logger.debug('Выбираю обычных инженеров из списка смен')
    engineers_works_shifts = works_shifts.filter(
        employee__groups__name='Инженеры'
    )
    logger.debug('Выбираю старших инженеров из списка смен')
    middle_engineers_works_shifts = works_shifts.filter(
        employee__groups__name='Старшие инженеры'
    )
    logger.debug('Инженеры: %s', engineers_works_shifts)
    logger.debug('Старшие инженеры: %s', middle_engineers_works_shifts)
    engineers_shift_info = get_engineers_shift_info(
        shift_date,
        engineers_works_shifts,
    )
    middle_engineers_shift_info = get_engineers_shift_info(
        shift_date,
        middle_engineers_works_shifts,
    )
    total_engineers = engineers_works_shifts.count()
    total_engineers += middle_engineers_works_shifts.count()
    return EngineersOnShift(
        count=total_engineers,
        engineers=engineers_shift_info,
        middle_engineers=middle_engineers_shift_info,
    )


def get_engineers_shift_info(
        shift_date: date,
        engineers_works_shifts: list[WorkShift],
) -> list[EngineerShiftInfo]:
    logger.debug('Собираю информацию по инженерам')
    engineers = []
    shift_start_at, shift_end_at = get_start_end_datetime_on_date(shift_date)
    for shift_engineer in engineers_works_shifts:
        logger.debug('Считаю время на перерыве')
        total_breaks_time = timedelta()
        for break_shift in shift_engineer.break_shift.all():
            break_shift_start = break_shift.start_break_at
            break_shift_end = break_shift.end_break_at
            total_breaks_time += break_shift_end - break_shift_start
        logger.debug('Время на перерыве: %s', total_breaks_time)
        logger.debug('Ищу задачи за смену у инженера')
        tasks = shift_engineer.employee.tasks.filter(
            start_at__lte=shift_end_at,
            start_at__gte=shift_start_at,
            status='COMPLETED',
        )
        avg_rating = 0.0
        if tasks.count():
            tasks_rating = [task.rating for task in tasks if task.rating]
            avg_rating = sum(tasks_rating) / tasks.count()

        engineers.append(
            EngineerShiftInfo(
                name=shift_engineer.employee.name,
                shift_start_at=shift_engineer.shift_start_at,
                shift_end_at=shift_engineer.shift_end_at,
                total_breaks_time=format_timedelta(total_breaks_time),
                tasks_closed=tasks.count(),
                avg_tasks_rating=avg_rating,
            )
        )
    logger.debug('engineers: %s', engineers)
    return engineers


def get_tasks_on_shift(shift_date: datetime) -> TasksOnShift:
    shift_start_at, shift_end_at = get_start_end_datetime_on_date(shift_date)
    tasks = Task.objects.prefetch_related('performer').filter(
        number__startswith='SD-',
        start_at__lte=shift_end_at,
        start_at__gte=shift_start_at,
    )
    return get_tasks_stat(tasks)


def get_tasks_stat(tasks: list[Task]) -> TasksOnShift:
    tasks_processing_time = []
    for task in tasks:
        if not task.status == 'COMPLETED':
            continue
        tasks_processing_time.append(task.finish_at - task.start_at)

    avg_tasks_processing_time = timedelta()
    if tasks_processing_time:
        avg_tasks_processing_time = sum(
            tasks_processing_time,
            timedelta(0)
        ) / len(tasks_processing_time)

    avg_tasks_rating = 0.0
    tasks_rating = [task.rating for task in tasks if task.rating]
    if tasks_rating:
        avg_tasks_rating = sum(tasks_rating) / len(tasks_rating)

    tasks_on_shift = TasksOnShift(
        count=len(tasks),
        closed=len(tasks_processing_time),
        avg_processing_time=format_timedelta(avg_tasks_processing_time),
        tasks=tasks,
        avg_rating=avg_tasks_rating,
    )
    return tasks_on_shift


def get_sync_statuses(sync_report: dict) -> tuple[list, list]:
    errors = []
    completed = []
    for report in sync_report:
        if report['status'] == 'error':
            errors.append(report)
            continue
        if report['status'] == 'ok':
            completed.append(report)
    return completed, errors


def format_timedelta(delta: timedelta):
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = round((total_seconds % 3600) / 60)
    if minutes == 60:
        hours += 1
        minutes = 0
    if hours and minutes:
        return f'{hours} ч. : {minutes} мин.'
    elif hours:
        # Display only hours
        return f'{hours} ч.'
    # Display only minutes
    return f'{minutes} мин.'
