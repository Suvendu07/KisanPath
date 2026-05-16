from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    # Constraint: rating must be between 1 and 5
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )

    id          = Column(Integer, primary_key=True, index=True)

    # Who gave feedback
    user_id     = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)

    # What is being reviewed
    product_id  = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    # Which order this feedback belongs to (prevents fake reviews)
    order_id    = Column(Integer, ForeignKey("orders.id",   ondelete="SET NULL"), nullable=True)

    # Review Content
    rating      = Column(Float,   nullable=False)           # 1.0 – 5.0
    title       = Column(String(150), nullable=True)
    review      = Column(Text,    nullable=True)
    image       = Column(String(255), nullable=True)        # optional review photo

    # Timestamps
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user    = relationship("User",    back_populates="feedbacks")
    product = relationship("Product", back_populates="feedbacks")
    order   = relationship("Order",   back_populates="feedback")

    def __repr__(self):
        return f"<Feedback id={self.id} rating={self.rating} product={self.product_id}>"