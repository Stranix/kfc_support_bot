import logging
import aiohttp

from urllib.parse import urljoin

from aiohttp.web_exceptions import HTTPUnauthorized

from django.conf import settings
from django.utils import timezone

from src.models import SimpleOneCred

logger = logging.getLogger('simpleone_client')
if settings.DEBUG:
    logger.setLevel(logging.DEBUG)


class SimpleOneClient:
    __token: str = ''

    def __init__(self):
        self.api = settings.SIMPLEONE_API
        self.user = settings.SIMPLEONE_USER
        self.__password = settings.SIMPLEONE_PASSWORD
        self.user_agent = 'Chrome/122.0.0.0'

    async def send_get_request(self, url: str, params: dict | None = None):
        headers = {
            'User-Agent': self.user_agent,
            'Authorization': f'Bearer {self.__token}',
            'Content-Type': 'application/json',
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url,
                    headers=headers,
                    params=params
            ) as response:
                header_content_type = response.headers.get('Content-Type')
                logger.debug('response: %s', response.status)
                logger.debug('content-type: %s', header_content_type)
                if header_content_type.split(';')[0] == 'text/html':
                    logger.error('Что то пошло не так. Не верный тип ответа')
                    return
                if response.status == 401:
                    raise HTTPUnauthorized
                logger.debug('response.json(): %s', await response.json())
                return await response.json()

    # TODO не нравится кусок, изменить
    async def get_token(self, force: bool = False):
        if not force:
            await self._token_from_db()
            if self.__token:
                logger.info('Использую токен полученный ранее')
                return
        await self._token_from_api()

    async def _token_from_db(self):
        logger.info('Попытка получить токен из базы')
        try:
            creds = await SimpleOneCred.objects.filter(
                login=self.user,
            ).alatest('start_at')
            if creds.expired_at < timezone.now():
                logger.debug('now: %s', timezone.now())
                logger.debug('expired_at: %s', creds.expired_at)
                self.__token = ''
                logger.warning('Срок действия токена истек')
                return
            self.__token = creds.token
            logger.info('Токен получен')
        except SimpleOneCred.DoesNotExist:
            logger.info('Нет доступного токена')
            self.__token = ''

    async def _token_from_api(self):
        logger.info('Получаю новый токен')
        url = urljoin(self.api, 'auth/login')
        data = {
            'username': self.user,
            'password': self.__password,
            'language': 'ru',
        }
        logger.debug('url: %s', url)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url,
                    data=data,
            ) as response:
                header_content_type = response.headers.get('Content-Type')
                logger.debug('response: %s', response.status)
                logger.debug('content-type: %s', header_content_type)
                response.headers.get('Content-Type')
                token = await response.json()
                logger.debug('token: %s', token['data']['auth_key'])
                self.__token = token['data']['auth_key']
        logger.debug('Записываю токен в базу')
        cred = await SimpleOneCred.objects.acreate(
            login=self.user,
            token=self.__token,
        )
        logger.debug('Токен создан с id: %s', cred.id)
        logger.info('Токен получен')

    async def get_task_info(self, url_path: str):
        url = urljoin(self.api, f'table/{url_path}')
        logger.debug('url: %s', url)
        try:
            task_info = await self.send_get_request(url)
        except HTTPUnauthorized:
            logger.info('Токен не подходит. Обновляю')
            await self.get_token(force=True)
            task_info = await self.send_get_request(url)
            logger.debug('task_info: %s', task_info)
        return task_info['data'][0]

    async def get_caller_department_info(self, url: str) -> tuple:
        url = url.replace('http', 'https')
        department = await self.send_get_request(url)
        department_name = department['data'][0]['name']
        department_ext_code = department['data'][0]['facts']
        return department_name, department_ext_code

    async def get_service_name(self, url: str) -> str:
        url = url.replace('http', 'https')
        service = await self.send_get_request(url)
        return service['data'][0]['name']

    async def get_company_name(self, url: str) -> str:
        url = url.replace('http', 'https')
        company = await self.send_get_request(url)
        return company['data'][0]['name']

    async def get_assignment_group_name(self, url: str) -> str:
        url = url.replace('http', 'https')
        assignment_group = await self.send_get_request(url)
        return assignment_group['data'][0]['name']

    async def get_request_type(self, url: str) -> str:
        url = url.replace('http', 'https')
        assignment_group = await self.send_get_request(url)
        return assignment_group['data'][0]['title']
