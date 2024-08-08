from aiogram import Router

from src.bot.middlewares import AlbumMiddleware

from .on_shift import router as on_shift_router
from .break_shift import router as break_shift_router
from .end_shift import router as end_shift_router
from .tasks import router as support_router
from .field_engineers import router as field_engineers_router
from .managerial import router as managerial_router
from .additional import router as additional_router
from .sber_engineer import router as sber_engineer_router


router = Router(name='support_handlers')
router.message.outer_middleware(AlbumMiddleware())
router.include_router(on_shift_router)
router.include_router(break_shift_router)
router.include_router(end_shift_router)
router.include_router(support_router)
router.include_router(additional_router)
router.include_router(field_engineers_router)
router.include_router(sber_engineer_router)
router.include_router(managerial_router)
