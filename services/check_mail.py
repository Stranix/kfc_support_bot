import email
import imaplib
import logging

import env_config as config


def get_conn():
    login = config.MAIL_LOGIN
    password = config.MAIL_PASSWORD
    logging.info('Подключаюсь к почте')
    conn = imaplib.IMAP4_SSL('imap.yandex.ru', port=993)
    conn.login(login, password)
    return conn


def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)


def get_emails(result_bytes, conn):
    msgs = []
    for num in result_bytes[0].split():
        status, data = conn.fetch(num, '(RFC822)')
        msgs.append(data)
    return msgs


def find_ticket(ticket_number):
    result = False
    logging.info(f'Ищу письмо с заявкой: {ticket_number}')
    mail_conn = get_conn()
    mail_conn.select("GSD|Disp")
    status, search_data = mail_conn.uid('search', f'(SUBJECT "{ticket_number}")')
    logging.info(f'Status: {status}')
    msgs = get_emails(search_data, mail_conn)
    logging.info(f'Нашел {len(msgs)} письмо')
    if len(msgs) > 0:
        for msg in msgs:
            msg_byte = get_body(email.message_from_bytes(msg[0][1]))
            message = msg_byte.decode('UTF-8').split('---------------------------------------------------')
            result = message[1]
    logging.info(f'Закрытие соединения с ящиком: {mail_conn.logout()}')
    return result


def check_unread_mail():
    message_list = []
    mail_conn = get_conn()
    logging.info('Перехожу в папку GSD|Disp')
    mail_conn.select("GSD|Disp")
    logging.info('Получаю непрочитанные письма')
    status, search_data = mail_conn.uid('search', 'UNSEEN')
    logging.debug(f'{search_data}')
    msgs = get_emails(search_data, mail_conn)
    logging.info(f'Нашел {len(msgs)} писем')
    if len(msgs) > 0:
        for msg in msgs:
            msg_byte = get_body(email.message_from_bytes(msg[0][1]))
            message = msg_byte.decode('UTF-8').split('---------------------------------------------------')
            message_list.append(message[0] + message[1])

    logging.info('Закрываю соединение с почтой')
    logging.info(f'Закрытие соединения с ящиком: {mail_conn.logout()}')
    return message_list
