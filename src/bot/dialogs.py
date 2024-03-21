import logging

from typing import Any

from django.template.loader import render_to_string

from src.bot import keyboards
from src.entities.SupportEngineer import SupportEngineer
from src.models import SDTask, GSDTask, SimpleOneTask, Restaurant

logger = logging.getLogger('support_bot')


async def tg_render_message(template: str, context: Any = None) -> str:
    logger.info('Подготовка сообщения')
    message: str = render_to_string(template, context)
    message = message.replace('\n', '').replace('<br>', '\n')
    return message


async def required_task_number() -> str:
    """Команда /close. Начало.
    Запрос номера задачи по которой приехал инженер
    """
    context = {'step': 1}
    return await tg_render_message('bot/close.html', context)


async def required_documents() -> str:
    """Команда /close. Шаг два.
    Запрос актов и тех заключений для задачи от выездного
    """
    context = {'step': 2}
    return await tg_render_message('bot/close.html', context)


async def wrong_task_number() -> str:
    """Команда /close. Ошибка ввода номера задачи"""
    context = {'wrong_task_number': True}
    return await tg_render_message('bot/errors.html', context)


async def confirmation_received_documents(documents: dict) -> tuple:
    """Команда /close. Подтверждение для полученных документов"""
    context = {
        'step': 3,
        'doc_count': len(documents),
        'doc_names': ', '.join(documents.keys()),
    }
    message = await tg_render_message('bot/close.html', context)
    keyboard = await keyboards.get_yes_no_cancel_keyboard()
    return message, keyboard


async def confirmation_received_documents_disp(documents: dict) -> tuple:
    """Команда /close_task. Подтверждение для полученных документов"""
    context = {
        'step': 3,
        'doc_count': len(documents),
        'doc_names': ', '.join(documents.keys()),
    }
    message = await tg_render_message('bot/close.html', context)
    keyboard = await keyboards.get_choice_task_doc_approved_keyboard()
    return message, keyboard


async def waiting_creating_task() -> str:
    """Команда /close. Информирование о формирования задачи"""
    context = {'creating_task': True}
    return await tg_render_message('bot/common.html', context)


async def error_no_engineers_on_shift(number: str) -> str:
    """Уведомление, что нет инженеров на смене при новой задаче"""
    context = {
        'no_engineers_on_shift': True,
        'task_number': number,
    }
    return await tg_render_message('bot/errors.html', context)


async def new_task_notify_for_engineers(
        number: str,
        description: str,
        creator_contact: str,
        support_group: str,
        legal: str,
) -> str:
    """Уведомление о новой задаче для инженеров или диспетчеров"""
    context = {
        'created_task_for_engineers': True,
        'task_number': number,
        'task_description': description.replace('\n', '<br>'),
        'user_tg_nick_name': creator_contact,
        'dispatcher': True if support_group == 'DISPATCHER' else False,
        'legal': legal,
    }
    return await tg_render_message('bot/common.html', context)


async def new_task_notify_for_creator(number: str, title: str) -> str:
    """Уведомление о фиксации новой задачи для инициатора"""
    context = {
        'created_task_for_creator': True,
        'task_number': number,
        'task_title': title,
    }
    return await tg_render_message('bot/common.html', context)


async def error_empty_documents() -> str:
    """Сообщение об ошибке в случаи отсутствия документов"""
    context = {'empty_doc': True}
    return await tg_render_message('bot/errors.html', context)


async def support_help_whose_help_is_needed() -> tuple:
    """Команда /support_help. Вопрос чья помощь требуется."""
    message = 'Чья помощь требуется?'
    keyboard = await keyboards.get_choice_support_group_keyboard()
    return message, keyboard


async def support_help_choice_legal_entity() -> tuple:
    """Команда /support_help. Выбор юр лица"""
    message = 'К какому юр лицу принадлежит ресторан?'
    keyboard = await keyboards.get_choice_legal_entity_keyboard()
    return message, keyboard


async def request_task_description() -> str:
    """Команда /support_help. Запрос описания к задаче"""
    return 'Напиши, с чем нужна помощь?'


