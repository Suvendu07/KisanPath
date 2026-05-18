import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    FARMER = "farmer"
    VENDOR = "vendor"
    
    
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(15), unique=True, nullable=True)
    hashed_password = Column(String(255), unique=True, nullable=False)
    profile_image = Column(String(255), nullable=True)
    
    
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    
    
    adress = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    
    created_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    
    farmer_profile  = relationship("Farmer",   back_populates="user", uselist=False)
 
    # One user → one vendor profile (if role is vendor)
    vendor_profile  = relationship("Vendor",   back_populates="user", uselist=False)
 
    # One user → many orders (if role is user/buyer)
    orders          = relationship("Order",    back_populates="buyer")
 
    # One user → many feedbacks given
    feedbacks       = relationship("Feedback", back_populates="user")
 
    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"