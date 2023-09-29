from aiogram import Router
from .common import router as common_router
from .scan_chats import router as scan_chats_router


router = Router(name='main_handlers_router')
router.include_router(common_router)
router.include_router(scan_chats_router)