async def request_task_confirmation(number: str, description: str) -> tuple:
    """Команда /support_help. Запрос подтверждения полученной информации"""
    context = {
        'task_confirmation': True,
        'task_number': number,
        'task_description': description,
    }
    message = await tg_render_message('bot/support_help.html', context)
    keyboard = await keyboards.get_approved_task_keyboard(number)
    return message, keyboard


async def error_wrong_task_description() -> str:
    """Ошибка. Нет описания к задаче"""
    context = {'wrong_task_description': True}
    return await tg_render_message('bot/errors.html', context)


async def rating_feedback(number: str) -> str:
    """Благодарность за оценку задачи"""
    context = {
        'rating_feedback': True,
        'task_number': number,
    }
    return await tg_render_message('bot/common.html', context)


async def error_task_not_found() -> str:
    """Ошибка что не нашлась задача в базе"""
    return 'Не нашел информацию по задаче'


async def work_shift_exist() -> str:
    """Информация. Смена уже открыта"""
    return 'У вас уже есть открытая смена'


async def start_work_shift() -> str:
    """Информация. Смена Начата"""
    return 'Вы добавлены в очередь на получение задач'


async def end_work_shift() -> str:
    """Информация. Смена Закончена"""
    return 'Смена окончена. Пока 👋'


async def notify_for_engineers_from_dispatcher(
        task_id: int,
        disp_number: str,
        outside_number: str,
        commit: str,
) -> tuple:
    """Создание заявки из отбивки диспетчера в телеграм"""
    context = {
        'number': disp_number,
        'outside_number': outside_number,
        'task_commit': commit,
    }
    message = await tg_render_message('bot/notify_disp.html', context)
    keyboard = await keyboards.get_choice_dispatcher_task_closed_keyboard(
        task_id,
    )
    return message, keyboard


async def additional_chat_message(number: str):
    """Сообщение для чата доп работ"""
    context = {
        'for_chat': True,
        'number': number,
    }
    return await tg_render_message('bot/additional.html', context)


async def additional_chat_for_creator(
        task_id: str,
        number: str,
        title: str,
) -> tuple:
    """Сообщение по доп работам для выездного инженера"""
    context = {
        'for_creator': True,
        'number': number,
        'task_title': title,
    }
    message = await tg_render_message('bot/additional.html', context)
    keyboard = await keyboards.get_task_feedback_keyboard(int(task_id))
    return message, keyboard


async def additional_chat_for_performer() -> str:
    """Сообщение по доп работам для диспетчера"""
    context = {
        'for_performer': True,
    }
    return await tg_render_message('bot/additional.html', context)


async def new_task_notify_for_middle(task_numbers: list):
    """Сообщение с новыми задачами для старших инженеров"""
    context = {
        'new_task_for_middle': True,
        'task_numbers': task_numbers,
    }
    return await tg_render_message('bot/common.html', context)


async def engineer_on_shift(name: str) -> str:
    """Уведомление. Инженер на смене для менеджеров"""
    context = {
        'name': name
    }
    return await tg_render_message('bot/on_shift.html', context)


async def engineer_end_shift(name: str) -> str:
    """Уведомление. Инженер завершил смену для менеджеров"""
    context = {
        'name': name
    }
    return await tg_render_message('bot/end_shift.html', context)


async def start_break_message() -> str:
    """Команда /break_start. Уведомление для сотрудника"""
    return '⏰Ваш перерыв начался'


async def engineer_start_break(engineer_name: str) -> str:
    """Команда /break_start. Уведомление для менеджеров"""
    context = {
        'start_break': True,
        'name': engineer_name,
    }
    return await tg_render_message('bot/breaks_shift.html', context)


async def stop_break_message() -> str:
    """Команда /break_stop. Уведомление для сотрудника"""
    return '⏰Ваш перерыв завершен'


async def engineer_stop_break(engineer_name: str) -> str:
    """Команда /break_stop. Уведомление для менеджеров"""
    context = {
        'end_break': True,
        'name': engineer_name,
    }
    return await tg_render_message('bot/breaks_shift.html', context)


async def error_no_active_shift() -> str:
    """Сообщение об ошибке. Нет активной смены"""
    context = {
        'no_active_shift': True,
    }
    return await tg_render_message('bot/errors.html', context)


async def error_no_active_breaks() -> str:
    """Сообщение об ошибке. Нет активных перерывов"""
    context = {
        'no_active_breaks': True,
    }
    return await tg_render_message('bot/errors.html', context)


