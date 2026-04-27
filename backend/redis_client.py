"""
cita.me — Cliente Redis async, locking distribuido y coordinacion.

Funcionalidades:
- DistributedLock: Wrapper de redis.lock para compatibilidad
- Locking explícito: set_lock_raw() con SET NX EX
- Semaforo distribuido: acquire_semaphore() / release_semaphore()
- Cache: cache_get() / cache_set() / cache_delete()
- Coordinacion: check_service_health() / is_service_alive()
"""
import json
import logging
import redis.asyncio as redis
from config import REDIS_URL, LOCK_TIMEOUT_SECONDS, LOCK_WAIT_SECONDS, CACHE_TTL

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    """Inicializar conexion async a Redis."""
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
    """Cerrar conexion a Redis."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("[cita.me/REDIS] Conexión cerrada")


class DistributedLock:
    """Lock distribuido usando redis.lock (wrapper interno)."""

    def __init__(self, resource_key: str, timeout: int = LOCK_TIMEOUT_SECONDS):
        self.redis = redis_client
        self.lock_key = f"lock:citame:{resource_key}"
        self.timeout = timeout
        self._lock = None

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
                logger.info("[cita.me/LOCK] Adquirido: %s", self.lock_key)
            else:
                logger.warning("[cita.me/LOCK] Timeout: %s", self.lock_key)
            return acquired
        except Exception as e:
            logger.error("[cita.me/LOCK] Error: %s", e)
            return False

    async def release(self):
        if self._lock and self.redis:
            try:
                await self._lock.release()
                logger.info("[cita.me/LOCK] Liberado: %s", self.lock_key)
            except Exception as e:
                logger.error("[cita.me/LOCK] Error liberando: %s", e)


# ── Locking explicito con SET NX EX ──

async def set_lock_raw(key: str, value: str = "1", ttl: int = 30) -> bool:
    """Lock distribuido explicito: SET lock:citame:{key} {value} NX EX {ttl}."""
    if not redis_client:
        return False
    lock_key = f"lock:citame:{key}"
    try:
        result = await redis_client.set(lock_key, value, nx=True, ex=ttl)
        if result:
            logger.info("[cita.me/LOCK-RAW] SET NX EX exitoso: %s", lock_key)
        else:
            logger.warning("[cita.me/LOCK-RAW] Lock ya existe: %s", lock_key)
        return bool(result)
    except Exception as e:
        logger.error("[cita.me/LOCK-RAW] Error: %s", e)
        return False


# ── Semaforo distribuido ──

async def acquire_semaphore(resource: str, limit: int = 10, timeout: int = 30) -> bool:
    """Semaforo distribuido con INCR. Limita concurrencia por recurso."""
    if not redis_client:
        return False
    key = f"sem:citame:{resource}"
    try:
        actual = await redis_client.incr(key)
        if actual == 1:
            await redis_client.expire(key, timeout)
        if actual > limit:
            await redis_client.decr(key)
            return False
        logger.info("[cita.me/SEMAFORO] Adquirido: %s (%d/%d)", key, actual, limit)
        return True
    except Exception as e:
        logger.error("[cita.me/SEMAFORO] Error: %s", e)
        return False


async def release_semaphore(resource: str) -> None:
    """Liberar un slot del semaforo."""
    if not redis_client:
        return
    key = f"sem:citame:{resource}"
    try:
        await redis_client.decr(key)
        logger.info("[cita.me/SEMAFORO] Liberado: %s", key)
    except Exception as e:
        logger.error("[cita.me/SEMAFORO] Error liberando: %s", e)


# ── Coordinacion: heartbeats ──

async def check_service_health(service_name: str) -> bool:
    """Registrar heartbeat de un servicio en Redis (TTL 10s)."""
    if not redis_client:
        return False
    key = f"service:citame:{service_name}"
    try:
        await redis_client.set(key, "alive", ex=10)
        logger.info("[cita.me/COORD] Heartbeat: %s", service_name)
        return True
    except Exception as e:
        logger.error("[cita.me/COORD] Error heartbeat: %s", e)
        return False


async def is_service_alive(service_name: str) -> bool:
    """Verificar si un servicio esta activo via heartbeat."""
    if not redis_client:
        return False
    key = f"service:citame:{service_name}"
    try:
        val = await redis_client.exists(key)
        return bool(val)
    except Exception:
        return False


# ── Cache ──

async def cache_get(key: str) -> dict | None:
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
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
        logger.debug("[cita.me/CACHE] Set: %s (TTL=%ds)", key, ttl)
    except Exception as e:
        logger.error("[cita.me/CACHE] Error set: %s", e)


async def cache_delete(pattern: str):
    if not redis_client:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.debug("[cita.me/CACHE] Eliminadas %d: %s", len(keys), pattern)
    except Exception as e:
        logger.error("[cita.me/CACHE] Error delete: %s", e)