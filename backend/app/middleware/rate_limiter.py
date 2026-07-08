"""
Rate limiting middleware.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis.
    Limits requests per IP and per user.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter."""
        # TODO: Implement Redis-based rate limiting
        # For now, pass through all requests
        response = await call_next(request)
        return response
