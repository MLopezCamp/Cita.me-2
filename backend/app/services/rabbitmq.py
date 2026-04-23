import aio_pika
from app.config import settings

async def get_rabbitmq_connection():
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return connection

async def publish_message(queue_name: str, message: dict):
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(body=str(message).encode()),
            routing_key=queue_name
        )