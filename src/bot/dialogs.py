import logging

from typing import Any

from django.template.loader import render_to_string

from src.bot import keyboards

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
) -> str:
    """Уведомление о новой задаче для инженеров или диспетчеров"""
    context = {
        'created_task_for_engineers': True,
        'task_number': number,
        'task_description': description.replace('\n', '<br>'),
        'user_tg_nick_name': creator_contact,
        'dispatcher': True if support_group == 'DISPATCHER' else False,
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


async def notify_for_engineers_from_dispatcher(
        task_id: int,
        disp_number: str,
        outside_number: str,
        commit: str,
) -> tuple:
    """Создание заявки из отбивки диспетчера в телеграме"""
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


async def additional_chat_for_performer():
    """Сообщение по доп работам для диспетчера"""
    context = {
        'for_performer': True,
    }
    return await tg_render_message('bot/additional.html', context)
