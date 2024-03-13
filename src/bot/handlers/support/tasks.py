import re
import logging

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from src import exceptions
from src.bot import dialogs
from src.models import SDTask
from src.entities.Message import Message
from src.entities.Service import Service
from src.entities.SupportEngineer import SupportEngineer


logger = logging.getLogger('support_bot')
router = Router(name='support_task_handlers')


class TaskState(StatesGroup):
    show_info = State()
    close_task = State()
    get_doc = State()
    doc_approved = State()
    approved_sub_tasks = State()
    task_comment = State()
    approved_close_tasks = State()
    show_docs = State()


class AssignedTaskState(StatesGroup):
    task = State()
    engineers_on_shift = State()
    task_applicant = State()


@router.message(Command('get_task'))
async def get_task(
        message: types.Message,
        support_engineer: SupportEngineer,
        state: FSMContext
):
    logger.info('Получаем список доступных задач')
    tasks = await SDTask.objects.new_task_by_engineer_group(support_engineer)
    if not tasks:
        logger.info('Нет новых задач')
        await message.answer(await dialogs.error_no_new_tasks())
        return
    tasks_numbers = [task.number for task in tasks]
    text, keyboard = await dialogs.request_show_task_info(tasks_numbers)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(TaskState.show_info)
    logger.info('Список доступных задач отправлен')


