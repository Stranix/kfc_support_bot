import re
import email
import imaplib
import asyncio
import logging

from datetime import datetime

import aiogram.utils.markdown as md

from aiogram import Bot
from aiogram import types

from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand

from src.models import Task
from src.models import Restaurant

logger = logging.getLogger('mail_service')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.DEBUG)
        asyncio.run(fetch_mail())


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
                applicant=task.get('applicant'),
                defaults=task,
            )
            if created:
                if task_db.service == 'Digital Kiosk':
                    if task_db.title == 'Киоск ошибка':
                        await send_message_to_tg_group(
                            378630510,
                            prepare_message_for_tg(task_db),
                        )
        except (IndexError, ValueError):
            logger.error('Ошибка при обработке сообщения')
            logger.debug('Ошибочное сообщение: %s', mail)


def prepare_message_for_tg(task: Task) -> str:
    logger.debug('Подготовка сообщения для tg')
    time_formatted_mask = '%d-%m-%Y- %H:%M:%s'
    start_at = task.start_at.strftime(time_formatted_mask)
    expired_at = task.expired_at.strftime(time_formatted_mask)
    message = md.text(
        '⁉ Зафиксировано обращение:\n\n',
        'Услуга: ' + md.hcode(task.service),
        '\nТип обращения: ' + md.hcode(task.title),
        '\nЗаявитель: ' + md.hcode(task.applicant),
        '\nДата регистрации: ' + md.hcode(start_at),
        '\nСрок обработки: ' + md.hcode(expired_at),
    )
    logger.info('Успех')
    return message


async def send_message_to_tg_group(group_id: int, message: str):
    logger.info('Отправка сообщению ботом из менеджмент команды')
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    await bot.send_message(group_id, message)
    logger.info('Сообщение отправлено')


@sync_to_async
def get_restaurant_by_applicant(applicant: str) -> Restaurant:
    logger.info('Пробую найти ресторан в бд по заявителю')
    logger.debug('applicant: %s', applicant)
    restaurant = Restaurant.objects.filter(
        name__icontains=applicant,
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
