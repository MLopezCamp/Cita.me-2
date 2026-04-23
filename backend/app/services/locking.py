import redis.asyncio as redis
from contextlib import asynccontextmanager
from app.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

@asynccontextmanager
async def distributed_lock(lock_name: str, expire_time: int = 10):
    lock_acquired = await redis_client.setnx(lock_name, "locked")
    if lock_acquired:
        await redis_client.expire(lock_name, expire_time)
        try:
            yield True
        finally:
            await redis_client.delete(lock_name)
    else:
        yield False