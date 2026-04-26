"""
cita.me — Cliente Redis async y locking distribuido.
Redis previene condiciones de carrera al reservar citas concurrentemente.
"""
import asyncio
import json
import logging
import redis.asyncio as redis
from config import REDIS_URL, LOCK_TIMEOUT_SECONDS, LOCK_WAIT_SECONDS, CACHE_TTL

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    """Inicializar conexión async a Redis."""
    global redis_client
    redis_client = redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    await redis_client.ping()
    logger.info("[cita.me/REDIS] Conexión establecida")
    return redis_client


async def close_redis():
    """Cerrar conexión a Redis."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("[cita.me/REDIS] Conexión cerrada")


class DistributedLock:
    """
    Lock distribuido con Redis para cita.me.

    Uso:
        lock = DistributedLock("cita:doctor_5:2025-01-15:10:00")
        if await lock.acquire():
            try:
                # operación crítica
            finally:
                await lock.release()
    """

    def __init__(self, resource_key: str, timeout: int = LOCK_TIMEOUT_SECONDS):
        self.redis = redis_client
        self.lock_key = f"lock:citame:{resource_key}"
        self.timeout = timeout
        self._lock = None

    async def acquire(self, wait_timeout: int = LOCK_WAIT_SECONDS) -> bool:
        """Intentar adquirir el lock."""
        if not self.redis:
            logger.warning("[cita.me/REDIS] Sin conexión, lock no disponible")
            return False

        self._lock = self.redis.lock(
            self.lock_key,
            timeout=self.timeout,
            blocking_timeout=wait_timeout,
        )
        try:
            acquired = await self._lock.acquire()
            if acquired:
                logger.info("[cita.me/LOCK] Adquirido: %s", self.lock_key)
            else:
                logger.warning("[cita.me/LOCK] Timeout: %s", self.lock_key)
            return acquired
        except Exception as e:
            logger.error("[cita.me/LOCK] Error: %s", e)
            return False

    async def release(self):
        """Liberar el lock."""
        if self._lock and self.redis:
            try:
                await self._lock.release()
                logger.info("[cita.me/LOCK] Liberado: %s", self.lock_key)
            except Exception as e:
                logger.error("[cita.me/LOCK] Error liberando: %s", e)


async def cache_get(key: str) -> dict | None:
    """Obtener valor del cache."""
    if not redis_client:
        return None
    try:
        data = await redis_client.get(key)
        if data:
            logger.debug("[cita.me/CACHE] Hit: %s", key)
            return json.loads(data)
        logger.debug("[cita.me/CACHE] Miss: %s", key)
        return None
    except Exception as e:
        logger.error("[cita.me/CACHE] Error get: %s", e)
        return None


async def cache_set(key: str, value: dict, ttl: int = CACHE_TTL):
    """Guardar valor en cache."""
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
        logger.debug("[cita.me/CACHE] Set: %s (TTL=%ds)", key, ttl)
    except Exception as e:
        logger.error("[cita.me/CACHE] Error set: %s", e)


async def cache_delete(pattern: str):
    """Eliminar claves por patrón."""
    if not redis_client:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.debug("[cita.me/CACHE] Eliminadas %d: %s", len(keys), pattern)
    except Exception as e:
        logger.error("[cita.me/CACHE] Error delete: %s", e)