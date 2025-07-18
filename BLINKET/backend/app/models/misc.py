from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship
import datetime

from app.db.base_class import Base

promotion_product_link = Table(
    'promotion_product_link', Base.metadata,
    Column('promotion_id', Integer, ForeignKey('promotions.id')),
    Column('product_id', Integer, ForeignKey('products.id'))
)

class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    discount_percentage = Column(Float)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime)

    products = relationship("Product", secondary=promotion_product_link)

class Tax(Base):
    __tablename__ = "taxes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    rate = Column(Float, nullable=False)

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False) # e.g., Bangalore, Mumbai
    pincode = Column(String(6), index=True)
    
class ProductPlatformMapping(Base):
    __tablename__ = "product_platform_mapping"
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), primary_key=True)
    platform_product_id = Column(String, nullable=False) # ID of the product on the specific platform

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class SearchQueryLog(Base):
    __tablename__ = "search_query_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User")

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("search_query_logs.id"))
    thought_process = Column(String)
    generated_sql = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    query = relationship("SearchQueryLog") 