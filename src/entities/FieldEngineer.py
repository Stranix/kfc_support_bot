import logging

from src.models import SDTask
from src.models import Dispatcher
from src.entities.User import User

logger = logging.getLogger('support_bot')


class FieldEngineer(User):

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

    async def create_sd_task_to_close(
            self,
            number: str,
            documents: dict,
    ) -> SDTask:
        """Создание задачи для закрытия выездной задачи во внешней системе"""
        logger.info(
            'Формирования заявки на закрытие задачи %s во внешней системе',
            number,
        )
        sd_task = await self.create_sd_task(
            f'Закрыть заявку {number}',
            'DISPATCHER',
            'Закрытие заявки во внешней системе',
            is_close_task_command=True,
            tg_documents=documents,
        )
        return sd_task

    async def create_sd_task_to_help(
            self,
            number: str,
            support_group: str,
            description: str,
            legal: str = '',
    ) -> SDTask:
        """Создание задачи для помощи выездному инженеру"""
        logger.info(
            'Создание задачи для помощи выездному инженеру по задаче %s',
            number,
        )
        if legal == 'irb':
            legal = 'IRB'
        if legal == 'am':
            legal = 'Unirest'
        sd_task = await self.create_sd_task(
            f'Помощь по заявке {number}',
            support_group,
            description,
            legal=legal,
        )
        return sd_task

    async def create_task_closing_from_dispatcher(
            self,
            task: Dispatcher,
            description: str,
            documents: dict,
    ) -> SDTask:
        """Создание задачи для закрытия на основе отбивки в чате"""
        logger.info(
            'Диспетчер: %s Закрытие заявки внешней системы',
            task.dispatcher_number,
        )
        outside_number = task.gsd_numbers
        if task.simpleone_number:
            outside_number = task.simpleone_number
        sd_task = await self.create_sd_task(
            f'Закрыть заявку {outside_number}',
            'DISPATCHER',
            description,
            is_close_task_command=True,
            tg_documents=documents,
        )
        return sd_task
