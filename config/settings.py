import os
import sys
import json
import logging

from pathlib import Path

from pydantic_core import ValidationError
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

logger = logging.getLogger('support_bot')


class Settings(BaseSettings):
    log_level: int = logging.INFO

    tg_bot_token: str = ''

    rk_xml_api: str = ''
    rk_user: str = ''
    rk_password: str = ''

    mail_login: str = ''
    mail_password: str = ''
    mail_imap_server: str = ''

    transits: dict = {}

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )


try:
    settings = Settings()
    tr_settings_json = os.path.join('./', 'config/tr_settings.json')
    settings.transits = json.loads(Path(tr_settings_json).read_text('UTF-8'))
except FileNotFoundError:
    logger.critical('В папке config отсутствует файл tr_settings.json')
    sys.exit()
except ValidationError as exc:
    logger.critical('Заданы не все обязательные настройки')
    logger.critical(exc.json())
    sys.exit()