async def error_active_break_exist() -> str:
    """Команда /break_start. Сообщение об ошибке: перерыв уже начат"""
    return 'Есть незавершенный перерыв.\nЗавершите его.'


async def error_active_break_not_exist() -> str:
    """Команда /break_stop. Сообщение об ошибке: нет активного перерыва"""
    return 'У вас нет активных перерывов 🤷‍♂'


async def error_no_new_tasks() -> str:
    """Сообщение об ошибке: нет новых задач"""
    return 'Нет новых задач 🥹'


async def request_show_task_info(tasks_numbers: list) -> tuple:
    """Запрос по какой задаче показать информацию"""
    keyboard = await keyboards.create_tg_keyboard_markup(tasks_numbers)
    message = 'По какой задаче показать информацию?'
    return message, keyboard


async def error_task_performer_exist(performer_name: str) -> str:
    """На задачу уже назначен исполнитель"""
    context = {
        'performer_exist': True,
        'name': performer_name,
    }
    return await tg_render_message('bot/errors.html', context)


async def sd_task_info(task: SDTask, short: bool = True) -> tuple:
    """Описание по внутренней задачи поддержки"""
    context = {
        'short': short,
        'task': task,
    }
    keyboard = await keyboards.get_support_task_keyboard(task.id)
    message = await tg_render_message('bot/sd_task.html', context)
    return message, keyboard


async def sd_task_start_for_performer(task: SDTask) -> str:
    """Сообщение: задачу взяли в работу для исполнителя"""
    context = {
        'for_performer': True,
        'task': task,
    }
    return await tg_render_message('bot/sd_task.html', context)


async def sd_task_start_for_creator(task: SDTask) -> str:
    """Сообщение: задачу взяли в работу для создателя"""
    context = {
        'for_creator': True,
        'task': task,
    }
    return await tg_render_message('bot/sd_task.html', context)


async def request_choice_engineer_for_assign(engineers_names: list) -> tuple:
    """Запрос выбора инженера для назначения на задачу"""
    message = 'Выберите инженера на смене для назначения'
    keyboard = await keyboards.create_tg_keyboard_markup(engineers_names)
    return message, keyboard


async def sd_task_assign_for_appointer(
        task_number: str,
        performer: str,
) -> str:
    """Назначение заявки. Сообщение для назначающего"""
    context = {
        'for_appointer': True,
        'number': task_number,
        'engineer_name': performer,
    }
    return await tg_render_message('bot/sd_task.html', context)


async def sd_task_assign_for_creator(task: SDTask) -> str:
    """Назначение заявки. Сообщение автору задачи"""
    return await sd_task_start_for_creator(task)


async def sd_task_assign_for_performer(
        appointer_name: str,
        task: SDTask,
) -> str:
    """Назначение заявки. Уведомление для исполнителя"""
    context = {
        'assign_performer': True,
        'appointer_name': appointer_name,
        'task': task,
    }
    return await tg_render_message('bot/sd_task.html', context)


async def error_not_tasks_in_work() -> str:
    """Ошибка. Нет задач в работе"""
    context = {
        'not_tasks_in_work': True,
    }
    return await tg_render_message('bot/errors.html', context)


async def request_task_for_close(task_numbers: list) -> tuple:
    """Команда /close_task. Запрос номера задачи на закрытие"""
    keyboard = await keyboards.create_tg_keyboard_markup(task_numbers)
    message = 'Какую задачу будем закрывать?'
    return message, keyboard


async def error_wrong_task_performer(performer_name: str) -> str:
    """Ошибка. Неправильный исполнитель"""
    context = {
        'wrong_task_performer': True,
        'name': performer_name,
    }
    return await tg_render_message('bot/errors.html', context)


async def request_check_documents() -> tuple:
    """Запрос проверки документов"""
    message = 'Внимательно проверь документы!\nВсе верно?'
    keyboard = await keyboards.get_choice_task_doc_approved_keyboard()
    return message, keyboard


async def wait_load_documents() -> str:
    """Ожидание загрузки документов"""
    return 'Готовлю документы. Ожидайте...'


