import json
import re
import email
import imaplib
import asyncio
import logging

from datetime import datetime

import aiogram.utils.markdown as md

from aiogram import Bot
from aiogram import types
from aiogram.types import InlineKeyboardMarkup

from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.utils.dateformat import format

from src.models import Task
from src.models import Restaurant
from src.bot.keyboards import get_task_keyboard
from src.utils import configure_logging

logger = logging.getLogger('mail_service')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            asyncio.run(fetch_mail())
        except Exception as err:
            logger.exception(err)


async def fetch_mail():
    unread_mail = check_unread_mail()
    for mail in unread_mail:
        if mail.find('назначено группе') == -1:
            logger.warning('Не подходящее сообщение. Пропускаю.')
            logger.debug('Текст сообщения: %s', mail)
            continue
        try:
            task = parse_gsd_mail(mail)
            restaurant = await get_restaurant_by_applicant(
                task.get('applicant')
            )
            if restaurant:
                task['restaurant'] = restaurant
            task_db, created = await Task.objects.aupdate_or_create(
                number=task.get('number'),
                defaults=task,
            )
            if not created:
                logger.info('Задача уже существует в базе')

            if created and await is_critical_task(task_db):
                message, keyboard = await prepare_message_for_tg(task_db)
                await send_message_to_tg_group(
                    -1001328841443,
                    message,
                    keyboard,
                )
        except (IndexError, ValueError):
            logger.warning('Ошибка при обработке сообщения')
            logger.debug('Ошибочное сообщение: %s', mail)


async def is_critical_task(task: Task) -> bool:
    logger.info('Проверяю задачу на критичность')
    critical_service = ('Digital Kiosk', 'Касса Digital')
    critical_title = ('Киоск ошибка', 'Проблемы в работе')
    logger.debug('task.service: %s', task.service)
    logger.debug('task.title: %s', task.title)
    logger.debug('Критичный сервис: %s', task.service in critical_service)
    logger.debug('Критичный Тип: %s', task.title in critical_title)
    if task.service in critical_service:
        if task.title in critical_title:
            logger.info('Задача является критичной')
            return True
    logger.info('Задача не является критичной')
    return False


async def prepare_message_for_tg(
        task: Task
) -> tuple[str, InlineKeyboardMarkup]:
    logger.info('Подготовка сообщения для tg')
    time_formatted_mask = 'd-m-Y H:i:s'
    start_at = format(task.start_at, time_formatted_mask)
    expired_at = format(task.expired_at, time_formatted_mask)
    message = md.text(
        '⁉ Зафиксировано обращение:\n\n',
        md.hbold(task.number),
        '\n\nУслуга: ' + md.hcode(task.service),
        '\nТип обращения: ' + md.hcode(task.title),
        '\nЗаявитель: ' + md.hcode(task.applicant),
        '\nНа группе: ' + md.hcode(task.gsd_group),
        '\nДата регистрации: ' + md.hcode(start_at),
        '\nСрок обработки: ' + md.hcode(expired_at),
    )
    keyboard = await get_task_keyboard(task.id)
    logger.info('Успех')
    return message, keyboard


async def send_message_to_tg_group(
        group_id: int,
        message: str,
        keyboard: InlineKeyboardMarkup,
):
    logger.info('Отправка сообщению ботом из менеджмент команды')
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    await bot.send_message(group_id, message, reply_markup=keyboard)
    await bot.close()
    logger.info('Сообщение отправлено')


@sync_to_async
def get_restaurant_by_applicant(applicant: str) -> Restaurant:
    logger.info('Пробую найти ресторан в бд по заявителю')
    logger.debug('applicant: %s', applicant)
    restaurant = Restaurant.objects.filter(
        ext_name__icontains=applicant.split()[1],
    )
    if not restaurant:
        logger.info('Не нашел для %s подходящего ресторана в бд', applicant)

    logger.debug('restaurant %s', restaurant)
    return restaurant.first()


def parse_gsd_mail(mail_text: str) -> dict:
    logger.info('Разбираем сообщение')
    message = mail_text.split('Описание:')
    main_info = list(filter(None, message[0].split('\r\n')))

    start_at = datetime.strptime(
        main_info[8].split(': ')[1],
        '%d.%m.%Y %H:%M:%S',
    )
    expired_at = datetime.strptime(
        main_info[10].split(': ')[1],
        '%d.%m.%Y %H:%M:%S',
    )
    tz = timezone.get_current_timezone()
    tz_expired_at = timezone.make_aware(expired_at, tz, True)
    tz_start_at = timezone.make_aware(start_at, tz, True)

    task = {
        'applicant': main_info[2].split(': ')[1],
        'number': re.search(r'SC-(\d{7})+', main_info[0]).group(),
        'start_at': tz_start_at,
        'expired_at': tz_expired_at,
        'priority': main_info[9].split(': ')[1],
        'service': main_info[11].split(': ')[1],
        'title': main_info[12].split(': ')[1],
        'description': mail_text,
        'gsd_group': re.search(r'«([\s\S]+?)»', main_info[0]).group(),
    }
    logger.info('Информация по задаче собрана')
    logger.debug('task: %s', task)
    return task


def get_conn():
    try:
        login = settings.MAIL_LOGIN
        password = settings.MAIL_PASSWORD
        imap_server = settings.MAIL_IMAP_SERVER
        logger.info('Подключаюсь к почте')
        conn = imaplib.IMAP4_SSL(imap_server, port=993)
        conn.login(login, password)
        return conn
    except imaplib.IMAP4.error as err:
        logger.error('Ошибка соединения с почтой: %s', err)


def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)


def get_emails(result_bytes, conn):
    msgs = []
    for num in result_bytes[0].split():
        status, data = conn.uid('fetch', num, '(RFC822)')
        msgs.append(data)
    return msgs


def check_unread_mail():
    message_list = []
    mail_conn = get_conn()
    logger.info('Перехожу в папку GSD|Disp')
    mail_conn.select("GSD")
    logger.info('Получаю непрочитанные письма')
    status, search_data = mail_conn.uid('search', 'UNSEEN')
    logger.debug('status: %s', status)
    msgs = get_emails(search_data, mail_conn)
    logger.info(f'Нашел {len(msgs)} писем')
    for msg in msgs:
        msg_body = get_body(
            email.message_from_bytes(msg[0][1])
        ).decode('UTF-8')
        message = msg_body.split(
            '---------------------------------------------------',
        )
        try:
            message_list.append(message[0] + message[1])
        except IndexError:
            message_list.append(message[0])
    logger.debug('Количество полученных сообщений: %s', len(message_list))
    logger.info(f'Закрытие соединения с ящиком: {mail_conn.logout()}')
    return message_list
