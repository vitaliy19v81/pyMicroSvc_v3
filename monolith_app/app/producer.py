import logging
import json
import os
import asyncio
from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv


def load_environment():
    env = os.getenv('ENVIRONMENT', 'dev')  # По умолчанию 'dev'
    if env == 'prod':
        load_dotenv('.env.prod')
    else:
        load_dotenv('.env.dev')

load_environment()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_producer():
    producer = AIOKafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    await producer.start()
    logger.info("Kafka producer успешно создан.")
    return producer

# Асинхронная функция для ожидания готовности Kafka_producer
async def wait_for_kafka_producer():
    while True:
        try:
            # producer = await run_in_threadpool(create_producer)  # Асинхронное создание Kafka producer
            producer = await create_producer()  # Асинхронное создание Kafka producer
            logger.info("Kafka producer успешно создан.")
            break
        except Exception as e:
            logger.info(f"Kafka недоступна или ошибка при создании producer: {e}, ждем...")
            await asyncio.sleep(2)  # Асинхронное ожидание перед повторной попыткой
    return producer


# Функция для отправки сообщения в Kafka
async def send_message(producer: AIOKafkaProducer, topic: str, message: dict):
    await producer.send(topic, message)
    await producer.flush()
    logger.info(f"Сообщение отправлено в Kafka: {message}")
