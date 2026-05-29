from sqlalchemy import Column, String, Integer, Float, Boolean, Enum, DateTime,ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime, timezone





class BulkUnit(str, enum.Enum):
    KG = "kg"
    QUINTAL = "quintal"
    TON = "ton"
    
    
    
class VendorProduct(Base):
    
    __tablename__ = "vendor_products"
    
    
    id = Column(Integer, primary_key=True, unique=True)
    
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    
    
    crop_name = Column(String(150), nullable=False, index= True)
    crop_variety = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    
    
    price_per_unit = Column(Float, nullable=False)
    unit = Column(Enum(BulkUnit), default=BulkUnit.QUINTAL)
    
    
    stock_quantity = Column(Float, nullable=False, default=0.0)
    min_order_quantity = Column(Float, nullable=False, default=1.0)
    
    
    available_at = Column(String(200), default=None)
    
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    
    vendor = relationship("Vendor", back_populates="vendor_products")
    orders = relationship("VendorOrder", back_populates="vendor_product_model")
    
    
    def __repr__(self):
        return f"<VendorProduct id={self.id} crop={self.crop_name} price={self.price_per_unit}>"