import logging
import json
import os
import asyncio
from fastapi.concurrency import run_in_threadpool
# from kafka import KafkaConsumer
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

# from .database import SessionLocal
from .database import AsyncSessionLocal
from .crud import mark_message_processed


# consumer = None

def load_environment():
    env = os.getenv('ENVIRONMENT', 'dev')  # По умолчанию 'dev'
    if env == 'prod':
        load_dotenv('.env.prod')
    else:
        load_dotenv('.env.dev')

load_environment()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def create_consumer():
#     consumer = KafkaConsumer(
#         'message_topic',
#         bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
#
#         auto_offset_reset='earliest',
#         enable_auto_commit=True,
#         value_deserializer=lambda x: json.loads(x.decode('utf-8'))
#     )
#     logger.info("Kafka консьюмер успешно создан.")
#     return consumer

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

# async def consume_messages(consumer):
#     db = SessionLocal()
#
#     while True:
#         messages = await asyncio.to_thread(consumer.poll)  # Получаем сообщения из Kafka
#         if messages:
#             # Проходим по каждой паре ключ-значение, где ключ — это TopicPartition, а значение — список сообщений
#             for records in messages.values():
#                 for record in records:  # Проходим по каждому ConsumerRecord
#                     message_id = record.value.get('message_id')  # Извлекаем message_id
#                     if message_id is not None:
#                         logger.info(f"Получено сообщение из Kafka: {record.value}")
#                         # Асинхронно вызываем функцию mark_message_processed в пуле потоков
#                         await run_in_threadpool(mark_message_processed, db, message_id)
#                         logger.info(f"Сообщение с ID {message_id} обработано и помечено в базе данных.")

async def consume_messages(consumer):
    # consumer = await create_consumer()
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

# def consume_messages():
#     consumer = create_consumer()
#     db = SessionLocal()
#
#     for message in consumer:
#         logger.info(f"Получено сообщение из Kafka: {message.value}")
#         mark_message_processed(db, message.value['id'])
#         logger.info(f"Сообщение обработано и помечено в базе данных: {message.value}")

if __name__ == "__main__":
    # consume_messages()
    asyncio.run(consume_messages())