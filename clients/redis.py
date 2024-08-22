from functools import lru_cache
from os import environ
from typing import AsyncGenerator

from aioredis import Redis, from_url


async def get_async_redis_client() -> AsyncGenerator[Redis, None]:
    yield from_url(
        environ.get("REDIS_URI", "redis://localhost:6379"), db=environ.get("REDIS_DB", 0), decode_responses=True
    )


@lru_cache()
def retrieve_async_redis_client() -> Redis:
    return from_url(
        environ.get("REDIS_URI", "redis://localhost:6379"), db=environ.get("REDIS_DB", 0), decode_responses=True
    )
