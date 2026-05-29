import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Enum,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING     = "pending"       # just placed, payment not confirmed
    CONFIRMED   = "confirmed"     # payment done
    PROCESSING  = "processing"    # farmer is preparing
    SHIPPED     = "shipped"       # out for delivery
    DELIVERED   = "delivered"     # received by buyer
    CANCELLED   = "cancelled"     # cancelled by user or admin


class Order(Base):
    __tablename__ = "orders"

    id                  = Column(Integer, primary_key=True, index=True)

    # Who placed the order
    buyer_id            = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                                 nullable=True)

    # Delivery address (snapshot at time of order)
    delivery_address    = Column(Text, nullable=False)
    delivery_city       = Column(String(100), nullable=True)
    delivery_pincode    = Column(String(10),  nullable=True)

    # Pricing
    total_amount        = Column(Float, nullable=False)    # sum of all items
    delivery_charge     = Column(Float, default=0.0)
    final_amount        = Column(Float, nullable=False)    # total + delivery

    # Status & Tracking
    status              = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    tracking_id         = Column(String(100), nullable=True, unique=True)
    notes               = Column(Text, nullable=True)      # special instructions

    # Timestamps
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda:datetime.now(timezone.utc))
    delivered_at        = Column(DateTime, nullable=True)

    buyer       = relationship("User",      back_populates="orders")
    items       = relationship("OrderItem", back_populates="order", cascade="all, delete")
    feedback    = relationship("Feedback",  back_populates="order",  uselist=False)

    def __repr__(self):
        return f"<Order id={self.id} buyer={self.buyer_id} status={self.status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id              = Column(Integer, primary_key=True, index=True)

    order_id        = Column(Integer, ForeignKey("orders.id",   ondelete="CASCADE"),  nullable=False)
    product_id      = Column(Integer, ForeignKey("farmer_products.id", ondelete="SET NULL"), nullable=True)

    # Snapshot of product details at time of purchase
    product_name    = Column(String(150), nullable=False)
    quantity        = Column(Float, nullable=False)
    unit            = Column(String(20),  nullable=False)
    price_per_unit  = Column(Float, nullable=False)
    subtotal        = Column(Float, nullable=False)         # quantity × price_per_unit

    order   = relationship("Order",   back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem id={self.id} product={self.product_name} qty={self.quantity}>"