"""
API v1 router - aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, documents, admin, audit, models, security, gateway, ws_chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chat"])
api_router.include_router(
    documents.router, prefix="/documents", tags=["Documents & RAG"]
)
api_router.include_router(
    security.router, prefix="/security", tags=["Security Engine"]
)
api_router.include_router(
    gateway.router, prefix="/gateway", tags=["AI Gateway"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(models.router, prefix="/models", tags=["AI Models"])
api_router.include_router(ws_chat.router, tags=["WebSocket Chat"])
