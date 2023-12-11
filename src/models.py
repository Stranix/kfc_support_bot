import pytz

from datetime import date
from datetime import time
from datetime import datetime

from asgiref.sync import sync_to_async

from django.db import models
from django.utils import timezone

from django.core.validators import MaxValueValidator


class EmployeeQuerySet(models.QuerySet):

    async def dispatchers_on_work(self):
        return await self.employees_on_work_by_group_name('Диспетчеры')

    async def engineers_on_work(self):
        engineers = await sync_to_async(list)(
            self.filter(
                groups__name__icontains='Инженеры',
                work_shifts__is_works=True,
            ),
        )
        return engineers

    async def employees_on_work_by_group_name(self, group_name: str):
        employees = await sync_to_async(list)(
            self.filter(
                groups__name=group_name,
                work_shifts__is_works=True,
            )
        )
        return employees


class Employee(models.Model):
    name = models.CharField('Имя', max_length=50)
    tg_id = models.PositiveBigIntegerField(
        'Telegram_id',
        db_index=True,
        unique=True,
    )
    tg_nickname = models.CharField(
        'Ник в телеге',
        max_length=50,
        blank=True,
        default='',
    )
    dispatcher_name = models.CharField(
        'Имя в диспетчере',
        max_length=50,
        blank=True,
        null=True,
    )
    groups = models.ManyToManyField(
        'Group',
        related_name='employees',
        verbose_name='Группа доступа',
        blank=True,
    )
    managers = models.ManyToManyField(
        'Employee',
        verbose_name='Менеджеры',
        blank=True,
    )
    registered_at = models.DateTimeField(
        'Дата регистрации',
        default=timezone.now,
    )
    is_active = models.BooleanField('Активен?', default=False)

    objects = EmployeeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.name


class WorkShift(models.Model):
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        verbose_name='Сотрудник',
        related_name='work_shifts',
    )
    shift_start_at = models.DateTimeField('Старт смены')
    shift_end_at = models.DateTimeField(
        'Завершение смены',
        null=True,
        blank=True,
    )
    break_shift = models.ManyToManyField(
        'BreakShift',
        related_name='work_shifts',
        verbose_name='Перерывы',
        blank=True,
    )
    is_works = models.BooleanField('Работает?', default=True)

    class Meta:
        verbose_name = 'Рабочая Смена'
        verbose_name_plural = 'Рабочие Смены'

    def __str__(self):
        return f'{self.employee.name} - {self.shift_start_at}'


class BreakShift(models.Model):
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        verbose_name='Сотрудник',
        related_name='break_shifts',
    )
    start_break_at = models.DateTimeField(
        'Старт перерыва',
        auto_now_add=True,
    )
    end_break_at = models.DateTimeField(
        'Завершение перерыва',
        null=True,
        blank=True,
    )
    is_active = models.BooleanField('Активен?', default=True)

    class Meta:
        verbose_name = 'Перерыв'
        verbose_name_plural = 'Перерывы'

    def __str__(self):
        return f'{self.employee.name} - {self.start_break_at}'


class Group(models.Model):
    name = models.CharField(
        'Имя группы',
        max_length=50,
        unique=True,
        db_index=True,
    )
    rights = models.ManyToManyField(
        'Right',
        related_name='groups',
        verbose_name='Права',
        blank=True,
    )

    class Meta:
        verbose_name = 'Группа доступа'
        verbose_name_plural = 'Группы доступа'

    def __str__(self):
        return self.name


class Right(models.Model):
    name = models.CharField('Имя права', max_length=100)

    class Meta:
        verbose_name = 'Право'
        verbose_name_plural = 'Права'

    def __str__(self):
        return self.name


