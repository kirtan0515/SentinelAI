"""
Rate Limiter

Redis-backed sliding window rate limiter.
Supports per-user and per-IP rate limiting with configurable windows.
"""

import time
from typing import Optional, Tuple

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RateLimitResult:
    """Result of a rate limit check."""

    def __init__(
        self,
        allowed: bool,
        limit: int,
        remaining: int,
        reset_at: float,
        retry_after: Optional[float] = None,
    ):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        self.retry_after = retry_after


class RateLimiter:
    """
    Redis-backed sliding window rate limiter.

    Provides two levels of rate limiting:
    - Per minute (burst protection)
    - Per hour (sustained load protection)
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._per_minute = settings.RATE_LIMIT_PER_MINUTE
        self._per_hour = settings.RATE_LIMIT_PER_HOUR

    async def _get_redis(self):
        """Lazy-initialize Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning("Redis unavailable for rate limiting", error=str(e))
                return None
        return self._redis

    async def check_rate_limit(
        self,
        identifier: str,
        limit_per_minute: Optional[int] = None,
        limit_per_hour: Optional[int] = None,
    ) -> RateLimitResult:
        """
        Check if the identifier is within rate limits.

        Args:
            identifier: User ID, IP address, or API key
            limit_per_minute: Override per-minute limit
            limit_per_hour: Override per-hour limit

        Returns:
            RateLimitResult indicating if the request is allowed
        """
        redis = await self._get_redis()

        # If Redis is unavailable, allow the request (fail open)
        if redis is None:
            return RateLimitResult(
                allowed=True,
                limit=self._per_minute,
                remaining=self._per_minute,
                reset_at=time.time() + 60,
            )

        per_minute = limit_per_minute or self._per_minute
        per_hour = limit_per_hour or self._per_hour

        now = time.time()

        # Check minute window
        minute_key = f"ratelimit:minute:{identifier}"
        minute_result = await self._sliding_window_check(redis, minute_key, per_minute, 60, now)

        if not minute_result[0]:
            return RateLimitResult(
                allowed=False,
                limit=per_minute,
                remaining=0,
                reset_at=minute_result[1],
                retry_after=minute_result[1] - now,
            )

        # Check hour window
        hour_key = f"ratelimit:hour:{identifier}"
        hour_result = await self._sliding_window_check(redis, hour_key, per_hour, 3600, now)

        if not hour_result[0]:
            return RateLimitResult(
                allowed=False,
                limit=per_hour,
                remaining=0,
                reset_at=hour_result[1],
                retry_after=hour_result[1] - now,
            )

        # Request allowed
        remaining = min(
            per_minute - minute_result[2],
            per_hour - hour_result[2],
        )

        return RateLimitResult(
            allowed=True,
            limit=per_minute,
            remaining=max(0, remaining - 1),
            reset_at=now + 60,
        )

    async def _sliding_window_check(
        self,
        redis,
        key: str,
        limit: int,
        window_seconds: int,
        now: float,
    ) -> Tuple[bool, float, int]:
        """
        Sliding window rate limit check using Redis sorted sets.

        Returns:
            Tuple of (allowed, reset_time, current_count)
        """
        window_start = now - window_seconds

        # Use a pipeline for atomicity
        pipe = redis.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current entries in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry on the key
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]

        reset_time = now + window_seconds

        if current_count >= limit:
            # Over limit - remove the entry we just added
            await redis.zrem(key, str(now))
            return (False, reset_time, current_count)

        return (True, reset_time, current_count + 1)

    async def get_usage(self, identifier: str) -> dict:
        """Get current usage stats for an identifier."""
        redis = await self._get_redis()
        if redis is None:
            return {"minute": 0, "hour": 0}

        now = time.time()

        minute_key = f"ratelimit:minute:{identifier}"
        hour_key = f"ratelimit:hour:{identifier}"

        pipe = redis.pipeline()
        pipe.zcount(minute_key, now - 60, now)
        pipe.zcount(hour_key, now - 3600, now)
        results = await pipe.execute()

        return {
            "minute": {
                "used": results[0],
                "limit": self._per_minute,
                "remaining": max(0, self._per_minute - results[0]),
            },
            "hour": {
                "used": results[1],
                "limit": self._per_hour,
                "remaining": max(0, self._per_hour - results[1]),
            },
        }