@router.message(
    TaskState.show_info,
    F.text.regexp(r'SD-(\d{5,7})+').as_('regexp'),
)
async def show_task_info(
        message: types.Message,
        regexp: re.Match[str],
        state: FSMContext,
):
    logger.info(f'Запрос показа информации по задаче: {regexp.group()}')
    task_number = regexp.group()
    task = await SDTask.objects.by_number(task_number)
    if task.new_performer:
        logger.warning('Заявку уже назначена на сотрудника')
        await message.answer(
            await dialogs.error_task_performer_exist(task.new_performer.name),
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    text, keyboard = dialogs.sd_task_info(task)
    await message.answer(text, reply_markup=keyboard)
    logger.info('Информация по задаче отправлена')
    await state.clear()


@router.callback_query(F.data.startswith('stask_'))
async def process_start_task(
        query: types.CallbackQuery,
        support_engineer: SupportEngineer,
):
    task_id = query.data.split('_')[1]
    try:
        task = await support_engineer.start_task(task_id)
        await Message.send_start_task_notify(task)
        logger.info(
            'Задачу взял в работу сотрудник %s',
            support_engineer.user.name,
        )
    except exceptions.TaskAssignedError as error:
        logger.debug('Задача %s назначена на сотрудника', task_id)
        await query.message.answer(error.message)
    except SDTask.DoesNotExist:
        logger.warning('Задачи %s нет в базе', task_id)
        await query.message.answer(await dialogs.error_task_not_found())
    finally:
        await query.message.delete()


@router.callback_query(F.data.startswith('atask_'))
async def process_assigned_task(
        query: types.CallbackQuery,
        support_engineer: SupportEngineer,
        state: FSMContext,
):
    logger.info('Назначить задачу на сотрудника')
    task_id = query.data.split('_')[1]
    try:
        task = await SDTask.objects.by_id(task_id)
        available_to_assign = await support_engineer.get_available_to_assign()
        engineers_names = [engineer.name for engineer in available_to_assign]
        await state.update_data(
            task=task,
            engineers_on_shift=available_to_assign,
            task_applicant=task.new_applicant,
        )
        text, keyboard = await dialogs.request_choice_engineer_for_assign(
            engineers_names,
        )
        await query.message.answer(text, reply_markup=keyboard)
        await query.message.delete()
        await state.set_state(AssignedTaskState.task)
    except exceptions.TaskAssignedError as error:
        logger.debug('Задача %s назначена на сотрудника', task_id)
        await query.message.answer(error.message)
    except exceptions.NotAvailableToAssignError as assign_error:
        logger.debug('Нет подходящих инженеров для назначения')
        await query.message.answer(assign_error.message)


@router.message(AssignedTaskState.task)
async def process_assigned_task_step_2(
        message: types.Message,
        support_engineer: SupportEngineer,
        state: FSMContext,
):
    logger.info('Назначения задачи на инженера шаг 2')
    selected_engineer_name = message.text
    data = await state.get_data()
    task_id = data['task'].id
    engineers_on_shift = data['engineers_on_shift']
    try:
        selected_engineer = await Service.select_engineer_on_shift(
            selected_engineer_name,
            engineers_on_shift,
        )
        task = await support_engineer.assigned_task(task_id, selected_engineer)
        logger.info(
            'Инженер %s назначен на задачу %s',
            selected_engineer.name,
            task.number,
        )
        await Message.send_assigned_task_notify(task, support_engineer)
    except exceptions.NoSelectedEngineerError as selected_error:
        await message.answer(
            selected_error.message,
            reply_markup=ReplyKeyboardRemove(),
        )
    except exceptions.TaskAssignedError as assigned_error:
        logger.debug('Задача %s назначена на сотрудника', task_id)
        await message.answer(
            assigned_error.message,
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await state.clear()


@router.message(Command('close_task'))
async def close_task(
        message: types.Message,
        support_engineer: SupportEngineer,
        state: FSMContext,
):
    logger.info('Запрос на закрытие задачи')
    try:
        task_numbers = await support_engineer.get_task_number_in_work()
        text, keyboard = await dialogs.request_task_for_close(task_numbers)
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(TaskState.close_task)
    except exceptions.TaskNotFoundError:
        logger.info('Закрытие задач. Нет задач в работе')
        await message.answer(await dialogs.error_not_tasks_in_work())


@router.message(
    TaskState.close_task,
    F.text.regexp(r'SD-(\d{5,7})+').as_('regexp'),
)
async def process_close_task(
        message: types.Message,
        support_engineer: SupportEngineer,
        regexp: re.Match[str],
        state: FSMContext,
):
    logger.info(f'Закрываем задачу: {regexp.group()}')
    task_number = regexp.group()
    task = await SDTask.objects.by_number(task_number)
    if task.new_performer.name != support_engineer.user.name:
        logger.warning('Исполнитель и закрывающий отличаются')
        await message.answer(
            await dialogs.error_wrong_task_performer(task.new_performer.name),
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    if task.support_group == 'DISPATCHER' and task.is_close_task_command:
        logger.info('Закрытие заявки созданной выездным по команде /close')
        await state.update_data(close_task=task, get_doc=eval(task.tg_docs))
        await message.answer(await dialogs.wait_load_documents())
        await Service.send_documents_out_task(task, dispatcher=False)
        text, keyboard = await dialogs.request_check_documents()
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(TaskState.doc_approved)
        return
    if task.support_group == 'DISPATCHER':
        logger.info('Старт процесса закрытия задачи диспетчером')
        text, keyboard = await dialogs.request_documents()
        await message.answer(text, reply_markup=keyboard)
        await state.update_data(close_task=task)
        await state.set_state(TaskState.get_doc)
        return
    if task.support_group == 'ENGINEER':
        task = await support_engineer.engineer_close_task(task.id)
        await Message.send_close_task_notify(task)
        await state.clear()


@router.message(TaskState.get_doc)
async def dispatcher_close_task_get_doc(
        message: types.Message,
        state: FSMContext,
        service: Service,
        album: dict,
):
    logger.info('Получение документов')
    if message.text and message.text.lower() == 'без документов':
        text, keyboard = await dialogs.without_documents()
        await message.answer(text, reply_markup=keyboard)
        await state.update_data(get_doc={})
        await state.set_state(TaskState.doc_approved)
        return
    tg_documents = await service.get_documents(message, album)
    if tg_documents.is_error:
        await message.answer(tg_documents.error_msg)
        return
    text, keyboard = await dialogs.confirmation_received_documents_disp(
        tg_documents.documents,
    )
    await message.answer(text, reply_markup=keyboard)
    await state.update_data(get_doc=tg_documents.documents)
    await state.set_state(TaskState.doc_approved)


@router.callback_query(TaskState.doc_approved, F.data == 'doc_apr_yes')
async def dispatcher_close_task_approved_doc_yes(
        query: types.CallbackQuery,
        state: FSMContext,
):
    await query.message.delete()
    text, keyboard = await dialogs.request_sub_tasks()
    await query.message.answer(text, reply_markup=keyboard)
    await state.set_state(TaskState.approved_sub_tasks)


@router.callback_query(TaskState.doc_approved, F.data == 'doc_apr_no')
async def dispatcher_close_task_approved_doc_no(
        query: types.CallbackQuery,
        state: FSMContext,
):
    await query.answer()
    await query.message.answer(await dialogs.retry_request_documents())
    await state.update_data(get_doc=State())
    await state.set_state(TaskState.get_doc)


@router.message(TaskState.approved_sub_tasks)
async def dispatcher_close_task_approved_sub_tasks(
        message: types.Message,
        state: FSMContext,
):
    logger.debug('Получение и проверка дочерних обращений')
    sub_tasks = []
    if message.text.lower() != 'нет':
        sub_tasks = re.findall(r'([a-zA-Z]{2,3}\S?[0-9]{7})+', message.text)
        if not sub_tasks:
            await message.answer(await dialogs.wrong_task_number())
            return
    await state.update_data(approved_sub_tasks=sub_tasks)
    await message.answer(
        await dialogs.request_task_close_commit(),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(TaskState.task_comment)


@router.message(TaskState.task_comment)
async def dispatcher_close_task_comment(
        message: types.Message,
        state: FSMContext,
):
    data = await state.get_data()
    docs_names = ', '.join(data['get_doc'].keys())
    text, keyboard = await dialogs.close_task_request_approved(
        docs_names,
        data['close_task'].number,
        data['approved_sub_tasks'],
        message.text,
    )
    await state.update_data(task_comment=message.text)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(TaskState.approved_close_tasks)


@router.callback_query(
    TaskState.approved_close_tasks,
    F.data == 'apr_close_task',
)
async def dispatcher_close_task_approved(
        query: types.CallbackQuery,
        support_engineer: SupportEngineer,
        state: FSMContext,
):
    logger.info('Старт закрытия задачи диспетчером')
    await query.message.delete()
    data = await state.get_data()
    task: SDTask = data['close_task']
    task = await support_engineer.dispatcher_close_task(
        task.id,
        task.number,
        data['approved_sub_tasks'],
        data['get_doc'],
        data['task_comment']
    )
    await Message.send_close_task_notify(task)
    await state.clear()


@router.message(Command('my_active_tasks'))
async def get_employee_active_tasks(
        message: types.Message,
        support_engineer: SupportEngineer,
):
    try:
        tasks = await support_engineer.get_task_in_work()
        file_to_send = await Service.prepare_tasks_as_file_for_send(
            'Ваши задачи в работе',
            tasks,
            'tasks.txt',
        )
        await message.answer_document(
            file_to_send,
            caption='Задачи в работе',
        )
    except exceptions.TaskNotFoundError as error:
        await message.answer(error.message)


@router.message(Command('new_tasks'))
async def get_new_tasks(
        message: types.Message,
):
    tasks = await SDTask.objects.get_not_assign_task()
    logger.debug('Список найденных новых задач: %s', tasks)
    if not tasks:
        await message.answer('Нет новый задач')
        return
    file_to_send = await Service.prepare_tasks_as_file_for_send(
        'Новые задачи',
        tasks,
        'new_tasks.txt',
    )
    await message.answer_document(
        file_to_send,
        caption='Не назначенные задачи',
    )
