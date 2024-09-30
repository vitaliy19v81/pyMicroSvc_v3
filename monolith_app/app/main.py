import logging
# import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.exc import OperationalError
from tenacity import retry, stop_after_attempt, wait_fixed, before_log, after_log


from .consumer import wait_for_kafka_consumer
from .crud import create_message, get_message_stats
from .database import check_db_ready, get_db, engine, init_db
# from .database import engine, Base, SessionLocal
from .producer import send_message, wait_for_kafka_producer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()



# # Глобальный объект Kafka producer
producer, consumer = None, None

# # # Асинхронная функция для ожидания готовности базы данных
# async def wait_for_db():
#     while True:
#         try:
#             Base.metadata.create_all(bind=engine)
#             db = SessionLocal()
#             db.execute("SELECT 1")  # Пробный запрос к базе данных
#             db.close()
#             logger.info("PostgreSQL доступен.")
#
#             break
#         except OperationalError:
#             logger.info("PostgreSQL недоступен, ждем...")
#             await asyncio.sleep(2)  # Асинхронное ожидание перед повторной попыткой

# # Функция для проверки готовности базы данных
# async def wait_for_db():
#     try:
#         async with engine.connect() as conn:
#             await conn.execute("SELECT 1")  # Тестовое подключение
#         logger.info("База данных готова.")
#         return True
#     except Exception as e:
#         logger.error(f"База данных не готова: {e}")
#         return False



# Проверка готовности базы данных и Kafka при старте FastAPI
@app.on_event("startup")
async def startup():
    global producer, consumer
    # await wait_for_db()
    await init_db()  # Инициализация базы данных
    await check_db_ready(engine) # Ожидаем, пока база данных станет доступной
    producer = await wait_for_kafka_producer()  # Ожидаем, пока Kafka_producer станет доступным
    await wait_for_kafka_consumer()  # Ожидаем, пока Kafka_consumer станет доступным

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

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



# # Декоратор для повторных попыток сохранения в базу данных
# @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before=before_log(logger, logging.INFO),
#        after=after_log(logger, logging.INFO))
# async def save_message_with_retry(db: Session, message: str):
#     return await run_in_threadpool(create_message, db, message)
#
#
# # Декоратор для повторных попыток отправки сообщения в Kafka
# @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before=before_log(logger, logging.INFO),
#        after=after_log(logger, logging.INFO))
# async def send_message_with_retry(producer, topic, message):
#     await run_in_threadpool(send_message, producer, topic, message)


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

# @app.get("/stats/")
# async def get_message_stats_api(db: Session = Depends(get_db)):
#     # Асинхронно вызываем блокирующую функцию, чтобы она выполнялась в пуле потоков
#     stats = await run_in_threadpool(get_message_stats, db)
#     return stats

@app.get("/stats/")
async def get_message_stats_api(db: AsyncSession = Depends(get_db)):
    # Асинхронно вызываем функцию для получения статистики сообщений
    stats = await get_message_stats(db)
    return stats