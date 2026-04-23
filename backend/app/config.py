import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost/citamedica")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = RABBITMQ_URL
    LOCK_EXPIRE_SECONDS = 10

config = Config()