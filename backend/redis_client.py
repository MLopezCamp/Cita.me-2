"""
cita.me — Cliente Redis async, locking distribuido y cache.
"""
import logging
import json
import redis.asyncio as redis
from config import REDIS_URL, LOCK_TIMEOUT_SECONDS, LOCK_WAIT_SECONDS, CACHE_TTL

logger = logging.getLogger("redis")

redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    global redis_client
    redis_client = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    await redis_client.ping()
    logger.info("[REDIS] Conexion establecida")
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("[REDIS] Conexion cerrada")


class DistributedLock:
    """Lock distribuido con Redis."""

    def __init__(self, resource_key: str, timeout: int = LOCK_TIMEOUT_SECONDS, request_id: str = "-"):
        self.redis = redis_client
        self.lock_key = f"lock:citame:{resource_key}"
        self.timeout = timeout
        self._lock = None
        self.request_id = request_id

    async def acquire(self, wait_timeout: int = LOCK_WAIT_SECONDS) -> bool:
        if not self.redis:
            return False
        self._lock = self.redis.lock(
            self.lock_key,
            timeout=self.timeout,
            blocking_timeout=wait_timeout,
        )
        try:
            acquired = await self._lock.acquire()
            if acquired:
                logger.info("[REDIS] [%s] Lock adquirido: %s", self.request_id, self.lock_key)
            else:
                logger.warning("[REDIS] [%s] Lock NO adquirido (timeout): %s", self.request_id, self.lock_key)
            return acquired
        except Exception as e:
            logger.error("[REDIS] [%s] Error acquire: %s — %s", self.request_id, self.lock_key, e)
            return False

    async def release(self):
        if self._lock and self.redis:
            try:
                await self._lock.release()
                logger.info("[REDIS] [%s] Lock liberado: %s", self.request_id, self.lock_key)
            except Exception as e:
                logger.error("[REDIS] [%s] Error release: %s", self.request_id, e)


async def cache_get(key: str, request_id: str = "-") -> dict | None:
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        if data:
            logger.debug("[REDIS] [%s] Cache hit: %s", request_id, key)
            return json.loads(data) if data else None
        return None
    except Exception:
        return None


async def cache_set(key: str, value: dict, ttl: int = CACHE_TTL, request_id: str = "-"):
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass


async def cache_delete(pattern: str, request_id: str = "-"):
    if not redis_client:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.debug("[REDIS] [%s] Cache invalidado: %s (%d keys)", request_id, pattern, len(keys))
    except Exception:
        pass