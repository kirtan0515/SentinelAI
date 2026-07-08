"""
Rate Limiting Middleware

Integrates the Redis-based rate limiter into the FastAPI request pipeline.
Applies limits per IP for unauthenticated requests and per user for authenticated.
"""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.gateway.rate_limiter import RateLimiter

logger = structlog.get_logger(__name__)

# Paths exempt from rate limiting
EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/",
}


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    HTTP middleware that enforces rate limits on API requests.

    Rate limits are applied based on:
    - IP address (for all requests)
    - User ID (for authenticated requests, from JWT)

    Exempt paths (health, docs) are not rate-limited.
    """

    def __init__(self, app):
        super().__init__(app)
        self._limiter = RateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Check rate limits before processing the request."""
        # Skip rate limiting for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Determine identifier (prefer user ID from token, fall back to IP)
        identifier = self._get_identifier(request)

        # Check rate limit
        result = await self._limiter.check_rate_limit(identifier)

        if not result.allowed:
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                path=request.url.path,
                retry_after=result.retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after_seconds": round(result.retry_after or 60, 1),
                },
                headers={
                    "Retry-After": str(int(result.retry_after or 60)),
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))

        return response

    def _get_identifier(self, request: Request) -> str:
        """
        Extract rate limit identifier from request.

        Priority:
        1. User ID from Authorization header (if valid JWT)
        2. Client IP address
        """
        # Try to extract user from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from app.core.security import decode_token

                payload = decode_token(token)
                if payload and "sub" in payload:
                    return f"user:{payload['sub']}"
            except Exception:
                pass

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"

        # Check for forwarded IP (behind reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        return f"ip:{client_ip}"
