import email
import imaplib
import logging

from dataclasses import asdict

from src.parsers import parse_gsd_mail, parse_simpleone_mail
from src.parsers import save_parsed_task_in_db

logger = logging.getLogger('mail_client')


class MailClient:
    connection = None

    def mail_connect(
            self,
            login: str,
            password: str,
            imap_server: str,
    ) -> None:
        try:
            logger.info('Подключаюсь к почте')
            conn = imaplib.IMAP4_SSL(imap_server, port=993)
            conn.login(login, password)
            self.connection = conn
        except imaplib.IMAP4.error as err:
            logger.error('Ошибка соединения с почтой: %s', err)

    def close_connection(self):
        logger.info('Закрытие соединения с ящиком')
        self.connection.logout()
        self.connection = None
        logger.info('Выполнено')

    def check_unread_mail(self, imap_folder: str) -> list:
        message_list = []
        logger.info('Перехожу в папку %s', imap_folder)
        self.connection.select(imap_folder)
        logger.info('Получаю непрочитанные письма')
        status, search_data = self.connection.uid('search', 'UNSEEN')
        logger.debug('status: %s', status)
        msgs = self._get_emails(search_data)
        logger.info(f'Нашел {len(msgs)} писем')
        for msg in msgs:
            msg_body = self._get_body(
                email.message_from_bytes(msg[0][1])
            ).decode('UTF-8')
            message_list.append(msg_body)
        logger.debug('Количество полученных сообщений: %s', len(message_list))
        return message_list

    def _get_emails(self, result_bytes):
        msgs = []
        for num in result_bytes[0].split():
            status, data = self.connection.uid('fetch', num, '(RFC822)')
            msgs.append(data)
        return msgs

    def _get_body(self, msg):
        if msg.is_multipart():
            return self._get_body(msg.get_payload(0))
        else:
            return msg.get_payload(None, True)

    async def fetch_gsd_mail(self, *, save_in_db: bool = True):
        unread_mail = self.check_unread_mail('GSD')
        for mail in unread_mail:
            if mail.find('назначено группе') == -1:
                logger.warning('Не подходящее сообщение. Пропускаю.')
                logger.debug('Текст сообщения: %s', mail)
                continue
            task = await parse_gsd_mail(mail)
            if not save_in_db:
                logger.warning('Задача не сохраняется в БД')
                logger.info('Информация по задаче: %s', asdict(task))
                continue
            await save_parsed_task_in_db(task)

    async def fetch_simpleone_mail(self, *, save_in_db: bool = True):
        unread_mail = self.check_unread_mail('IRB_SD')
        for mail in unread_mail:
            try:
                task = await parse_simpleone_mail(mail)
                if not save_in_db:
                    logger.warning('Задача не сохраняется в БД')
                    logger.info('Информация по задаче: %s', asdict(task))
                    continue
                await save_parsed_task_in_db(task)
            except TypeError:
                pass
