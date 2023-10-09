from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator


class Employee(models.Model):
    name = models.CharField('Имя', max_length=50)
    tg_id = models.PositiveIntegerField(
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
    groups = models.ManyToManyField(
        'Group',
        related_name='employees',
        verbose_name='Группа доступа',
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
    shift_start_break_at = models.DateTimeField(
        'Старт перерыва',
        null=True,
        blank=True,
    )
    shift_end_break_at = models.DateTimeField(
        'Завершение перерыва',
        null=True,
        blank=True,
    )
    shift_end_at = models.DateTimeField(
        'Завершение смены',
        null=True,
        blank=True,
    )
    is_works = models.BooleanField('Работает?', default=True)

    class Meta:
        verbose_name = 'Рабочая Смена'
        verbose_name_plural = 'Рабочие Смены'

    def __str__(self):
        return f'{self.employee.name} - {self.shift_start_at}'


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


class Task(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'Новая'),
        ('ASSIGNED', 'Назначена'),
        ('IN_WORK', 'В работе'),
        ('SUSPENDED', 'Приостановлена'),
        ('COMPLETED', 'Завершена'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Низкий'),
        ('MID', 'Средний'),
        ('HIGH', 'Высокий'),
        ('CRITICAL', 'Критичный'),
    )

    applicant = models.CharField('Заявитель', max_length=100)
    number = models.CharField(
        'Номер заявки GSD',
        unique=True,
        db_index=True,
        max_length=25,
    )
    performer = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        verbose_name='Исполнитель',
        related_name='tasks',
        null=True,
        blank=True,
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Ресторан',
    )
    start_at = models.DateTimeField('Дата регистрации', default=timezone.now)
    expired_at = models.DateTimeField('Срок обработки', null=True, blank=True)
    finish_at = models.DateTimeField('Дата закрытия', null=True, blank=True)
    priority = models.CharField(
        'Приоритет',
        choices=PRIORITY_CHOICES,
        default='LOW',
        db_index=True,
        max_length=20,
    )
    service = models.CharField('Услуга', max_length=100)
    title = models.CharField('Тема обращения', max_length=150)
    description = models.TextField('Полное описание')
    status = models.CharField(
        'Статус',
        choices=STATUS_CHOICES,
        default='NEW',
        db_index=True,
        max_length=20,
    )
    gsd_group = models.CharField(
        'Группа GSD',
        blank=True,
        null=True,
        max_length=50,
    )
    rating = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[MaxValueValidator(5)],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return f'{self.applicant} - {self.number}'


class TaskComment(models.Model):
    task = models.ForeignKey(
        'Task',
        on_delete=models.PROTECT,
        related_name='comments',
        verbose_name='Задача номер',
    )
    comment = models.TextField('Комментарий')
    author = models.CharField('Автор комментария', max_length=150)
    group_gsd = models.CharField(
        'Группа GSD',
        blank=True,
        null=True,
        max_length=100,
    )
    time_comment = models.DateTimeField(
        'Дата комментария',
        default=timezone.now,
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.task} - {self.comment}'


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


class BotCommand(models.Model):
    name = models.CharField('Команда', max_length=25, unique=True)
    description = models.TextField('Описание команды', blank=True, default='')
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
