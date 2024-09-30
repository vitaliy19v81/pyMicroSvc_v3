import logging
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from . import models

logger = logging.getLogger(__name__)

# def create_message(db: Session, content: str):
#     message = models.Message(content=content)
#     db.add(message)
#     db.commit()
#     db.refresh(message)
#     logger.info(f'Создано сообщение с ID: {message.id}')
#     return message

async def create_message(db: AsyncSession, content: str):
    message = models.Message(content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    logger.info(f'Создано сообщение с ID: {message.id}')
    return message

# def get_message_stats(db: Session):
#     total = db.query(models.Message).count()
#     processed = db.query(models.Message).filter(models.Message.processed == True).count()
#     logger.info(f'Статистика сообщений - всего: {total}, обработанных: {processed}')
#     return {'total': total, 'processed': processed}

async def get_message_stats(db: AsyncSession):
    total = await db.execute(select(func.count()).select_from(models.Message))
    total_count = total.scalar()

    processed = await db.execute(
        select(func.count()).select_from(models.Message).filter(models.Message.processed == True))
    processed_count = processed.scalar()

    logger.info(f'Статистика сообщений - всего: {total_count}, обработанных: {processed_count}')
    return {'total': total_count, 'processed': processed_count}

# def mark_message_processed(db: Session, message_id: int):
#     message = db.query(models.Message).filter(models.Message.id == message_id).first()
#     if message:
#         message.processed = True
#         db.commit()
#         db.refresh(message)
#         logger.info(f'Сообщение с ID {message_id} помечено как обработанное')
#     return message

async def mark_message_processed(db: AsyncSession, message_id: int):
    async with db.begin():
        message = await db.get(models.Message, message_id)
        if message:
            message.processed = True
            await db.commit()
            logger.info(f'Сообщение с ID {message_id} помечено как обработанное')
    return message