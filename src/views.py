import json
import logging

from dataclasses import asdict

from datetime import datetime

from asgiref.sync import async_to_sync

from aiogram.types import Update

from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required

from src import utils
from src.models import SDTask
from src.models import CustomUser
from src.models import WorkShift
from src.models import SyncReport
from src.bot.webhook import tg_webhook_init

logger = logging.getLogger('support_web')
bot, dispatcher = tg_webhook_init()


def index(request):
    if not request.user.is_authenticated:
        return render(request, template_name='pages/stub.html')
    return render(request, template_name='pages/index.html')


@login_required
@permission_required('auth.web_app', raise_exception=True)
def show_employee(request):
    table_employees = {
        'headers': [
            'Имя',
            'Имя в диспетчере',
            'Телеграм',
            'Группы доступа',
            'Менеджеры',
            'Дата регистрации',
            'Активирован?'
        ],
    }
    employees = CustomUser.objects.prefetch_related('groups').order_by('-id')
    table_employees['users'] = employees
    return render(
        request,
        template_name='pages/employee.html',
        context={'table_employees': table_employees},
    )


@login_required
@permission_required('auth.web_app', raise_exception=True)
def show_support_tasks(request):
    support_group = request.GET.get('support_group')
    start_shift_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    if start_date:
        start_shift_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    end_shift_date = timezone.now().date()
    end_date = request.GET.get('end_date')
    if end_date:
        end_shift_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    logger.debug('start_shift_date: %s', start_shift_date)
    logger.debug('end_shift_date: %s', end_shift_date)

    tasks = SDTask.objects.in_period_date(start_shift_date, end_shift_date)
    if support_group == 'dispatchers':
        tasks = tasks.exclude(support_group='ENGINEER')
    if support_group == 'engineers':
        tasks = tasks.exclude(support_group='DISPATCHER')
    tasks_stat = utils.get_tasks_stat(tasks)
    tasks_table = {
        'headers': [
            'Номер',
            'Тема обращения',
            'Заявитель',
            'Исполнитель',
            'Дата регистрации',
            'Дата закрытия',
            'Время выполнения',
            'Описание',
            'Комментарий закрытия',
            'Дочерние заявки',
            'Документы',
            'Статус',
            'Оценка',
        ],
        'tasks': asdict(tasks_stat),
    }
    return render(
        request,
        template_name='pages/sd_tasks.html',
        context={
            'tasks_table': tasks_table,
            'start_shift_date': start_shift_date,
            'end_shift_date': end_shift_date,
        },
    )


@login_required
@permission_required('auth.web_app', raise_exception=True)
def show_shifts(request):
    shift_date = timezone.now().date()
    logger.debug('shift_date: %s', shift_date)
    shift_start_at, shift_end_at = utils.get_start_end_datetime_on_date(
        shift_date,
    )
    works_shifts = WorkShift.objects.prefetch_related(
        'new_employee',
        'break_shift',
    ).filter(
        Q(shift_start_at__gte=shift_start_at),
        Q(shift_end_at__lte=shift_end_at) | Q(shift_end_at__isnull=True),
    )
    shift_table = {
        'headers': [
            'Сотрудник',
            'Начало смены',
            'Перерывы',
            'Завершение смены',
            'Работает?',
        ],
        'shifts': works_shifts,
    }
    return render(
        request,
        template_name='pages/work_shifts.html',
        context={
            'shift_table': shift_table,
        },
    )


