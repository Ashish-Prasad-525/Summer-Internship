from fastapi import APIRouter
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.debug import router as debug_router

router = APIRouter()
router.include_router(upload_router, prefix="/upload", tags=["Upload"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(documents_router, prefix="/documents", tags=["Documents"])
router.include_router(debug_router, prefix="/debug", tags=["Debug"])