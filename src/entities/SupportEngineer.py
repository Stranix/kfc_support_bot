import logging

from django.db.models import Q
from django.utils import timezone

from src.exceptions import BreakShiftError
from src.models import SDTask, WorkShift, BreakShift
from src.entities.User import User

logger = logging.getLogger('support_bot')


class SupportEngineer(User):

    @staticmethod
    async def update_sd_task(task_id: int, task_data: dict):
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
        await SupportEngineer.update_sd_task(task_id, task_data=update)

    async def start_work_shift(self) -> WorkShift:
        shift = await WorkShift.objects.acreate(
            new_employee=self.user,
            shift_start_at=timezone.now(),
        )
        return shift

    async def start_break(self):
        work_shift = await self.current_work_shift
        if not work_shift.is_works:
            raise BreakShiftError('Есть не завершенный перерыв')
        await work_shift.break_shift.acreate(
            new_employee=self.user,
        )
        work_shift.is_works = False
        await work_shift.asave()

    async def stop_break(self):
        logger.info('Фиксируем завершение перерыва в БД')
        work_shift, active_break = await self.current_active_break
        active_break.end_break_at = timezone.now()
        active_break.is_active = False
        work_shift.is_works = True
        await active_break.asave()
        await work_shift.asave()
        logger.info('Успех')

    @property
    async def current_active_break(self) -> tuple[WorkShift, BreakShift]:
        work_shift = await self.current_work_shift
        active_break = await work_shift.break_shift.select_related(
            'new_employee'
        ).aget(is_active=True)
        return work_shift, active_break

    @property
    async def current_work_shift(self) -> WorkShift:
        work_shift = await self.user.new_work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
        )
        return work_shift

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
        logger.debug('Группы инженера: %s', self.user.groups.all())
        return await self.user.groups.filter(name='Старшие инженеры').aexists()

    @property
    async def group_id(self) -> int:
        logger.info('Получаем id основной группы сотрудника')
        groups = self.user.groups
        main_group = await groups.filter(
            Q(name__icontains='инженер') | Q(name='Диспетчеры')
        ).afirst()
        return main_group.id
