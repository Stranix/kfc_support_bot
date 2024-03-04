import logging

from asgiref.sync import sync_to_async

from aiogram import html


from src.models import WorkShift
from src.models import CustomGroup
from src.models import SDTask
from src.bot.utils import send_notify, send_notify_to_seniors_engineers
from src.bot.utils import get_senior_engineers


logger = logging.getLogger('support_bot_tasks')


async def check_task_activate_step_1(task_number: str):
    logger.info('Проверка задачи %s первые 10 минут', task_number)
    notify = f'❗Внимание задачу {task_number} не взяли в работу спустя 10 мин'
    try:
        task = await SDTask.objects.select_related(
            'new_performer',
            'new_applicant',
        ).aget(number=task_number)
    except SDTask.DoesNotExist:
        logger.warning('Задачи %s не существует в БД', task_number)
        return

    if task.new_performer:
        logger.info('На задачу назначен инженер')
        return

    managers = await CustomGroup.objects.group_managers('', task.support_group)
    await send_notify(managers, notify)
    await send_notify(
        [task.new_applicant],
        f'Не взяли в работу задачу {task.number} за 10 минут.\nСообщил старшим',
    )


async def check_task_activate_step_2(task_number: str):
    logger.debug('Проверка задачи %s через 20 минут', task_number)
    notify = f'‼Задачу {task_number} не взяли работу в течении 20 минут'
    task = await SDTask.objects.select_related(
        'new_applicant',
        'new_performer',
    ).aget(number=task_number)
    if task.new_performer:
        logger.info('На задачу назначен инженер')
        return
    await send_notify_to_seniors_engineers(notify)
    await send_notify(
        [task.new_applicant],
        f'Не взяли в работу задачу {task.number} за 20 минут.\n'
        f'Сообщил Ведущим'
        f'\n\n{html.italic("Инженеры работают, как правило с 8 утра")}'
    )


async def check_task_deadline(task_number: str):
    logger.debug('Проверка задачи %s через два часа', task_number)
    notify = f'🆘Задача {html.code(task_number)} не закрыта за два часа'
    task = await SDTask.objects.select_related(
        'new_performer',
    ).aget(number=task_number)

    if task.finish_at:
        logger.debug('Задача завершена')
        return

    if not task.performer:
        logger.info(
            'Прошло два часа, а на задаче %s нет инженера',
            task_number,
        )
        notify = f'🧨Прошло два часа, а на задаче {task_number} нет инженера!'
        await send_notify_to_seniors_engineers(notify)
        return

    engineer = task.new_performer
    managers = []
    for group in engineer.groups.all():
        managers.extend(group.managers.all())

    recipients_notification = [*managers, *await get_senior_engineers()]
    recipients_notification = list(set(recipients_notification))
    logger.debug('recipients_notification: %s', recipients_notification)
    await send_notify(recipients_notification, notify)


async def check_end_of_shift(shift_id: int):
    logger.debug('Проверка завершении смены сотрудником после 9 часов')
    shift = await WorkShift.objects.select_related(
        'new_employee',
    ).aget(id=shift_id)
    engineer = shift.new_employee
    notify = f'🔴 У сотрудника {engineer.name} не закрыта смена спустя 9 часов'
    if shift.shift_end_at:
        logger.debug(
            'Смена %s сотрудника %s, закрыта в %s',
            shift.id,
            engineer.name,
            shift.shift_end_at.strftime('%d-%m-%Y %H:%M:%S'),
        )
        return
    logger.debug(
        'У сотрудника %s не закрыта смена %s',
        engineer.name,
        shift.id,
    )
    logger.debug('Отправка уведомления менеджерам')
    managers = []
    for group in await sync_to_async(list)(engineer.groups.all()):
        group_managers = await sync_to_async(list)(group.managers.all())
        logger.debug('group_managers: %s', group_managers)
        managers.extend(group_managers)
    logger.debug('managers: %s', managers)
    await send_notify(managers, notify)
    logger.debug('Отправка уведомления инженеру')
    notify_to_engineer = '🔴 Прошло 9 часов, а у тебя не закрыта смена.\n\n' \
                         'Для закрытия смены используй команду /end_shift'
    await send_notify([engineer], notify_to_engineer)
    logger.debug('Проверка завершена')