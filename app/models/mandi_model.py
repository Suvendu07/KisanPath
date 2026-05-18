import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Enum,
    Date,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


# Reuse the same unit choices as products
class PriceUnit(str, enum.Enum):
    KG      = "kg"
    QUINTAL = "quintal"
    TON     = "ton"


class MandiPrice(Base):
    __tablename__ = "mandi_prices"

    id              = Column(Integer, primary_key=True, index=True)

    # Who posted this price
    vendor_id       = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"),
                             nullable=False)

    # Crop Info
    crop_name       = Column(String(150), nullable=False, index=True)
    crop_variety    = Column(String(100), nullable=True)   # e.g. Basmati, Sona Masoori

    # Price Info
    min_price       = Column(Float, nullable=False)        # lowest price (INR)
    max_price       = Column(Float, nullable=False)        # highest price (INR)
    modal_price     = Column(Float, nullable=False)        # most common price (INR)
    unit            = Column(Enum(PriceUnit), default=PriceUnit.QUINTAL)

    # Market Info
    mandi_name      = Column(String(150), nullable=False)
    mandi_location  = Column(String(200), nullable=True)
    state           = Column(String(100), nullable=True)

    # Date of price (not necessarily today)
    price_date      = Column(Date, nullable=False, default=datetime.utcnow)

    # Extra
    notes           = Column(Text, nullable=True)

    # Timestamps
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor  = relationship("Vendor", back_populates="mandi_prices")

    def __repr__(self):
        return (
            f"<MandiPrice id={self.id} crop={self.crop_name} "
            f"modal={self.modal_price} mandi={self.mandi_name}>"
        )