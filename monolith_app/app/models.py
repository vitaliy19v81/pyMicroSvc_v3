from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    processed = Column(Boolean, default=False)