class FranchiseOwner(models.Model):
    name = models.CharField('Имя франшизы', max_length=25)
    alias = models.CharField('Alias', max_length=10)

    class Meta:
        verbose_name = 'Франшиза'
        verbose_name_plural = 'Франшизы'

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField(
        'Имя ресторана',
        max_length=100,
        db_index=True,
        unique=True,
    )
    ext_name = models.CharField(
        'Расширенное имя',
        max_length=50,
        default='',
    )
    id = models.PositiveIntegerField(
        'RK ident',
        primary_key=True,
    )
    code = models.PositiveSmallIntegerField(
        'RK Код',
        unique=True,
    )
    legal_entity = models.CharField(
        'Юр лицо',
        blank=True,
        null=True,
        max_length=100,
    )
    address = models.CharField('Адрес', max_length=100)
    phone = models.CharField(
        'Номер телефона ресторана',
        max_length=150,
        db_index=True,
        null=True,
        blank=True,
    )
    server_ip = models.GenericIPAddressField(
        'IP главного сервера RK',
        null=True,
        blank=True,
    )
    franchise = models.ForeignKey(
        'FranchiseOwner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurants',
        verbose_name='Франшиза',
    )
    is_sync = models.BooleanField('Синхронизация?', default=False)

    class Meta:
        verbose_name = 'Ресторан'
        verbose_name_plural = 'Рестораны'

    def __str__(self):
        return self.name


class ServerType(models.Model):
    name = models.CharField('Тип сервера RK', max_length=50)

    class Meta:
        verbose_name = 'Тип сервера'
        verbose_name_plural = 'Типы Серверов'

    def __str__(self):
        return self.name


class Server(models.Model):
    name = models.CharField(
        'Имя сервера',
        max_length=100,
        db_index=True,
        unique=True,
    )
    id = models.PositiveIntegerField(
        'RK ident',
        primary_key=True,
    )
    ip = models.GenericIPAddressField('IP адрес', null=True, blank=True)
    tcp = models.PositiveSmallIntegerField('TCP port', default=3029)
    web_server = models.PositiveSmallIntegerField(
        'Порт веб сервера',
        default=9000,
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='servers',
    )
    server_type = models.ForeignKey(
        'ServerType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Тип сервера',
        related_name='servers',
    )
    franchise_owner = models.ForeignKey(
        'FranchiseOwner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Франшиза',
        related_name='servers',
    )
    is_sync = models.BooleanField('Синхронизация?', default=False)
    is_active = models.BooleanField('Рабочий?', default=True)

    class Meta:
        verbose_name = 'Сервер'
        verbose_name_plural = 'Сервера'

    def __str__(self):
        return self.name


class SDTaskQuerySet(models.QuerySet):

    def in_period_date(
            self,
            start_shift_date: date,
            end_shift_date: date | None = None
    ):
        start_at = datetime.combine(start_shift_date, time(), tzinfo=pytz.UTC)
        if not end_shift_date:
            end_shift_date = timezone.now().replace(
                hour=23,
                minute=59,
                second=59,
                tzinfo=pytz.UTC,
            )

        end_at = datetime.combine(
            end_shift_date,
            time(hour=23, minute=59, second=59),
            tzinfo=pytz.UTC,
        )
        return self.select_related('performer').filter(
            start_at__gte=start_at,
            start_at__lte=end_at,
        ).order_by('-id')


class GSDTask(models.Model):
    applicant = models.CharField('Заявитель', max_length=100)
    number = models.CharField(
        'Номер заявки GSD',
        unique=True,
        db_index=True,
        max_length=25,
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='gsd_tasks',
        verbose_name='Ресторан',
    )
    start_at = models.DateTimeField('Дата регистрации', default=timezone.now)
    expired_at = models.DateTimeField('Срок обработки', null=True, blank=True)
    service = models.CharField('Услуга', max_length=100)
    gsd_group = models.CharField(
        'Группа GSD',
        blank=True,
        null=True,
        max_length=50,
    )
    title = models.CharField('Тема обращения', max_length=150)
    description = models.TextField('Полное описание')

    class Meta:
        verbose_name = 'Задача GSD'
        verbose_name_plural = 'Задачи GSD'

    def __str__(self):
        return f'{self.applicant} - {self.number}'


