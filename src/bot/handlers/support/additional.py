import re
import logging

from aiogram import F
from aiogram import Router
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder

from django.utils import timezone
from django.conf import settings

from src.models import SDTask

logger = logging.getLogger('support_bot')
router = Router(name='additional_handlers')


@router.callback_query(F.data == 'additional')
async def process_additional_work(
        query: types.CallbackQuery,
        state: FSMContext,
):
    logger.info('Обработчик передачи заявки на доп работы')
    await query.answer()
    data = await state.get_data()
    task: SDTask = data['close_task']
    docs = data['get_doc']
    gsd_number = re.search(r'\d{7}', task.title)
    if not gsd_number:
        logger.warning('Не смог найти номер в имени %s', task.title)
        logger.info('Поиск номера задачи в описании')
        gsd_number = re.search(r'\d{7}', task.description)
        if not gsd_number:
            logger.warning('не смог найти номер заявки GSD в теме и описании')
            await query.message.answer('Не смог найти номер обращения')
            return
    await query.message.delete()
    gsd_number = gsd_number[0]
    logger.info('Отправляю сообщение в чат доп работ')
    await query.bot.send_message(
        settings.TG_ADDITIONAL_CHAT_ID,
        f'Заявка <code>SC-{gsd_number}</code> относится '
        f'к доп работам/ремонтам\n'
        f'Закрывается на Вашей линии',
    )
    media_group = MediaGroupBuilder(caption='Приложенные документы')
    for doc_name, doc_id in docs.items():
        tg_file = await query.bot.get_file(doc_id)
        io_file = await query.bot.download_file(tg_file.file_path)
        text_file = types.BufferedInputFile(io_file.read(), filename=doc_name)
        media_group.add_document(text_file)
    await query.bot.send_media_group(
        chat_id=settings.TG_ADDITIONAL_CHAT_ID,
        media=media_group.build()
    )
    logger.info('Отправил')
    logger.info('Закрывая заявку в БД')
    task.status = 'COMPLETED'
    task.closing_comment = 'Передана на группу по доп работам/ремонтам'
    task.finish_at = timezone.now()
    await task.asave()
    logger.info('Заявка закрыта')
    await query.message.answer(
        'Передал информацию в группу доп/рем работ',
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.clear()
    logger.info('Работа обработчика завершена')
