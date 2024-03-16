import re
import logging

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from src.entities.Message import Message
from src.entities.Scheduler import Scheduler
from src.entities.FieldEngineer import FieldEngineer

from src.bot import dialogs
from src.bot import services
from src.models import SDTask
from src.models import Dispatcher
from src.models import CustomUser

logger = logging.getLogger('support_bot')
router = Router(name='field_engineers_handlers')


class NewTaskState(StatesGroup):
    support_group = State()
    get_gsd_number = State()
    descriptions = State()
    approved = State()


class CloseTaskState(StatesGroup):
    get_number = State()
    get_documents = State()
    documents_approved = State()


class DispatcherTask(StatesGroup):
    task = State()
    get_doc = State()


@router.message(Command('close'))
async def start_close_task(
        message: types.Message,
        employee: CustomUser,
        state: FSMContext,
):
    logger.info('Запрос на закрытие заявки от инженера %s', employee.name)
    await message.answer(await dialogs.required_task_number())
    await state.set_state(CloseTaskState.get_number)


@router.message(CloseTaskState.get_number)
async def process_get_number(message: types.Message, state: FSMContext):
    logger.info('Закрытие заявки. Обработка номера задачи')
    task_number = re.match(r'([a-zA-Z]{2,3}\S?[0-9]{7})+', message.text)
    if not task_number:
        logger.warning('Не правильный номер задачи')
        await message.answer(await dialogs.wrong_task_number())
        return
    await state.update_data(get_number=task_number.group())
    await message.answer(await dialogs.required_documents())
    await state.set_state(CloseTaskState.get_documents)
    logger.info('Обработано')


@router.message(CloseTaskState.get_documents)
async def process_close_task_get_documents(
        message: types.Message,
        state: FSMContext,
        album: dict,
):
    tg_documents = await services.get_documents(message, album)
    if tg_documents.is_error:
        await message.answer(tg_documents.error_msg)
        return
    text, keyboard = await dialogs.confirmation_received_documents(
        tg_documents.documents,
    )
    await message.answer(text, reply_markup=keyboard)
    await state.update_data(get_documents=tg_documents.documents)
    await state.set_state(CloseTaskState.documents_approved)


@router.callback_query(
    CloseTaskState.documents_approved,
    F.data == 'uni_yes',
)
async def process_close_task_approved_doc_yes(
        query: types.CallbackQuery,
        field_engineer: FieldEngineer,
        scheduler: Scheduler,
        state: FSMContext,
):
    logger.info('Создание заявки на закрытие. Финальный этап')
    await query.message.edit_text(await dialogs.waiting_creating_task())
    data = await state.get_data()
    logger.debug('state_data: %s', data)
    task = await field_engineer.create_sd_task_to_close(
        data["get_number"],
        data["get_documents"],
    )
    await scheduler.add_new_task_schedulers(task)
    await Message.send_new_task_notify(task)
    edit_text = await dialogs.new_task_notify_for_creator(
        task.number,
        task.title,
    )
    await query.message.edit_text(edit_text)
    await state.clear()
    logger.info('Процесс завершен')


@router.callback_query(
    CloseTaskState.documents_approved,
    F.data == 'uni_no',
)
async def process_close_task_approved_doc_no(
        query: types.CallbackQuery,
        state: FSMContext,
):
    logger.info('Не уверен в документах, просим еще раз')
    await query.message.edit_text(await dialogs.required_documents())
    await state.update_data(get_documents={})
    await state.set_state(CloseTaskState.get_documents)
    logger.info('Процесс завершен')


@router.message(Command('support_help'))
async def start_new_support_task(message: types.Message, state: FSMContext):
    logger.info('Запрос на создание новой выездной задачи')
    text, keyboard = await dialogs.support_help_whose_help_is_needed()
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(NewTaskState.support_group)


@router.callback_query(
    NewTaskState.support_group,
    F.data.startswith('engineer') | F.data.startswith('dispatcher')
)
async def new_task_engineer(query: types.CallbackQuery, state: FSMContext):
    logger.info('support_help_step_2')
    await query.message.delete()
    await state.update_data(support_group=query.data)
    await query.message.answer(await dialogs.required_task_number())
    await state.set_state(NewTaskState.get_gsd_number)


@router.message(NewTaskState.get_gsd_number)
async def process_get_gsd_number(message: types.Message, state: FSMContext):
    logger.info('Обработка номера задачи от инженера')
    task_number = re.match(r'([a-zA-Z]{2,3}\S?[0-9]{7})+', message.text)
    if not task_number:
        logger.warning('Не правильный номер задачи')
        await message.answer(await dialogs.wrong_task_number())
        return
    await state.update_data(get_gsd_number=task_number.group())
    await message.answer(await dialogs.request_task_description())
    await state.set_state(NewTaskState.descriptions)
    logger.info('Обработано')


