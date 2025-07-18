from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)

    products = relationship("Product", back_populates="category")


class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    products = relationship("Product", back_populates="brand")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")

    brand_id = Column(Integer, ForeignKey("brands.id"))
    brand = relationship("Brand", back_populates="products")

    prices = relationship("ProductPrice", back_populates="product")
    availability = relationship("ProductAvailability", back_populates="product")
    promotions = relationship("Promotion", secondary="promotion_product_link")

class UOM(Base):
    """Unit of Measure"""
    __tablename__ = "uom"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # e.g., kg, g, litre, piece 