"""
AI Model management endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.repositories.model_repository import ModelRepository

router = APIRouter()


@router.get("/")
async def list_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available AI models."""
    model_repo = ModelRepository(db)
    models = await model_repo.get_enabled()
    return models


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """List supported AI providers."""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-sonnet", "claude-3-haiku"]},
            {"id": "google", "name": "Google", "models": ["gemini-pro", "gemini-pro-vision"]},
            {"id": "ollama", "name": "Ollama (Local)", "models": ["llama2", "mistral", "codellama"]},
        ]
    }


@router.put("/{model_id}/default")
async def set_default_model(
    model_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Set the default AI model (admin only)."""
    model_repo = ModelRepository(db)
    model = await model_repo.set_default(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    return {"message": f"Default model set to {model.display_name}"}
