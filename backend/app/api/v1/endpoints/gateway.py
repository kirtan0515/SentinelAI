"""
Gateway management endpoints.
Provides administrative tools for the AI gateway.
"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.gateway.rate_limiter import RateLimiter
from app.gateway.router import GatewayRouter
from app.guardrails.manager import GuardrailsManager
from app.models.user import User

router = APIRouter()


@router.get("/status")
async def gateway_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive gateway status.
    Shows provider health, rate limits, and guardrails status.
    """
    gateway = GatewayRouter()
    guardrails = GuardrailsManager()
    rate_limiter = RateLimiter()

    # Get rate limit usage for current user
    usage = await rate_limiter.get_usage(f"user:{current_user.id}")

    return {
        "gateway": {
            "providers": gateway.get_provider_health(),
            "total_models": len(gateway.get_available_models()),
        },
        "guardrails": await guardrails.get_status(),
        "rate_limits": usage,
    }


@router.get("/rate-limit")
async def get_rate_limit_status(
    current_user: User = Depends(get_current_user),
):
    """Get current user's rate limit usage."""
    rate_limiter = RateLimiter()
    usage = await rate_limiter.get_usage(f"user:{current_user.id}")
    return usage
