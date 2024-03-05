import logging

from django.utils import timezone

from src.models import SDTask, WorkShift
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

    async def start_work_shift(self) -> WorkShift:
        shift = await WorkShift.objects.acreate(
            new_employee=self.user,
            shift_start_at=timezone.now(),
        )
        return shift

    @property
    async def is_active_shift(self) -> bool:
        logger.info('Проверяем есть ли у пользователя не завершенные смены')
        try:
            await self.user.new_work_shifts.aget(
                shift_start_at__isnull=False,
                shift_end_at__isnull=True,
            )
            logger.info('У пользователя есть активная смена')
            return True
        except WorkShift.DoesNotExist:
            logger.warning('У пользователя нет активной смены')
            return False

    @property
    async def is_middle_engineer(self) -> bool:
        logger.info('Проверяем является ли инженер старшим')
        return await self.user.groups.filter(
            name__contains='Старшие инженеры',
        ).afirst()

    @property
    async def group_id(self) -> int:
        logger.info('Получаем id основной группы сотрудника')
        groups = self.user.groups
        main_group = await groups.filter(name__icontains='инженер').afirst()
        return main_group.id
