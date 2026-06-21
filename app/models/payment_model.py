import enum
from datetime import datetime, timezone



from sqlalchemy import Column, Integer, String, Float, Enum, DateTime,ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentStatus(str, enum.Enum):
    
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUND = "refunded"
    
    
    
class OrderType(str, enum.Enum):
    PRODUCT = "product"
    VENDOR = "vendor"
    
    
class Payment(Base):
    
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    payer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    order_type = Column(Enum(OrderType), nullable=False)
    
    product_order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    
    vendor_order_id = Column(Integer, ForeignKey("vendor_orders.id", ondelete="SET NULL"), nullable=True)
    
    
    
    razorpay_order_id = Column(String(100), unique=True, nullable=False, index=True)
    
    razorpay_payment_id = Column(String(100), unique=True, nullable=True)
    
    razorpay_signature = Column(String(255), nullable=True)
    
    
    
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.CREATED)
    
    
    refund_id = Column(String(100), nullable=True)
    refund_amount = Column(Float, nullable=True)
    refund_reason = Column(Text, nullable=True)
    
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    updated_at = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc))

    paid_at = Column(DateTime(timezone=True),nullable=True)
    
    
    payer = relationship("User", foreign_keys=[payer_id])
    
    
    def __repr__(self):
        return (
            f"<Payment id={self.id} status={self.status} "
            f"amount={self.amount} rzp={self.razorpay_order_id}>"
        )
 