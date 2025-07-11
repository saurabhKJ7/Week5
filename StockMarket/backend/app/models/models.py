from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    watchlist = relationship("WatchlistItem", back_populates="user")
    chat_history = relationship("ChatMessage", back_populates="user")

class WatchlistItem(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    symbol = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="watchlist")

class ChatMessage(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    context_data = Column(JSON, nullable=True)  # Store relevant stock/news data
    
    # Relationships
    user = relationship("User", back_populates="chat_history")

class StockPrice(Base):
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    class Config:
        indexes = [
            ("symbol", "timestamp")
        ]

class NewsArticle(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    embedding = Column(JSON, nullable=True)  # Store vector embedding
    
    class Config:
        indexes = [
            ("published_at",)
        ] 