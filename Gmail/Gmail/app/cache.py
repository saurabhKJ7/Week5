from __future__ import annotations

import hashlib
from typing import Optional

import redis

from .config import get_settings

settings = get_settings()


class RedisCache:
    def __init__(self):
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def _key(self, query: str) -> str:
        return "email_cache:" + hashlib.sha256(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[str]:
        return self.client.get(self._key(query))

    def set(self, query: str, response: str):
        self.client.setex(self._key(query), settings.cache_ttl_seconds, response) 