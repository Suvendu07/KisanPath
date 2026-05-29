from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base


class Vendor(Base):

    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    business_name = Column(String(150), nullable=False)
    business_type = Column(String(100), nullable=True)
    gst_number = Column(String(20), unique=True, nullable=True)
    license_number = Column(String(50), unique=True, nullable=True)

    mandi_name = Column(String(150), nullable=True)
    mandi_location = Column(String(150), nullable=True)

    is_approved = Column(Boolean, default=False)
    bio = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="vendor_profile"
    )

    mandi_prices = relationship(
        "MandiPrice",
        back_populates="vendor",
        cascade="all, delete"
    )

    # Added
    vendor_products = relationship(
        "VendorProduct",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Vendor id={self.id} business={self.business_name}>"