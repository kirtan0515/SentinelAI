"""
Redis Caching Utility

Provides a high-level caching interface with TTL support, a decorator
for caching endpoint responses, and cache invalidation patterns.
"""

import functools
import hashlib
import json
import pickle
from typing import Any, Callable

import structlog
from redis.asyncio import Redis

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Default TTL values (in seconds)
DEFAULT_TTL = 300  # 5 minutes
SHORT_TTL = 60  # 1 minute
LONG_TTL = 3600  # 1 hour


class CacheManager:
    """
    Redis-based cache manager with get/set, TTL, and invalidation support.

    Usage:
        cache = CacheManager()
        await cache.connect()

        # Basic get/set
        await cache.set("key", {"data": "value"}, ttl=300)
        result = await cache.get("key")

        # Invalidation
        await cache.delete("key")
        await cache.invalidate_pattern("user:*")
    """

    def __init__(self, redis_url: str | None = None, prefix: str = "sentinelai"):
        self._redis_url = redis_url or settings.REDIS_URL
        self._prefix = prefix
        self._redis: Redis | None = None

    async def connect(self) -> None:
        """Initialize Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info("Redis cache connected", url=self._redis_url)

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis cache disconnected")

    @property
    def redis(self) -> Redis:
        """Get Redis client, raising if not connected."""
        if self._redis is None:
            raise RuntimeError("Cache not connected. Call connect() first.")
        return self._redis

    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self._prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired.
        """
        try:
            full_key = self._make_key(key)
            data = await self.redis.get(full_key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """
        Set a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be picklable)
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise.
        """
        try:
            full_key = self._make_key(key)
            data = pickle.dumps(value)
            await self.redis.setex(full_key, ttl, data)
            return True
        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))
            return False

    async def get_json(self, key: str) -> dict | list | None:
        """Get a JSON-serializable value from cache."""
        try:
            full_key = self._make_key(key)
            data = await self.redis.get(full_key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.warning("Cache get_json failed", key=key, error=str(e))
            return None

    async def set_json(self, key: str, value: dict | list, ttl: int = DEFAULT_TTL) -> bool:
        """Set a JSON-serializable value in cache."""
        try:
            full_key = self._make_key(key)
            data = json.dumps(value)
            await self.redis.setex(full_key, ttl, data)
            return True
        except Exception as e:
            logger.warning("Cache set_json failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if it didn't exist.
        """
        try:
            full_key = self._make_key(key)
            result = await self.redis.delete(full_key)
            return result > 0
        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Glob pattern (e.g., "user:*", "model:config:*")

        Returns:
            Number of keys deleted.
        """
        try:
            full_pattern = self._make_key(pattern)
            count = 0
            async for key in self.redis.scan_iter(match=full_pattern, count=100):
                await self.redis.delete(key)
                count += 1
            if count > 0:
                logger.info("Cache invalidated", pattern=pattern, count=count)
            return count
        except Exception as e:
            logger.warning("Cache invalidation failed", pattern=pattern, error=str(e))
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            full_key = self._make_key(key)
            return bool(await self.redis.exists(full_key))
        except Exception:
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for a key in seconds. Returns -2 if key doesn't exist."""
        try:
            full_key = self._make_key(key)
            return await self.redis.ttl(full_key)
        except Exception:
            return -2


# Global cache instance
cache = CacheManager()


def cached(
    ttl: int = DEFAULT_TTL,
    key_prefix: str = "",
    key_builder: Callable | None = None,
):
    """
    Decorator for caching endpoint/function responses.

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for the cache key
        key_builder: Optional function to build a custom cache key

    Usage:
        @cached(ttl=300, key_prefix="models")
        async def get_models():
            return await expensive_query()

        @cached(ttl=60, key_builder=lambda user_id: f"user:{user_id}:profile")
        async def get_user_profile(user_id: str):
            return await fetch_profile(user_id)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Auto-generate key from function name and arguments
                key_parts = [key_prefix or func.__module__, func.__name__]
                if args:
                    key_parts.append(
                        hashlib.md5(str(args).encode(), usedforsecurity=False).hexdigest()[:8]
                    )
                if kwargs:
                    key_parts.append(
                        hashlib.md5(
                            str(sorted(kwargs.items())).encode(), usedforsecurity=False
                        ).hexdigest()[:8]
                    )
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug("Cache hit", key=cache_key)
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            logger.debug("Cache miss, stored", key=cache_key, ttl=ttl)
            return result

        # Attach cache control methods to the wrapper
        wrapper.invalidate = lambda *a, **kw: cache.delete(
            key_builder(*a, **kw)
            if key_builder
            else f"{key_prefix or func.__module__}:{func.__name__}"
        )

        return wrapper

    return decorator
