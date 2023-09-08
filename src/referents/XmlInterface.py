import logging
import requests
import urllib3
import xml.etree.ElementTree as ET

from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning

from src.referents.commands import system_info

logger = logging.getLogger('xml_interface')


class XmlInterface:
    """Класс для работы с xml интерфейсом Кипера"""
    def __init__(
            self,
            host: str,
            port: int,
            login: str,
            password: str
    ) -> None:
        self.xml_host = host
        self.xml_port = port
        self.xml_address = f'https://{host}:{port}/rk7api/v0/xmlinterface.xml'
        self.xml_login = login
        self.xml_password = password

    def check_settings_xml_interface(self):
        """Проверка настроек интерфейса"""
        logger.info('Выполняю тестовую команду')
        interface_answer = self.send_data(
            system_info.get_system_info_xml()
        )
        logger.info('Успех')
        return system_info.parse_get_system_info(interface_answer)

    def send_data(self, xml_request: str):
        """Отправка команды на xml интерфейс"""
        logger.info('Отправляю запрос на интерфейс: %s', self.xml_address)
        urllib3.disable_warnings(InsecureRequestWarning)
        headers = {'Content-Type': 'application/xml; charset=utf-8'}
        response = requests.post(
            self.xml_address,
            data=xml_request.encode('utf-8'),
            headers=headers,
            verify=False,
            auth=HTTPBasicAuth(self.xml_login, self.xml_password)
        )
        response.raise_for_status()
        logger.info('Получен ответ от интерфейса')
        if self.is_error(response.text):
            raise requests.exceptions.HTTPError
        return response.text

    @staticmethod
    def is_error(xml: str) -> bool:
        """Проверка ответа xml интерфейса на наличие ошибки"""
        logger.info('Проверяю ответ интерфейса на ошибку')
        tree = ET.fromstring(xml)
        try:
            error_message = tree.attrib['ErrorText']
            if not error_message:
                return False
            logger.error(f'Ошибка выполнения команды: {error_message}')
            return True
        except AttributeError:
            return False
