"""
Thread-safe in-memory metadata and schema cache with TTL and freshness tracking.
"""
from typing import Dict, Any, Optional
import time
from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    key: str
    data: Any
    created_at: float = Field(default_factory=time.time)
    ttl_seconds: float = 300.0  # default 5 minutes

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class MetadataCache:
    """
    In-memory cache for schema, table, and profiling metadata.
    """

    def __init__(self, default_ttl_seconds: float = 300.0):
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            del self._cache[key]
            return None
        return entry.data

    def set(self, key: str, data: Any, ttl_seconds: Optional[float] = None) -> None:
        self._cache[key] = CacheEntry(
            key=key,
            data=data,
            ttl_seconds=ttl_seconds or self.default_ttl,
        )

    def invalidate(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

    def get_freshness(self, key: str) -> Optional[float]:
        """Returns age in seconds of the cached key, or None if not cached."""
        entry = self._cache.get(key)
        if entry is None or entry.is_expired:
            return None
        return entry.age_seconds
