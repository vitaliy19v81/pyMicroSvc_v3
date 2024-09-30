import logging
import json
import os
import asyncio
from fastapi.concurrency import run_in_threadpool

from kafka import KafkaProducer
from aiokafka import AIOKafkaProducer

from dotenv import load_dotenv

# producer = None

def load_environment():
    env = os.getenv('ENVIRONMENT', 'dev')  # По умолчанию 'dev'
    if env == 'prod':
        load_dotenv('.env.prod')
    else:
        load_dotenv('.env.dev')

load_environment()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def create_producer():
#     producer = KafkaProducer(
#         bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
#         value_serializer=lambda v: json.dumps(v).encode('utf-8')
#     )
#     logger.info("Kafka продюсер успешно создан.")
#     return producer
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

# def send_message(producer, topic, message):
#     producer.send(topic, message)
#     producer.flush()
#     logger.info(f"Сообщение отправлено в Kafka: {message}")



# Функция для отправки сообщения в Kafka
async def send_message(producer: AIOKafkaProducer, topic: str, message: dict):
    await producer.send(topic, message)
    await producer.flush()
    logger.info(f"Сообщение отправлено в Kafka: {message}")

if __name__ == "__main__":
    producer = create_producer()
    message = {"content": "Hello Kafka"}
    send_message(producer, "message_topic", message)