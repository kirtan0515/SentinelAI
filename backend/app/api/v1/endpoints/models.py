"""
AI Model management endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.gateway.router import GatewayRouter
from app.models.user import User
from app.repositories.model_repository import ModelRepository

router = APIRouter()


@router.get("/")
async def list_models(
    current_user: User = Depends(get_current_user),
):
    """
    List all available AI models with metadata.
    Includes provider, pricing, capabilities, and availability.
    """
    gateway = GatewayRouter()
    models = gateway.get_available_models()
    return {"models": models, "total": len(models)}


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """List supported AI providers and their health status."""
    gateway = GatewayRouter()
    health = gateway.get_provider_health()

    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "status": health.get("openai", "unknown"),
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "status": health.get("anthropic", "unknown"),
            },
            {
                "id": "google",
                "name": "Google",
                "models": ["gemini-pro", "gemini-pro-vision"],
                "status": health.get("google", "unknown"),
            },
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "models": ["llama2", "llama3", "mistral", "codellama"],
                "status": health.get("ollama", "unknown"),
            },
        ]
    }


@router.get("/health")
async def provider_health(
    current_user: User = Depends(get_current_user),
):
    """Get real-time health status of all AI providers."""
    gateway = GatewayRouter()
    return {
        "circuit_breaker_states": gateway.get_provider_health(),
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
