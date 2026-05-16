import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Enum,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


class ProductCategory(str, enum.Enum):
    VEGETABLES  = "vegetables"
    FRUITS      = "fruits"
    GRAINS      = "grains"
    PULSES      = "pulses"
    SPICES      = "spices"
    DAIRY       = "dairy"
    OTHER       = "other"


class ProductUnit(str, enum.Enum):
    KG          = "kg"
    QUINTAL     = "quintal"
    TON         = "ton"
    PIECE       = "piece"
    DOZEN       = "dozen"
    LITRE       = "litre"


class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True, index=True)

    # Owner
    farmer_id       = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"),
                       nullable=False)

    # Product Info
    name            = Column(String(150), nullable=False, index=True)
    description     = Column(Text,        nullable=True)
    category        = Column(Enum(ProductCategory), default=ProductCategory.OTHER)
    image           = Column(String(255), nullable=True)   # uploaded image path

    # Pricing
    price_per_unit  = Column(Float, nullable=False)        # price in INR
    unit            = Column(Enum(ProductUnit), default=ProductUnit.KG)
    stock_quantity  = Column(Float, default=0.0)           # available quantity

    # Ratings (aggregated)
    average_rating  = Column(Float, default=0.0)
    total_ratings   = Column(Integer, default=0)

    # Status
    is_available    = Column(Boolean, default=True)
    is_organic      = Column(Boolean, default=False)

    # Timestamps
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer      = relationship("Farmer",    back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    feedbacks   = relationship("Feedback",  back_populates="product")

    def __repr__(self):
        return f"<Product id={self.id} name={self.name} price={self.price_per_unit}>"