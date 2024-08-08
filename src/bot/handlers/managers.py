import re
import logging

from aiogram import types
from aiogram import Bot
from aiogram import Router
from aiogram.enums import ParseMode

from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link

from asgiref.sync import sync_to_async

from django.conf import settings

from src.models import BotCommand
from src.models import TGDeepLink
from src.models import CustomGroup
from src.entities.SupportEngineer import SupportEngineer

logger = logging.getLogger('support_bot')
router = Router(name='managers_handlers')


class DeepLinkState(StatesGroup):
    waiting_name = State()


@router.message(Command('create_deeplink'))
async def create_deeplink_start(
        message: types.Message,
        support_engineer: SupportEngineer,
        state: FSMContext,
):
    has_permission = await sync_to_async(
        support_engineer.user.has_perm
    )('auth.web_app')
    if not has_permission:
        await message.answer(
            'У вас нет прав на создание пригласительных ссылок',
        )
        return
    await message.answer(
        'Задайте ключевое слово ссылки'
        'Должно содержать только латиницу  от 3 до 5 букв',
    )
    await state.set_state(DeepLinkState.waiting_name)


@router.message(DeepLinkState.waiting_name)
async def create_deeplink_step_2(
        message: types.Message,
        support_engineer: SupportEngineer,
        state: FSMContext,
):
    deeplink_key = message.text
    if not deeplink_key or not re.match(r'([a-z]{3,5})+', deeplink_key):
        await message.answer(
            'Не правильной ключ. Попробуй еще раз'
            'Должно содержать только латиницу  от 3 до 5 букв',
        )
        return
    bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode=ParseMode.HTML)
    deeplink = await create_start_link(bot, deeplink_key, encode=True)
    await bot.session.close()
    logger.info('Создаю deeplink группу')
    group = await CustomGroup.objects.acreate(name=f'SBER_{deeplink_key}')
    await TGDeepLink.objects.acreate(
        deeplink_key=deeplink_key,
        deeplink=deeplink,
        group=group,
        user=support_engineer.user,
    )
    bot_command = await BotCommand.objects.prefetch_related(
        'new_groups',
    ).aget(
        name='/help_sber',
    )
    await sync_to_async(bot_command.new_groups.add)(group)
    await bot_command.asave()

    await message.answer(f'Пригласительная ссылка для Сбер:\n{deeplink}')
    await state.clear()
