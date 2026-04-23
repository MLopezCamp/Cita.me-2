from celery import Celery
from app.config import settings

celery_app = Celery(
    "cita_medica",
    broker=settings.redis_url,
    backend=settings.rabbitmq_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_track_started=True,
)