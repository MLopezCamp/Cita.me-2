import redis.asyncio as redis
from contextlib import asynccontextmanager
from ..config import config

redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

@asynccontextmanager
async def redis_lock(lock_name: str, expire_seconds: int = config.LOCK_EXPIRE_SECONDS):
    acquired = await redis_client.setnx(lock_name, "locked")
    if acquired:
        await redis_client.expire(lock_name, expire_seconds)
        try:
            yield True
        finally:
            await redis_client.delete(lock_name)
    else:
        yield False