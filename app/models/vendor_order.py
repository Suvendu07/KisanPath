import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Enum, DateTime, ForeignKey, Text

from sqlalchemy.orm import relationship
from app.database import Base



class VendorOrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    
    
    
class BuyerType(sts, enum.Enum):
    
    FARMER = "farmer"
    USER = "user"
    
    
    
class VendorOrder(Base):
    
    __tablename__ = "vendor_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    vendor_id = Column(Integer, ForeignKey("vendor_products.id", ondelete="SET NULL"), nullable=False)
    
    
    crop_name = Column(String(150), nullable=False)
    price_per_unit = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    
    buyer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    buyer_type = Column(Enum(BuyerType), nullable=False)
    
    delivery_address = Column(Text, nullable=False)
    delivery_city = Column(String(150), nullable=False)
    delivery_pincode = Column(String(10), nullable=False)
    
    
    status = Column(Enum(VendorOrderStatus), default=VendorOrderStatus.PENDING)
    tracking_id = Column(String(100), unique=True, nullable=False)
    notes = Column(Text, nullable= True)
    
    
    
    created_at = Column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc)
)

    updated_at = Column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc),
    onupdate=lambda: datetime.now(timezone.utc)
)

    delivered_at = Column(
    DateTime(timezone=True),
    nullable=True
)