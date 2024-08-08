import logging

from src.models import SDTask
from src.entities.User import User

logger = logging.getLogger('support_bot')


class SberEngineer(User):

    async def create_sd_task(
            self,
            title: str,
            support_group: str,
            description: str,
            *,
            legal: str = '',
            is_close_task_command: bool = False,
            tg_documents: dict = None,
            is_automatic: bool = False
    ) -> SDTask:
        """Создание внутренней задачи поддержки выездным инженером"""
        task = await SDTask.objects.acreate(
            new_applicant=self.user,
            title=title,
            support_group=support_group.upper(),
            description=description,
            is_close_task_command=is_close_task_command,
            tg_docs=tg_documents,
            is_automatic=is_automatic,
            legal=legal,
        )
        task.number = f'SD-{task.id}'
        await task.asave()
        logger.info('Задача зафиксирована в БД. Номер: %s', task.number)
        return task

    async def create_sd_task_to_help(
            self,
            rest_code: str,
            description: str,
    ) -> SDTask:
        """Создание задачи для помощи инженеру Sber"""
        logger.info('Создание задачи для помощи инженеру Sber')
        description += f'<br/>Ресторан: {rest_code}'
        sd_task = await self.create_sd_task(
            'Помощь инженеру сбер',
            'ENGINEER',
            description,
        )
        return sd_task