class SDTask(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'Новая'),
        ('ASSIGNED', 'Назначена'),
        ('IN_WORK', 'В работе'),
        ('COMPLETED', 'Завершена'),
    )

    SUPPORT_GROUP_CHOICES = (
        ('DISPATCHER', 'Диспетчера'),
        ('ENGINEER', 'Инженеры'),
    )

    applicant = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        verbose_name='Заявитель',
        related_name='applicant_sd_tasks',
        null=True,
    )
    number = models.CharField(
        'Номер заявки SD',
        db_index=True,
        max_length=10,
    )
    performer = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        verbose_name='Исполнитель',
        related_name='sd_tasks',
        null=True,
        blank=True,
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sd_tasks',
        verbose_name='Ресторан',
    )
    start_at = models.DateTimeField('Дата регистрации', default=timezone.now)
    finish_at = models.DateTimeField('Дата закрытия', null=True, blank=True)
    support_group = models.CharField(
        'Помощь от ',
        choices=SUPPORT_GROUP_CHOICES,
        default='DISPATCHER',
        db_index=True,
        max_length=10,
    )
    title = models.CharField('Тема обращения', max_length=150)
    description = models.TextField('Полное описание')
    status = models.CharField(
        'Статус',
        choices=STATUS_CHOICES,
        default='NEW',
        db_index=True,
        max_length=20,
    )
    closing_comment = models.TextField(
        'Комментарий закрытия',
        blank=True,
        null=True,
    )
    sub_task_number = models.TextField(
        'Список дочерних задач',
        blank=True,
        null=True,
    )
    doc_path = models.TextField(
        'Пути сохраненных файлов',
        blank=True,
        null=True,
    )
    rating = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[MaxValueValidator(5)],
        null=True,
        blank=True,
    )
    is_automatic = models.BooleanField('Автоматическая?', default=False)

    objects = SDTaskQuerySet.as_manager()

    class Meta:
        verbose_name = 'Задача Поддержки'
        verbose_name_plural = 'Задачи Поддержки'

    def __str__(self):
        return f'{self.applicant} - {self.number}'


class SyncReport(models.Model):
    start_at = models.DateTimeField(
        'Время запуска синхронизации',
        default=timezone.now,
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='sync_reports',
        verbose_name='Инициатор',
    )
    server_type = models.ForeignKey(
        'ServerType',
        on_delete=models.PROTECT,
        related_name='sync_reports',
        verbose_name='Что синхронизировали',
    )
    report = models.JSONField('Отчет')
    user_choice = models.CharField('Выбор пользователя', max_length=25)

    class Meta:
        verbose_name = 'Журнал синхронизации'
        verbose_name_plural = 'Журналы синхронизации'

    def __str__(self):
        return f'{self.start_at}'


class BotCommandCategory(models.Model):
    name = models.CharField('Команда', max_length=25, unique=True)

    class Meta:
        verbose_name = 'Категория Команды Бота'
        verbose_name_plural = 'Категории Команды Бота'

    def __str__(self):
        return self.name


class BotCommand(models.Model):
    name = models.CharField('Команда', max_length=25, unique=True)
    description = models.TextField('Описание команды', blank=True, default='')
    category = models.ForeignKey(
        'BotCommandCategory',
        on_delete=models.SET_NULL,
        related_name='category_bot_commands',
        verbose_name='Доступна для групп',
        blank=True,
        null=True,
    )
    view_priority = models.PositiveSmallIntegerField(
        'Порядок вывода команды',
        default=1,
    )
    groups = models.ManyToManyField(
        'Group',
        related_name='bot_commands',
        verbose_name='Доступна для групп',
        blank=True,
    )

    class Meta:
        verbose_name = 'Команда Бота'
        verbose_name_plural = 'Команды Бота'

    def __str__(self):
        return self.name


class Dispatcher(models.Model):
    dispatcher_number = models.PositiveSmallIntegerField(
        'Номер в диспетчере',
    )
    company = models.CharField(
        'Компания',
        max_length=100,
        blank=True,
        default='',
    )
    restaurant = models.CharField(
        'Ресторан',
        max_length=100,
        blank=True,
        default='',
    )
    itsm_number = models.CharField(
        'Номер ITSM',
        max_length=15,
        blank=True,
        default='',
    )
    performer = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='dispatcher_tasks',
        verbose_name='Исполнитель',
    )
    gsd_numbers = models.CharField(
        'Связанные заявки GSD',
        max_length=100,
        blank=True,
        default='',
    )
    closing_comment = models.TextField(
        'Комментарий закрытия',
        blank=True,
        null=True,
    )
    tg_documents = models.TextField(
        'Документы',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Задача из Диспетчера'
        verbose_name_plural = 'Задачи из Диспетчера'

    def __str__(self):
        return f'{self.dispatcher_number} - {self.performer}'
