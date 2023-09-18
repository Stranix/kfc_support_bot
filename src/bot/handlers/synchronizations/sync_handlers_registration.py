import logging

from aiogram import Dispatcher

from src.bot.handlers.synchronizations import sync_transits
from src.bot.handlers.synchronizations import sync_restaurants

logger = logging.getLogger('support_bot')


def register_handlers_sync(dp: Dispatcher):
    logger.info('Регистрация команд синхронизации')
    dp.register_message_handler(
        sync_transits.start,
        commands='sync_tr',
        state='*',
    )
    dp.register_message_handler(
        sync_restaurants.start,
        commands='sync_rest',
        state='*',
    )
    dp.register_callback_query_handler(
        sync_transits.choice,
        lambda call: call.data in ('yum', 'irb', 'fz', 'all'),
        state=sync_transits.SyncTrState,
    )
    dp.register_message_handler(
        sync_restaurants.sync_by_list,
        state=sync_restaurants.SyncRestState.waiting_rest_list,
    )
    dp.register_callback_query_handler(
        sync_restaurants.sync_by_group,
        state=sync_restaurants.SyncRestState.waiting_rest_group,
    )
    dp.register_callback_query_handler(
        sync_restaurants.choice,
        state=sync_restaurants.SyncRestState,
    )
