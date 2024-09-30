import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_fixed, before_log, after_log

from .consumer import wait_for_kafka_consumer
from .crud import create_message, get_message_stats
from .database import check_db_ready, get_db, engine, init_db
from .producer import send_message, wait_for_kafka_producer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# # Глобальный объект Kafka producer
producer, consumer = None, None


# Проверка готовности базы данных и Kafka при старте FastAPI
@app.on_event("startup")
async def startup():
    global producer, consumer
    # await wait_for_db()
    await init_db()  # Инициализация базы данных
    await check_db_ready(engine) # Ожидаем, пока база данных станет доступной
    producer = await wait_for_kafka_producer()  # Ожидаем, пока Kafka_producer станет доступным
    await wait_for_kafka_consumer()  # Ожидаем, пока Kafka_consumer станет доступным

# Декоратор для повторных попыток сохранения в базу данных
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before=before_log(logger, logging.INFO),
       after=after_log(logger, logging.INFO))
async def save_message_with_retry(db: AsyncSession, message: str):
    return await create_message(db, message)  # Убираем run_in_threadpool

# Декоратор для повторных попыток отправки сообщения в Kafka
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before=before_log(logger, logging.INFO),
       after=after_log(logger, logging.INFO))
async def send_message_with_retry(producer, topic, message):
    await send_message(producer, topic, message)  # Убираем run_in_threadpool


# Пример обработчика API для создания сообщения и отправки его в Kafka
@app.post("/messages/")
async def create_message_api(message: str, db: Session = Depends(get_db)):
    logger.info(f"Получено сообщение: {message}")

    # Повторные попытки сохранения сообщения в базе данных
    try:
        db_message = await save_message_with_retry(db, message)
    except Exception as e:
        logger.error(f"Не удалось сохранить сообщение в базе данных: {e}")
        raise HTTPException(status_code=500, detail="Failed to save message to database.")

    # Повторные попытки отправки сообщения в Kafka
    try:
        await send_message_with_retry(producer, "message_topic", {"message_id": db_message.id, "content": message})
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message to Kafka.")

    return {"message_id": db_message.id, "message": message}


@app.get("/stats/")
async def get_message_stats_api(db: AsyncSession = Depends(get_db)):
    # Асинхронно вызываем функцию для получения статистики сообщений
    stats = await get_message_stats(db)
    return stats