from fastapi import APIRouter

from app.api import ai, hello, route

router = APIRouter(prefix="/api")
router.include_router(hello.router)
router.include_router(ai.router)
router.include_router(route.router)