@login_required
@permission_required('auth.web_app', raise_exception=True)
def show_shift_report(request):
    shift_date = request.GET.get('date')
    if shift_date:
        shift_date = datetime.strptime(shift_date, '%Y-%m-%d').date()
    if not shift_date:
        shift_date = timezone.now().date()
    logger.debug('shift_date: %s', shift_date)
    engineers_on_shift = utils.get_info_for_engineers_on_shift(shift_date)
    tasks_on_shift = utils.get_tasks_on_shift(shift_date)
    engineers_table = {
        'headers': [
            'Имя',
            'Группа',
            'Пришел',
            'Ушел',
            'Длительность Перерыва',
            'Количество закрытых задач',
            'Средняя оценка',
        ],
        'engineers_on_shift': asdict(engineers_on_shift)
    }
    tasks_table = {
        'headers': [
            'Номер',
            'Заявитель',
            'Исполнитель',
            'Дата регистрации',
            'Дата закрытия',
            'Описание',
            'Статус выполнения',
            'Оценка',
        ],
        'tasks': asdict(tasks_on_shift),
    }
    context = {
        'shift_date': shift_date,
        'engineers_table': engineers_table,
        'tasks_table': tasks_table,
    }
    return render(
        request,
        template_name='pages/shift_report.html',
        context=context,
    )


@login_required
@permission_required('auth.web_app', raise_exception=True)
@permission_required('auth.dealers', raise_exception=True)
def show_dealers_report(request):
    support_group = request.GET.get('support_group')
    start_shift_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    if start_date:
        start_shift_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    end_shift_date = timezone.now().date()
    end_date = request.GET.get('end_date')
    if end_date:
        end_shift_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    logger.debug('start_shift_date: %s', start_shift_date)
    logger.debug('end_shift_date: %s', end_shift_date)

    tasks = SDTask.objects.in_period_date(
        start_shift_date,
        end_shift_date,
        request.user.groups.first().name,
    )
    if support_group == 'dispatchers':
        tasks = tasks.exclude(support_group='ENGINEER')
    if support_group == 'engineers':
        tasks = tasks.exclude(support_group='DISPATCHER')
    tasks_stat = utils.get_tasks_stat(tasks)
    tasks_table = {
        'headers': [
            'Номер',
            'Тема обращения',
            'Заявитель',
            'Исполнитель',
            'Дата регистрации',
            'Дата закрытия',
            'Время выполнения',
            'Описание',
            'Комментарий закрытия',
            'Дочерние заявки',
            'Документы',
            'Статус',
            'Оценка',
        ],
        'tasks': asdict(tasks_stat),
    }
    return render(
        request,
        template_name='pages/dealers.html',
        context={
            'tasks_table': tasks_table,
            'start_shift_date': start_shift_date,
            'end_shift_date': end_shift_date,
        },
    )


def show_sync_report_prev(request):
    last_4_sync_reports = SyncReport.objects.prefetch_related(
        'new_employee',
        'server_type'
    ).all().order_by('-id')[:4]
    sync_reports = []
    for sync in last_4_sync_reports:
        sync_report = {
            'id': sync.id,
            'sync_date': sync.start_at,
            'employee': sync.employee,
            'what_sync': sync.user_choice,
        }
        sync_completed, sync_errors = utils.get_sync_statuses(sync.report)
        sync_report['errors'] = len(sync_errors)
        sync_report['completed'] = len(sync_completed)
        sync_reports.append(sync_report)
    return render(
        request,
        template_name='pages/sync_report_prev.html',
        context={'sync_reports': sync_reports},
    )


def show_sync_report(request, pk):
    sync = get_object_or_404(SyncReport, pk=pk)
    sync_report = {
        'table': {
            'headers': [
                'Имя сервера',
                'Web_server',
                'Ошибка',
            ],
        },
        'sync_date': sync.start_at,
        'employee': sync.employee,
        'what_sync': sync.user_choice,
        'sync_status': {
            'errors': [],
            'completed': [],
        }
    }
    sync_completed, sync_errors = utils.get_sync_statuses(sync.report)
    sync_report['sync_status']['completed'] = sync_completed
    sync_report['sync_status']['errors'] = sync_errors
    return render(
        request,
        template_name='pages/sync_report.html',
        context={'sync_report': sync_report},
    )


@csrf_exempt
@async_to_sync
async def bot_webhook(request):
    logger.debug('Обновление: ', request.body.decode(encoding='UTF-8'))
    update = Update.model_validate(
        json.loads(request.body.decode(encoding='UTF-8')),
    )
    await dispatcher.feed_update(bot, update)
    return HttpResponse(status=200)