async def request_documents() -> tuple:
    """Команда /close_task. Диспетчер. Запрос документов"""
    context = {
        'dispatcher_request_documents': True,
    }
    keyboard = await keyboards.create_tg_keyboard_markup(['без документов'])
    message = await tg_render_message('bot/close_task.html', context)
    return message, keyboard


async def without_documents() -> tuple:
    """Команда /close_task. Диспетчер. Без документов"""
    keyboard = await keyboards.get_choice_task_doc_approved_keyboard()
    message = 'Нет актов и заключений. Все верно?'
    return message, keyboard


async def request_sub_tasks() -> tuple:
    """Команда /close_task. Диспетчер. Запрос дочерних задач"""
    context = {
        'disp_sub_tasks': True,
    }
    keyboard = await keyboards.create_tg_keyboard_markup(['нет'])
    message = await tg_render_message('bot/close_task.html', context)
    return message, keyboard


async def retry_request_documents() -> str:
    """Команда /close_task. Диспетчер. Повторный запрос документов"""
    return 'Ок. Давай попробуем еще раз. Жду документы'


async def request_task_close_commit() -> str:
    """Команда /close_task. Диспетчер. Запрос комментария закрытия задачи"""
    return 'Введите комментарий для закрытия'


async def close_task_request_approved(
        tg_docs_name: str,
        task_number: str,
        sub_tasks: list[str],
        task_close_comment: str,
) -> tuple:
    """Команда /close_task. Подведение итогов, перед закрытием заявки"""
    context = {
        'close_task_approved': True,
        'task_number': task_number,
        'tg_docs_name': tg_docs_name,
        'sub_tasks': sub_tasks,
        'task_close_comment': task_close_comment,
    }
    keyboard = await keyboards.get_choice_task_closed_approved_keyboard()
    message = await tg_render_message('bot/close_task.html', context)
    return message, keyboard


async def sd_task_close_for_creator(
        task_id: int,
        task_number: str,
        task_title: str,
) -> tuple:
    context = {
        'for_creator': True,
        'number': task_number,
        'title': task_title,
    }
    keyboard = await keyboards.get_task_feedback_keyboard(task_id)
    message = await tg_render_message('bot/close_task.html', context)
    return message, keyboard


async def sd_task_close_for_performer(task_number: str) -> str:
    context = {
        'for_performer': True,
        'number': task_number,
    }
    return await tg_render_message('bot/close_task.html', context)


async def scan_chat_sd_task_info(
        task: SDTask,
        engineer: SupportEngineer,
        short: bool = True,
) -> tuple:
    """Описание внутренней задачи"""
    assign = False
    performer = ''
    if not task.new_performer and await engineer.has_perm('assign'):
        assign = True
    if task.new_performer:
        name = task.new_performer.name
        nickname = task.new_performer.tg_nickname
        performer = f'<code>{name}</code>(@{nickname})'
    context = {
        'short': short,
        'task': task,
        'performer': performer,
    }
    message = await tg_render_message('bot/scan_chat/sd.html', context)
    keyboard = await keyboards.get_sd_task_keyboard(
        task.id,
        short=short,
        assign=assign,
    )
    return message, keyboard


async def scan_chat_gsd_task_info(task: GSDTask, short: bool = True) -> tuple:
    """Описание задачи GSD"""
    keyboard = None
    context = {
        'short': short,
        'task': task,
    }
    message = await tg_render_message('bot/scan_chat/gsd.html', context)
    if short:
        keyboard = await keyboards.get_gsd_task_keyboard(task.id)
    return message, keyboard


async def scan_chat_simpleone_task_info(
        task: SimpleOneTask,
        short: bool = True,
) -> tuple:
    """Описание задачи SimpleOne"""
    keyboard = None
    context = {
        'short': short,
        'task': task,
    }
    message = await tg_render_message('bot/scan_chat/simpleone.html', context)
    if short:
        keyboard = await keyboards.get_simpleone_task_keyboard(task.id)
    return message, keyboard


async def restaurant_info(restaurant: Restaurant) -> str:
    """Информация по ресторану"""
    context = {
        'restaurant': restaurant,
    }
    return await tg_render_message('bot/scan_chat/restaurant.html', context)


async def error_restaurant_not_found() -> str:
    return 'Не нашел ресторан'
