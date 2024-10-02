# database.py
import asyncio
import logging
import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine,AsyncEngine, AsyncSession #, async_sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

def load_environment():
    env = os.getenv('ENVIRONMENT', 'dev')  # По умолчанию 'dev'
    if env == 'prod':
        load_dotenv('.env.prod')
    else:
        load_dotenv('.env.dev')

load_environment()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# Создаем асинхронный движок
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Создаем фабрику для асинхронной сессии
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

# Асинхронная функция для получения сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()  # Гарантируем, что сессия закрыта

# Асинхронная функция для создания таблиц
async def init_db():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        finally:
            await conn.close()  # Гарантированное закрытие соединения

# Функция для проверки готовности базы данных с тайм-аутом
async def check_db_ready(engine: AsyncEngine, timeout: int = 30, retry_interval: int = 2):
    total_wait_time = 0
    while total_wait_time < timeout:
        try:
            # Попытка подключения к базе данных
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))  # Тестовое подключение
            logger.info("База данных готова.")
            break
        except OperationalError:
            logger.warning("PostgreSQL недоступен, ждем...")
            await asyncio.sleep(retry_interval)
            total_wait_time += retry_interval
        finally:
            await engine.dispose()  # Закрытие соединения в любом случае
    else:
        # Если не удалось подключиться за отведенное время, выводим ошибку
        logger.error(f"Не удалось подключиться к базе данных за {timeout} секунд.")
        raise TimeoutError("Превышено время ожидания подключения к базе данных.")