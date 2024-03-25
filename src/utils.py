from urllib.parse import urlparse

import pytz
import json
import logging

from ast import literal_eval as make_tuple

from datetime import time
from datetime import date
from datetime import datetime
from datetime import timedelta

from src.bot.scheme import TasksOnShift
from src.bot.scheme import EngineersOnShift
from src.bot.scheme import EngineerShiftInfo
from src.entities.SimpleOneClient import SimpleOneClient

from src.models import CustomGroup, Restaurant
from src.models import SDTask
from src.models import WorkShift
from src.models import SimpleOneRequestType
from src.models import SimpleOneSupportGroup
from src.models import SimpleOneIRBDepartment
from src.models import SimpleOneCompany
from src.models import SimpleOneCIService

logger = logging.getLogger('support_bot')


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
    works_shifts = WorkShift.objects.prefetch_related('new_employee').filter(
        shift_start_at__lte=shift_end_at,
        shift_start_at__gte=shift_start_at,
    )
    logger.debug('Выбираю обычных инженеров из списка смен')
    engineers_works_shifts = works_shifts.filter(
        new_employee__groups__name='Инженеры'
    )
    logger.debug('Выбираю старших инженеров из списка смен')
    middle_engineers_works_shifts = works_shifts.filter(
        new_employee__groups__name='Старшие инженеры'
    )
    logger.debug('Выбираю диспетчеров из списка смен')
    dispatchers_works_shifts = works_shifts.filter(
        new_employee__groups__name='Диспетчеры'
    )
    logger.debug('Инженеры: %s', engineers_works_shifts)
    logger.debug('Старшие инженеры: %s', middle_engineers_works_shifts)
    logger.debug('Диспетчеры: %s', dispatchers_works_shifts)
    engineers_shift_info = get_engineers_shift_info(
        shift_date,
        engineers_works_shifts,
    )
    middle_engineers_shift_info = get_engineers_shift_info(
        shift_date,
        middle_engineers_works_shifts,
    )
    dispatchers_shift_info = get_engineers_shift_info(
        shift_date,
        dispatchers_works_shifts,
    )
    total_engineers = engineers_works_shifts.count()
    total_engineers += middle_engineers_works_shifts.count()
    return EngineersOnShift(
        count=total_engineers,
        engineers=engineers_shift_info,
        middle_engineers=middle_engineers_shift_info,
        dispatchers=dispatchers_shift_info,
        dispatchers_count=dispatchers_works_shifts.count(),
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
            if break_shift_end and break_shift_start:
                total_breaks_time += break_shift_end - break_shift_start
        logger.debug('Время на перерыве: %s', total_breaks_time)
        logger.debug('Ищу задачи за смену у инженера')
        tasks = shift_engineer.new_employee.new_sd_tasks.filter(
            start_at__lte=shift_end_at,
            start_at__gte=shift_start_at,
            status='COMPLETED',
        )
        avg_rating = 0.0
        if tasks.count():
            tasks_rating = [task.rating for task in tasks if task.rating]
            if len(tasks_rating):
                avg_rating = sum(tasks_rating) / len(tasks_rating)

        engineer_group = ''
        try:
            engineer_group = shift_engineer.new_employee.groups.exclude(
                name='Задачи',
            ).first().name
        except CustomGroup.DoesNotExist:
            pass

        engineers.append(
            EngineerShiftInfo(
                name=shift_engineer.new_employee.name,
                group=engineer_group,
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
    tasks = SDTask.objects.in_period_date(shift_start_at, shift_end_at)
    return get_tasks_stat(tasks)


def get_tasks_stat(tasks: list) -> TasksOnShift:
    tasks_info, task_closed, avg_processing_time = prepare_tasks_info(tasks)

    avg_tasks_rating = 0.0
    tasks_rating = [task.rating for task in tasks if task.rating]
    if tasks_rating:
        avg_tasks_rating = sum(tasks_rating) / len(tasks_rating)

    tasks_on_shift = TasksOnShift(
        count=len(tasks),
        closed=task_closed,
        avg_processing_time=format_timedelta(avg_processing_time),
        tasks=tasks_info,
        avg_rating=avg_tasks_rating,
    )
    return tasks_on_shift


def prepare_tasks_info(tasks: list) -> tuple:
    tasks_info = []
    tasks_processing_time = []
    for task in tasks:
        task_fields = {
            'number': task.number,
            'title': task.title,
            'applicant': task.new_applicant,
            'performer': task.new_performer,
            'start_at': task.start_at,
            'finish_at': task.finish_at,
            'avg_processing_time': '-',
            'description': task.description,
            'status': task.status,
            'closing_comment': task.closing_comment,
            'support_group': task.support_group,
            'sub_tasks_number': '',
            'doc_path': '',
            'rating': task.rating,
        }
        if task.status == 'COMPLETED':
            processing_time = task.finish_at - task.start_at
            task_fields['processing_time'] = format_timedelta(processing_time)
            tasks_processing_time.append(processing_time)

        if task.sub_task_number:
            task_fields['sub_tasks_number'] = task.sub_task_number.split(',')

        if task.doc_path:
            task_fields['doc_path'] = make_tuple(task.doc_path)
            logger.debug('tuple_doc_path: %s', task_fields['doc_path'])

        tasks_info.append(task_fields)

    avg_tasks_processing_time = timedelta()
    if tasks_processing_time:
        avg_tasks_processing_time = sum(
            tasks_processing_time,
            timedelta(0)
        ) / len(tasks_processing_time)
    return tasks_info, len(tasks_processing_time), avg_tasks_processing_time


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
        return f'{hours} ч : {minutes} мин.'
    elif hours:
        # Display only hours
        return f'{hours} ч.'
    # Display only minutes
    return f'{minutes} мин.'


async def get_restaurant_by_ext_code(ext_code: int) -> Restaurant:
    logger.info('Пробую найти ресторан в бд по внешнему коду')
    logger.debug('ext_code: %s', ext_code)
    restaurant = await Restaurant.objects.filter(
        ext_code=ext_code,
    ).afirst()
    if not restaurant:
        logger.info('Для кода %s нет подходящего ресторана в бд', ext_code)

    logger.debug('restaurant %s', restaurant)
    return restaurant


async def get_restaurant_by_applicant(applicant: str) -> Restaurant:
    logger.info('Пробую найти ресторан в бд по заявителю')
    logger.debug('applicant: %s', applicant)
    restaurant = await Restaurant.objects.filter(
        ext_name__icontains=applicant.split()[1],
    ).afirst()
    if not restaurant:
        logger.info('Не нашел для %s подходящего ресторана в бд',
                    applicant)

    logger.debug('restaurant %s', restaurant)
    return restaurant


async def get_simpleone_service_name_by_url(
        service_link: str,
        api_client: SimpleOneClient = None,
) -> str:
    service_id = urlparse(service_link).path.split('/')[-1]
    logger.debug('Поиск service_name id (%s) в бд', service_id)
    try:
        service_name = await SimpleOneCIService.objects.values('name')\
                                                       .aget(id=service_id)
        return service_name
    except SimpleOneCIService.DoesNotExist:
        logger.debug('Совпадений в базе не найдено')
        if api_client is None:
            return ''
        logger.debug('Попытка получить %s из api', service_id)
        return await api_client.get_service_name(service_link)


async def get_simpleone_company_name_by_url(
        company_link: str,
        api_client: SimpleOneClient = None,
) -> str:
    company_id = urlparse(company_link).path.split('/')[-1]
    logger.debug('Поиск company_name id (%s) в бд', company_id)
    try:
        company_name = await SimpleOneCompany.objects.values('name')\
                                                     .aget(id=company_id)
        return company_name['name']
    except SimpleOneCompany.DoesNotExist:
        logger.debug('Совпадений в базе не найдено')
        if api_client is None:
            return ''
        logger.debug('Попытка получить %s из api', company_id)
        return await api_client.get_company_name(company_link)


async def get_simpleone_request_type_name_by_url(
        request_type_link: str,
        api_client: SimpleOneClient = None,
) -> str:
    type_id = urlparse(request_type_link).path.split('/')[-1]
    logger.debug('Поиск request_type_name id (%s) в бд', type_id)
    try:
        type_name = await SimpleOneRequestType.objects.values('name')\
                                                      .aget(id=type_id)
        return type_name
    except SimpleOneRequestType.DoesNotExist:
        logger.debug('Совпадений в базе не найдено')
        if api_client is None:
            return ''
        logger.debug('Попытка получить %s из api', type_id)
        return await api_client.get_request_type(request_type_link)


async def get_simpleone_assignment_group_name_by_url(
        assignment_group_link: str,
        api_client: SimpleOneClient = None,
) -> str:
    group_id = urlparse(assignment_group_link).path.split('/')[-1]
    logger.debug('Поиск assignment_group_name id (%s) в бд', group_id)
    try:
        group_name = await SimpleOneSupportGroup.objects.values('name')\
                                                        .aget(id=group_id)
        return group_name
    except SimpleOneSupportGroup.DoesNotExist:
        logger.debug('Совпадений в базе не найдено')
        if api_client is None:
            return ''
        logger.debug('Попытка получить %s из api', group_id)
        return await api_client.get_assignment_group_name(
            assignment_group_link,
        )


async def get_simpleone_depart_info_by_url(
        caller_department_link: str,
        api_client: SimpleOneClient = None,
) -> tuple:
    department_id = urlparse(caller_department_link).path.split('/')[-1]
    logger.debug('Поиск depart_info id (%s) в бд', department_id)
    try:
        department = await SimpleOneIRBDepartment.objects.values(
            'name',
            'ext_code',
        ).aget(id=department_id)
        department_name = department['name']
        department_ext_code = department['ext_code']
        return department_name, department_ext_code
    except SimpleOneIRBDepartment.DoesNotExist:
        logger.debug('Совпадений в базе не найдено')
        if api_client is None:
            return '', ''
        logger.debug('Попытка получить %s из api', department_id)
        depart_name, depart_code = await api_client.get_caller_department_info(
            caller_department_link,
        )
        await SimpleOneIRBDepartment.objects.acreate(
            id=int(department_id),
            name=depart_name,
            ext_code=depart_code,
        )
        return depart_name, depart_code
