import json
import logging

from django.core.management.base import BaseCommand

from src.models import Group
from src.models import BotCommand
from src.utils import configure_logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            configure_logging()
            file_name = 'config/support_bot_commands.json'
            with open(file_name, 'r', encoding='UTF-8') as json_file:
                bot_commands = json.load(json_file)
            upload_commands(bot_commands)
        except FileNotFoundError:
            logger.warning('Не найден файл с командами в папке config')
        except Exception as err:
            logger.exception(err)


def upload_commands(bot_commands: list):
    logger.info('Старт загрузки команд')
    groups = Group.objects.all()
    for command in bot_commands:
        name = command['command']
        description = command['description']
        privilege_groups = groups.filter(name__in=command['privilege_groups'])
        bot_command, _ = BotCommand.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
            }
        )
        bot_command.groups.add(*privilege_groups)
        bot_command.save()
    logger.info('Команды загружены')
