from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
import datetime

from app.db.base_class import Base

class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # e.g., Blinkit, Zepto
    base_url = Column(String)

    prices = relationship("ProductPrice", back_populates="platform")
    availability = relationship("ProductAvailability", back_populates="platform")


class ProductPrice(Base):
    __tablename__ = "product_prices"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    price = Column(Float, nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="prices")
    platform = relationship("Platform", back_populates="prices")
    currency = relationship("Currency")


class ProductAvailability(Base):
    __tablename__ = "product_availability"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    is_available = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="availability")
    platform = relationship("Platform", back_populates="availability")


class Currency(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False) # e.g., INR, USD
    name = Column(String) 