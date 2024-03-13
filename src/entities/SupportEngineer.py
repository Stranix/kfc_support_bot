import logging

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.utils import timezone

from src import exceptions
from src.entities.User import User
from src.entities.Service import Service
from src.models import SDTask
from src.models import CustomUser
from src.models import WorkShift
from src.models import BreakShift

logger = logging.getLogger('support_bot')


class SupportEngineer(User):

    @staticmethod
    async def update_sd_task(task_id: int, task_data: dict) -> SDTask:
        try:
            sd_task = await SDTask.objects.select_related(
                'new_performer',
                'new_applicant',
            ).aget(id=task_id)
            logger.debug('task_data: %s', task_data)
            for field, value in task_data.items():
                setattr(sd_task, field, value)
            await sd_task.asave()
            return sd_task
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
        logger.debug('Фиксируем начало смены в БД')
        shift = await WorkShift.objects.acreate(
            new_employee=self.user,
            shift_start_at=timezone.now(),
        )
        return shift

    async def end_work_shift(self) -> WorkShift:
        logger.debug('Фиксируем завершение смены в БД')
        shift = await self.user.new_work_shifts.aget(
            shift_start_at__isnull=False,
            shift_end_at__isnull=True,
        )
        shift.shift_end_at = timezone.now()
        shift.is_works = False
        await shift.asave()
        return shift

    async def start_break(self):
        work_shift = await self.current_work_shift
        if not work_shift.is_works:
            raise exceptions.BreakShiftError('Есть не завершенный перерыв')
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

    async def start_task(self, task_id: str) -> SDTask:
        """Взять внутреннюю задачу в работу"""
        logger.info('Берем задачу в работу')
        task: SDTask = await SDTask.objects.by_id(task_id)
        if task.new_performer:
            raise exceptions.TaskAssignedError(
                f'Задача {task.number} назначена на '
                f'сотрудника {task.new_performer.name}'
            )
        task.new_performer = self.user
        task.status = 'IN_WORK'
        await task.asave()
        return task

    @staticmethod
    async def assigned_task(
            task_id: str,
            selected_engineer: CustomUser,
    ) -> SDTask:
        task = await SDTask.objects.by_id(task_id)
        if task.new_performer:
            raise exceptions.TaskAssignedError(
                f'Задача {task.number} назначена на '
                f'сотрудника {task.new_performer.name}'
            )
        logger.debug('selected_engineer: %s', selected_engineer)
        task.new_performer = selected_engineer
        task.status = 'IN_WORK'
        await task.asave()
        return task

    async def get_available_to_assign(self):
        """Получаем сотрудников доступных для назначения"""
        engineer_group = await self.user.groups.afirst()
        logger.debug('Текущая группа: %s', engineer_group)
        if engineer_group.name == 'Старшие инженеры':
            groups_name = ('Инженеры',)
            return await CustomUser.objects.available_to_assign_by_groups_name(
                groups_name,
            )
        if engineer_group.name == 'Ведущие инженеры':
            groups_name = ('Инженеры', 'Старшие инженеры', 'Диспетчеры')
            return await CustomUser.objects.available_to_assign_by_groups_name(
                groups_name,
            )
        if await self.user.managers.afirst() == 'Диспетчеры':
            groups_name = ('Диспетчеры', )
            return await CustomUser.objects.available_to_assign_for_disp(
                groups_name,
            )
        raise exceptions.NotAvailableToAssignError(
            'Нет инженеров на смене на которых вы можете назначить задачу'
        )

    async def get_task_in_work(self) -> list[SDTask]:
        """Получаем все задачи в работе у сотрудника"""
        logger.info('Получение всех не назначенных задач')
        tasks = await sync_to_async(list)(
            self.user.new_sd_tasks.prefetch_related(
                'new_performer',
                'new_applicant',
            ).filter(status='IN_WORK')
        )
        if not tasks:
            logger.info('У сотрудника %s нет задач в работе', self.user.name)
            raise exceptions.TaskNotFoundError('Нет задач в работе')
        logger.debug('Список найденных новых задач: %s', tasks)
        logger.info('Задачи найдены')
        return tasks

    async def get_task_number_in_work(self) -> list[SDTask]:
        """Получаем все номера задач в работе у сотрудника"""
        tasks = await sync_to_async(list)(
            self.user.new_sd_tasks.filter(status='IN_WORK')
                                  .values_list('number', flat=True)
        )
        if not tasks:
            raise exceptions.TaskNotFoundError('Нет задач в работе')
        return tasks

    async def dispatcher_close_task(
            self,
            task_id: int,
            task_number: str,
            approved_sub_tasks: list,
            tg_docs: dict,
            closing_comment: str,
    ) -> SDTask:
        logger.info('Закрытие задачи диспетчером')
        files_save_info = await Service.save_doc_from_tg_to_disk(
            task_number,
            tg_docs,
        )
        if files_save_info:
            files_save_info = str(files_save_info).strip('[]') + ','

        if approved_sub_tasks:
            approved_sub_tasks = ','.join(approved_sub_tasks)

        task_update = {
            'status': 'COMPLETED',
            'closing_comment': closing_comment,
            'sub_task_number': approved_sub_tasks,
            'doc_path': files_save_info,
            'finish_at': timezone.now()
        }
        task = await self.update_sd_task(task_id, task_update)
        logger.info('Успех. Задача %s закрыта', task.number)
        return task

    async def engineer_close_task(self, task_id: int) -> SDTask:
        logger.info('Закрытие задачи инженером')
        task_update = {
            'status': 'COMPLETED',
            'finish_at': timezone.now()
        }
        task = await self.update_sd_task(task_id, task_update)
        logger.info('Задача %s закрыта', task.number)
        return task