@router.message(NewTaskState.descriptions)
async def process_task_descriptions(message: types.Message, state: FSMContext):
    logger.info('Получение описания по задаче')
    task_description = message.text
    if not task_description:
        await message.answer(await dialogs.error_wrong_task_description())
        return
    data = await state.get_data()
    task_number = data['get_gsd_number']
    await state.update_data(descriptions=task_description)
    text, keyboard = await dialogs.request_task_confirmation(
        task_number,
        task_description,
    )
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(NewTaskState.approved)
    logger.info('Описание получено')


@router.callback_query(F.data.startswith('approved_new_task'))
async def process_task_approved(
        query: types.CallbackQuery,
        field_engineer: FieldEngineer,
        scheduler: Scheduler,
        state: FSMContext,
):
    logger.info('Процесс подтверждения и создания новой заявки')
    await query.message.edit_text(await dialogs.waiting_creating_task())
    data = await state.get_data()
    logger.debug('state_data: %s', data)
    task = await field_engineer.create_sd_task_to_help(
        data['get_gsd_number'],
        data['support_group'],
        data['descriptions'],
    )
    await scheduler.add_new_task_schedulers(task)
    await Message.send_new_task_notify(task)
    edit_text = await dialogs.new_task_notify_for_creator(
        task.number,
        task.title,
    )
    await query.message.edit_text(edit_text)
    await state.clear()
    logger.info('Процесс завершен')


@router.callback_query(F.data.startswith('rating_'))
async def task_feedback(query: types.CallbackQuery):
    logger.info('Оценка задачи')
    rating = query.data.split('_')[1]
    task_id = query.data.split('_')[2]
    task = await SDTask.objects.aget(id=task_id)
    task.rating = int(rating)
    await task.asave()
    try:
        await query.message.delete()
        await query.message.answer(await dialogs.rating_feedback(task.number))
    except TelegramBadRequest:
        logger.debug('Сообщение уже удалено')
    logger.info('Оценка проставлена')


@router.callback_query(F.data.startswith('disp_task_'))
async def process_dispatchers_task(
        query: types.CallbackQuery,
        employee: CustomUser,
        state: FSMContext,
):
    logger.info(
        'Создание заявки на закрытие в GSD из диспетчера от выездного %s',
        employee.name,
    )
    task_id = query.data.split('_')[2]
    logger.debug('Получение информации о задаче из базы')
    try:
        task = await Dispatcher.objects.aget(id=task_id)
    except Dispatcher.DoesNotExist:
        logger.warning('Не нашел задачу с id %s в базе', task_id)
        await query.message.answer(await dialogs.error_task_not_found())
        await query.message.delete()
        return
    await query.message.answer(await dialogs.required_documents())
    await query.message.delete()
    await state.set_state(DispatcherTask.get_doc)
    await state.update_data(task=task)


@router.message(DispatcherTask.get_doc)
async def process_dispatchers_task_get_doc(
        message: types.Message,
        field_engineer: FieldEngineer,
        scheduler: Scheduler,
        state: FSMContext,
        album: dict,
):
    logger.info('Получение документов от выездного')
    data = await state.get_data()
    task: Dispatcher = data['task']
    tg_documents = await services.get_documents(message, album)
    if tg_documents.is_error:
        await message.answer(tg_documents.error_msg)
        return

    task.tg_documents = tg_documents.documents
    await task.asave()
    logger.info('Процесс подтверждения и создания новой заявки')
    send_message = await message.answer(await dialogs.waiting_creating_task())
    description = (
        'Закрыть заявку во внешней системе\n\n'
        '<b>Связанные задачи GSD:</b> <code>{gsd_numbers}</code>\n'
        '<b>Связанные задачи SimpleOne:</b> <code>{simple_one}</code>\n'
        '<b>Связанные задачи ITSM:</b> <code>{itsm}</code>\n\n'
        '<u><b>Комментарий закрытия от инженера:</b></u>\n{task_commit}'
    )
    description = description.format(
        number=task.dispatcher_number,
        gsd_numbers=task.gsd_numbers,
        simple_one=task.simpleone_number,
        itsm=task.itsm_number,
        task_commit=task.closing_comment,
    )
    sd_task = await field_engineer.create_task_closing_from_dispatcher(
        str(task.dispatcher_number),
        description,
        tg_documents.documents,
    )
    await scheduler.add_new_task_schedulers(sd_task)
    await Message.send_new_task_notify(sd_task)
    text = await dialogs.new_task_notify_for_creator(
        sd_task.number,
        sd_task.title,
    )
    await send_message.edit_text(text)
    await state.clear()
    logger.info('Процесс завершен')
