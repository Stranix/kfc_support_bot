import logging

from django.utils import timezone

from src.models import SDTask
from src.entities.User import User

logger = logging.getLogger('support_bot')


class SupportEngineer(User):

    @staticmethod
    async def close_sd_task(task_id: int, task_data: dict):
        try:
            sd_task = await SDTask.objects.aget(id=task_id)
            logger.debug('task_data: %s')
            for field, value in task_data.items():
                setattr(sd_task, field, value)
            await sd_task.asave()
        except SDTask.DoesNotExist:
            logger.error('Не нашел задачу %s в базе', task_id)

    @staticmethod
    async def close_sd_task_as_additional_work(task_id: int):
        """Закрытие внутренней задачи как доп работы"""
        update = {
            'status': 'COMPLETED',
            'closing_comment': 'Передана на группу по доп работам/ремонтам',
            'finish_at': timezone.now(),
        }
        await SupportEngineer.close_sd_task(task_id, task_data=update)
