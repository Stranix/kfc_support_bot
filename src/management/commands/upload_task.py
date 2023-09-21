import email
import imaplib
import logging
import re

from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from src.models import Task

logger = logging.getLogger('mail_service')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.DEBUG)
        unread_mail = check_unread_mail()
        for mail in unread_mail:
            if mail.find('назначено группе') == -1:
                logger.warning('Не подходящее сообщение. Пропускаю.')
                logger.debug('Текст сообщения: %s', mail)
            task = parse_gsd_mail(mail)
            Task.objects.create(**task)


def parse_gsd_mail(mail_text: str) -> dict:
    message = mail_text.split('Описание:')
    main_info = list(filter(None, message[0].split('\r\n')))

    expired_at = datetime.strptime(
        main_info[10].split(': ')[1],
        '%d.%m.%Y %H:%M:%S',
    )
    tz = timezone.get_current_timezone()
    tz_expired_at = timezone.make_aware(expired_at, tz, True)

    task = {
        'applicant': main_info[2].split(': ')[1],
        'number': re.search(r'SC-(\d{7})+', main_info[0]).group(),
        'expired_at': tz_expired_at,
        'priority': main_info[9].split(': ')[1],
        'service': main_info[11].split(': ')[1],
        'title': main_info[12].split(': ')[1],
        'description': mail_text,
        'gsd_group': re.search(r'«([\s\S]+?)»', main_info[0]).group(),
    }
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
    logger.debug('search_data: %s', search_data)
    msgs = get_emails(search_data, mail_conn)
    logger.info(f'Нашел {len(msgs)} писем')
    for msg in msgs:
        msg_byte = get_body(email.message_from_bytes(msg[0][1]))
        message = msg_byte.decode('UTF-8').split(
            '---------------------------------------------------')
        message_list.append(message[0] + message[1])
    logger.debug('Полученные сообщения: %s', message_list)
    logger.info(f'Закрытие соединения с ящиком: {mail_conn.logout()}')
    return message_list
