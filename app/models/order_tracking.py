from datetime import datetime, timezone


from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from app.database import Base
from app.models.payment_model import OrderType



class OrderTracking(Base):
    
    __tablename__ = "order_tracking"
    
    
    id = Column(Integer, primary_key=True, index=True)
    
    
    order_type = Column(Enum(OrderType), nullable=False)
    product_order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True)
    vendor_order_id = Column(Integer, ForeignKey("vendor_orders.id", ondelete="CASCADE"), nullable=True)
    
    
    status = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),)
    
    
    def __repr__(self):
        oid = self.product_order_id or self.vendor_order_id
        return f"<OrderTracking id={self.id} status={self.status} order_id={oid}>"
 