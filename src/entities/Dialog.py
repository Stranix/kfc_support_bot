from aiogram import html

from src.entities.FieldEngineer import FieldEngineer
from src.models import SDTask


class Dialog:

    @staticmethod
    def no_rights_for_command():
        return 'Нет прав на использование команды'

    @staticmethod
    def close_task_request_task_number():
        message = (
            'Напишите номер заявки по которой вы приехали\n'
            f'Например: {html.code("SC1395412")}, {html.code("INC0002295")}'
            f'\n\n‼{html.italic("Буквы обязательны !!!")}'
        )
        return message

    @staticmethod
    def close_task_wrong_task_number():
        help_message = html.italic(
            'Если передумал - используй команду отмены /cancel'
        )
        message = (
                'Не правильный формат номера задачи\n'
                'Номер задачи должен содержать:\n'
                '1. буквенный код (2-3 символа)\n'
                '2. 7-ми значный номер'
                f'Пример: {html.code("SC1395412, INC0002295")}\n\n'
                f'{help_message}'
        )
        return message

    @staticmethod
    def close_task_request_acts():
        message = (
            'Приложи акты.\n'
            'Файлы прикладываются в виде документа (без сжатия)'
        )
        return message

    @staticmethod
    def close_task_wrong_acts():
        message = (
            'Все еще жду документы.\n'
            'Пересылку, сжатые фото - не понимаю'
        )
        return message

    @staticmethod
    def close_task_confirmation_one_document():
        return 'Получен один документ. Все верно?'

    @staticmethod
    def close_task_confirmation_documents(documents: dict):
        message = (
            f'Получил {len(documents)} документ(ов)\n'
            f'Имена файлов: {html.code(", ".join(documents.keys()))}\n\n'
            f'Все верно?',
        )
        return message

    @staticmethod
    def new_support_task_for_creator(task: SDTask):
        help_message = html.italic('Регламентное время связи 10 минут')
        message = (
                f'Заявка принята.\n'
                f'Внутренний номер: {html.code(task.number)}\n'
                f'Запрос: {task.title}\n'
                f'Инженерам отправлено уведомление\n\n'
                f'{help_message}'
        )
        return message

    @staticmethod
    def new_task_no_engineers_on_shift(task_number):
        message = (
            f'Поступил запрос на помощь, но нет инженеров на смене\n'
            f'Номер обращения: {html.code(task_number)}'
        )
        return message

    @staticmethod
    def rating_feedback(task_number: str):
        return f'Спасибо за оценку задачи {task_number}'

    @staticmethod
    def new_task_notify_for_engineers(task: SDTask, creator: FieldEngineer):
        message = (
            f'Инженеру требуется помощь '
            f'по задаче {html.code(task.number)}\n\n'
            f'Описание: {html.code(task.description)}\n'
            f'Телеграм для связи: @{creator.user.tg_nickname}\n\n'
        )
        if task.support_group == 'DISPATCHER':
            message += html.italic(
                '‼Не забудь запросить акт и заключение (если требуется)',
            )
        return message

    @staticmethod
    def support_help_whose_help_is_needed():
        return 'Чья помощь требуется?'

    @staticmethod
    def support_help_request_task_number():
        message = (
            'Напишите номер заявки по которой вы приехали\n'
            f'Например: {html.code("1395412")}'
        )
        return message

    @staticmethod
    def support_help_wrong_task_number():
        help_message = html.italic(
            'Если передумал - используй команду отмены /cancel',
        )
        message = (
                'Не правильный формат номера задачи\n'
                'Номер задачи должен быть от 6 до 7 цифр\n'
                f'Пример: {html.code("1395412")} \n\n'
                f'{help_message}'
        )
        return message

    @staticmethod
    def support_help_request_task_description():
        return 'Напиши с чем нужна помощь'

    @staticmethod
    def support_help_wrong_task_description():
        message = (
            f'Нет описания по задаче. Чем помочь?\n\n'
            f'{html.italic("описание только в виде текста")}'
        )
        return message

    @staticmethod
    def support_help_request_task_result(task_number, task_description):
        message = (
            'Подводим итог: \n'
            f'Требуется помощь по задаче: {task_number}\n'
            f'Детали: {task_description}\n\n'
            'Все верно?',
        )
        return message

    @staticmethod
    def prepare_task_message():
        return 'Формирую задачу. Ожидайте...'

    @staticmethod
    def task_not_found_message():
        return 'Не нашел информацию по задаче'

    @staticmethod
    def dispatcher_task_request_acts():
        message = (
            'Приложите акты и заключения (если есть) '
            '<b>БЕЗ СЖАТИЯ(Документом)</b>\n'
            f'Если документов нет напишите: {html.italic("без документов")}'
        )
        return message

    @staticmethod
    def dispatcher_task_description():
        message = (
            '\nЗакрыть заявку во внешней системе\n'
            'Связана с задачами : {gsd_numbers}\n'
            'Комментарий закрытия от инженера: {task_commit}'
        )
        return message
