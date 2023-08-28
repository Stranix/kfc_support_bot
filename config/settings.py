import logging
import sys

from pydantic_core import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

logger = logging.getLogger('support_bot')


class Settings(BaseSettings):
    log_level: str = logging.INFO

    tg_bot_token: str = ''

    rk_xml_api: str = ''
    rk_user: str = ''
    rk_password: str = ''

    mail_login: str = ''
    mail_password: str = ''
    mail_imap_server: str = ''

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )


try:
    settings = Settings()
except ValidationError as exc:
    logger.critical('Заданы не все обязательные настройки')
    logger.critical(exc.json())
    sys.exit()
