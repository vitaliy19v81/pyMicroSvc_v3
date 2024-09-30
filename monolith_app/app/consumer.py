import logging
import json
import os
import asyncio
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

from .database import AsyncSessionLocal
from .crud import mark_message_processed


def load_environment():
    env = os.getenv('ENVIRONMENT', 'dev')  # По умолчанию 'dev'
    if env == 'prod':
        load_dotenv('.env.prod')
    else:
        load_dotenv('.env.dev')

load_environment()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_consumer():
    consumer = AIOKafkaConsumer(
        'message_topic',
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    await consumer.start()
    logger.info("Kafka consumer успешно создан.")
    return consumer

async def wait_for_kafka_consumer():
    while True:
        try:
            # consumer = run_in_threadpool(create_consumer)
            consumer = await create_consumer()
            logger.info("Kafka consumer успешно создан.")
            asyncio.create_task(consume_messages(consumer))  # Начинаем чтение сообщений сразу после создания consumer
            break
        except Exception as e:
            logger.info(f"Kafka недоступна или ошибка при создании consumer: {e}, ждем...")
            await asyncio.sleep(2)
    return consumer


async def consume_messages(consumer):
    async with AsyncSessionLocal() as session:
        try:
            async for message in consumer:
                message_id = message.value.get('message_id')
                if message_id is not None:
                    logger.info(f"Получено сообщение из Kafka: {message.value}")
                    await mark_message_processed(session, message_id)
                    logger.info(f"Сообщение с ID {message_id} обработано и помечено в базе данных.")
        finally:
            await consumer.stop()