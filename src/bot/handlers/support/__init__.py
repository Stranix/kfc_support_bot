from aiogram import Router

from .on_shift import router as on_shift_router
from .break_shift import router as break_shift_router
from .end_shift import router as end_shift_router

router = Router(name='support_handlers')
router.include_router(on_shift_router)
router.include_router(break_shift_router)
router.include_router(end_shift_router)
