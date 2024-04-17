import re
import logging

from urllib.parse import urlparse

from dataclasses import asdict
from dataclasses import dataclass

from typing import Any
from datetime import datetime

from bs4 import BeautifulSoup

from django.db import IntegrityError
from django.utils import timezone

from src import utils
from src.models import GSDTask
from src.models import Restaurant
from src.models import SimpleOneTask
from src.entities.SimpleOneClient import SimpleOneClient

logger = logging.getLogger('app_parsers')
logger.setLevel(logging.DEBUG)


@dataclass
class ParsedGSDTask:
    applicant: str
    number: str
    title: str
    gsd_group: str
    start_at: Any
    expired_at: Any
    service: str = ''
    description: str = ''
    restaurant: Restaurant | None = None


@dataclass
class ParsedSimpleOneTask:
    assignment_group_link: str
    company_link: str
    description: str
    number: str
    fact_start: datetime
    service_link: str
    subject: str
    sys_id: str
    caller_department_link: str
    contact_information: str
    sla: str
    exp_sla: datetime | None
    request_type_link: str
    restaurant: Restaurant | None = None
    request_type: str = ''
    api_path: str = ''
    caller_department: str = ''
    service: str = ''
    company: str = ''
    assignment_group: str = ''


async def parse_gsd_mail(mail_text: str) -> ParsedGSDTask:
    logger.info('Разбираем сообщение GSD')
    split_line = '---------------------------------------------------'
    mail_text = mail_text.split(split_line)
    mail_text = mail_text[0] + mail_text[1]
    message = mail_text.split('Описание:')
    main_info = list(filter(None, message[0].split('\r\n')))
    start_at = convert_str_datetime(main_info[8].split(': ')[1])
    expired_at = convert_str_datetime(main_info[10].split(': ')[1])
    task = ParsedGSDTask(
        applicant=main_info[2].split(': ')[1],
        number=re.search(r'SC-(\d{7})+', main_info[0]).group(),
        service=main_info[11].split(': ')[1],
        start_at=start_at,
        expired_at=expired_at,
        title=main_info[12].split(': ')[1],
        gsd_group=re.search(r'«([\s\S]+?)»', main_info[0]).group(),
        description=mail_text,
    )
    task.restaurant = await utils.get_restaurant_by_applicant(task.applicant)
    logger.info('Информация по задаче собрана')
    return task


async def parse_simpleone_mail(mail_text: str) -> ParsedSimpleOneTask:
    exp_sla = None
    soup = BeautifulSoup(mail_text, 'lxml')
    button = soup.find('a', href=True, text='Перейти к обращению')
    # (button['href']
    # https://sd.irb.rest/record/itsm_incident/171068457402143677
    url_path = urlparse(button['href']).path.split('/')
    url_sub_path = f'{url_path[-2]}/{url_path[-1]}'
    logger.debug('url_sub_path: %s', url_sub_path)
    simpleone_client = SimpleOneClient()
    await simpleone_client.get_token()
    task_info = await simpleone_client.get_task_info(url_sub_path)
    if task_info['sla_term']:
        exp_sla = convert_str_datetime(task_info['sla_term'], simpleone=True)
    fact_start = convert_str_datetime(
        task_info['sys_created_at'],
        simpleone=True,
    )
    task = ParsedSimpleOneTask(
        assignment_group_link=task_info['assignment_group']['link'],
        company_link=task_info['company']['link'],
        description=task_info['description'],
        number=task_info['number'],
        fact_start=fact_start,
        service_link=task_info['service']['link'],
        subject=task_info['subject'],
        sys_id=task_info['sys_id'],
        caller_department_link=task_info['caller_department']['link'],
        contact_information=task_info['contact_information'],
        sla=task_info['max_processing_duration'],
        api_path=url_sub_path,
        exp_sla=exp_sla,
        request_type_link=task_info['request_type']['link'],
    )
    task = await get_ext_task_info(task, simpleone_client)
    logger.info('Информация по задаче %s получена', task.number)
    return task


async def get_ext_task_info(
        task: ParsedSimpleOneTask,
        api_client: SimpleOneClient,
) -> ParsedSimpleOneTask:

    task.service = await utils.get_simpleone_service_name_by_url(
        task.service_link,
        api_client,
    )
    task.company = await utils.get_simpleone_company_name_by_url(
        task.company_link,
        api_client,
    )
    task.request_type = await utils.get_simpleone_request_type_name_by_url(
        task.request_type_link,
        api_client,
    )
    assignment_group = await utils.get_simpleone_assignment_group_name_by_url(
        task.assignment_group_link,
        api_client,
    )
    task.assignment_group = assignment_group
    depart_name, depart_code = await utils.get_simpleone_depart_info_by_url(
        task.caller_department_link,
        api_client,
    )
    task.caller_department = depart_name
    task.restaurant = await utils.get_restaurant_by_ext_code(depart_code)
    return task


def convert_str_datetime(
        date_time_str: str,
        simpleone: bool = False,
) -> datetime:
    datetime_format = '%d.%m.%Y %H:%M:%S'
    if simpleone:
        datetime_format = '%Y-%m-%d %H:%M:%S'
    converted_date_time = datetime.strptime(date_time_str, datetime_format)
    return timezone.make_aware(converted_date_time, is_dst=True)


async def save_parsed_task_in_db(task: ParsedGSDTask | ParsedSimpleOneTask):
    logger.info('Сохраняю задачу в БД')
    try:
        if isinstance(task, ParsedGSDTask):
            logger.info('Задача из GSD')
            await GSDTask.objects.aupdate_or_create(
                number=task.number,
                defaults=asdict(task),
            )
        if isinstance(task, ParsedSimpleOneTask):
            logger.info('Задача из SimpleOne')
            await SimpleOneTask.objects.aupdate_or_create(
                number=task.number,
                defaults=asdict(task),
            )
    except IntegrityError:
        logger.warning('Не смог сохранить задачу %s', task.number)
