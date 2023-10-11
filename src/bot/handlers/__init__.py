from aiogram import Router
from .common import router as common_router
from .scan_chats import router as scan_chats_router
from .synchronizations import router as sync_router
from .support import router as support_router
from .schedulers import router as scheduler_router


router = Router(name='main_handlers_router')
router.include_router(common_router)
router.include_router(support_router)
router.include_router(scan_chats_router)
router.include_router(sync_router)
router.include_router(scheduler_router)
