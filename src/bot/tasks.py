import logging

from aiogram import html

from src.models import SDTask
from src.models import WorkShift
from src.entities.User import User
from src.entities.Message import Message
from src.entities.SupportEngineer import SupportEngineer
from src.bot.services import get_group_managers_by_support_group

logger = logging.getLogger('support_bot_tasks')


async def check_task_activate_step_1(task_number: str):
    logger.info('Проверка задачи %s первые 10 минут', task_number)
    notify = f'❗Внимание задачу {task_number} не взяли в работу спустя 10 мин'
    try:
        task = await SDTask.objects.by_number(task_number)
    except SDTask.DoesNotExist:
        logger.warning('Задачи %s не существует в БД', task_number)
        return

    if task.new_performer:
        logger.info('На задачу назначен инженер')
        return

    managers = await get_group_managers_by_support_group(task.support_group)
    await Message.send_tg_notification(
        managers,
        notify,
    )
    await Message.send_tg_notification(
        [User(task.new_applicant)],
        f'Не взяли в работу задачу {task.number} за 10 минут.\n'
        f'Сообщил старшим',
    )


async def check_task_activate_step_2(task_number: str):
    logger.debug('Проверка задачи %s через 20 минут', task_number)
    notify = f'‼Задачу {task_number} не взяли работу в течении 20 минут'
    task = await SDTask.objects.by_number(task_number)
    if task.new_performer:
        logger.info('На задачу назначен инженер')
        return
    await Message.send_notify_to_seniors_engineers(notify)
    await Message.send_tg_notification(
        [User(task.new_applicant)],
        f'Не взяли в работу задачу {task.number} за 20 минут.\n'
        f'Сообщил Ведущим'
        f'\n\n{html.italic("Инженеры работают, как правило с 8 утра")}',
    )


async def check_task_deadline(task_number: str):
    logger.debug('Проверка задачи %s через два часа', task_number)
    notify = f'🆘Задача {html.code(task_number)} не закрыта за два часа'
    task = await SDTask.objects.by_number(task_number)

    if task.finish_at:
        logger.debug('Задача завершена')
        return

    if not task.new_performer:
        logger.info(
            'Прошло два часа, а на задаче %s нет инженера',
            task_number,
        )
        notify = f'🧨Прошло два часа, а на задаче {task_number} нет инженера!'
        await Message.send_notify_to_seniors_engineers(notify)
        return
    support_engineer = SupportEngineer(task.new_performer)
    await Message.send_notify_to_group_managers(
        await support_engineer.group_id,
        notify,
    )
    await Message.send_notify_to_seniors_engineers(notify)


async def check_end_of_shift(shift_id: int):
    logger.debug('Проверка завершении смены сотрудником после 9 часов')
    shift = await WorkShift.objects.select_related(
        'new_employee',
    ).aget(id=shift_id)
    support_engineer = SupportEngineer(shift.new_employee)
    notify = f'🔴 У сотрудника {support_engineer.user.name} ' \
             f'не закрыта смена спустя 9 часов'
    if shift.shift_end_at:
        logger.debug(
            'Смена %s сотрудника %s, закрыта в %s',
            shift.id,
            support_engineer.user.name,
            shift.shift_end_at.strftime('%d-%m-%Y %H:%M:%S'),
        )
        return
    logger.debug(
        'У сотрудника %s не закрыта смена %s',
        support_engineer.user.name,
        shift.id,
    )
    await Message.send_notify_to_group_managers(
        await support_engineer.group_id,
        notify,
    )
    await Message.send_tg_notification(
        [support_engineer],
        '🔴 Прошло 9 часов, а у тебя не закрыта смена.\n\n'
        'Для закрытия смены используй команду /end_shift',
    )
    logger.debug('Проверка завершена')
