import json
import logging

logger = logging.getLogger(__name__)


def configure_logging():
    """Загружаем конфигурация логирования из json. """
    try:
        with open('config/logging_config.json', 'r', encoding='utf-8') as file:
            logging.config.dictConfig(json.load(file))
    except FileNotFoundError:
        logger.warning(
            'Для настройки логирования нужен logging_config.json '
            'в корне проекта'
        )
