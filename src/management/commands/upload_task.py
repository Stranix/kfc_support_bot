# Подключение к почте
# Чтение писем
# Запись в бд
# Запуск раз в 15 минут задачи на скан почты

import email
import imaplib
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger('mail_service')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.DEBUG)
        unread_mail = check_unread_mail()
        one_message = unread_mail[0].split('Описание:')

        task_main_info = filter(None, one_message[0].split('\r\n'))
        task_descriptions = one_message[1]

        for line in task_main_info:
            print(line)


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
