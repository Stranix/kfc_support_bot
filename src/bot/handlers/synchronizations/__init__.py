from aiogram import Router

from src.bot.middlewares.SyncMiddleware import SyncMiddleware

from .sync_report import router as report_router
from .sync_transits import router as tr_router
from .sync_restaurants import router as rest_router


router = Router(name='sync_handlers_router')
router.callback_query.middleware(SyncMiddleware())
router.include_router(tr_router)
router.include_router(rest_router)
router.include_router(report_router)
