import pytz
import logging

from datetime import time
from datetime import datetime
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from src.models import Task
from src.models import Employee

logger = logging.getLogger('support_web')


def index(request):
    if not request.user.is_authenticated:
        return render(request, template_name='pages/stub.html')
    return render(request, template_name='pages/index.html')


@login_required(login_url='/accounts/login/')
def show_employee(request):
    table_employees = {
        'headers': [
            'Имя',
            'Телеграм',
            'Группы доступа',
            'Менеджеры',
            'Дата регистрации',
            'Активирован?'
        ],
    }
    employees = Employee.objects.prefetch_related('groups', 'managers').all()
    table_employees['users'] = employees
    return render(
        request,
        template_name='pages/employee.html',
        context={'table_employees': table_employees},
    )


@login_required(login_url='/accounts/login/')
def show_support_tasks(request):
    shift_date = request.GET.get('date')
    if shift_date:
        shift_date = datetime.strptime(shift_date, '%Y-%m-%d').date()
    if not shift_date:
        shift_date = timezone.now().date()
    logger.debug('shift_date: %s', shift_date)

    today = shift_date
    tomorrow = today + timedelta(1)
    shift_start_at = datetime.combine(today, time(), tzinfo=pytz.UTC)
    shift_end_at = datetime.combine(tomorrow, time(), tzinfo=pytz.UTC)
    shift_end_at -= timedelta(seconds=1)

    tasks = Task.objects.prefetch_related('performer').filter(
        number__startswith='SD-',
        start_at__lte=shift_end_at,
        start_at__gte=shift_start_at,
    )
    tasks_tables = {
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
        'tasks': tasks,
    }
    return render(
        request,
        template_name='pages/sd_tasks.html',
        context={
            'tasks_tables': tasks_tables,
            'shift_date': shift_date,
        },
    )
