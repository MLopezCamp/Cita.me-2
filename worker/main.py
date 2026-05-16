"""
cita.me — Worker standalone para procesar eventos RabbitMQ
"""
import asyncio
import logging
import sys
import os

# Añadir backend al path para importar módulos compartidos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from messaging.consumer import start_consumer
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger("worker")


async def main():
    logger.info("[INIT] Worker cita.me iniciando...")
    try:
        await start_consumer()
    except asyncio.CancelledError:
        logger.info("[SHUTDOWN] Worker detenido")
    except Exception as e:
        logger.error(f"[ERROR] Worker falló: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())