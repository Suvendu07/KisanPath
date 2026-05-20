from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base



class Farmer(Base):
    
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete = "CASCADE"), unique=True, nullable=False)
    
    
    farm_name = Column(String(150), nullable=True)
    farm_size_acres = Column(String, nullable=True)
    farm_location = Column(String(200), nullable=True)
    farm_image = Column(String(255), nullable=True)
    
    
    aadhar_number = Column(String(12), unique=True, nullable=True)
    kisan_id = Column(String(12), unique=True , nullable=True)
    
    
    is_approved = Column(Boolean, default=False)
    bio = Column(Text, nullable=True)
    
    
    created_at = Column(DateTime, default=datetime.utcnow)
    update_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    user     = relationship("User",    back_populates="farmer_profile")
    products = relationship("Product", back_populates="farmer", cascade="all, delete")
 
    def __repr__(self):
        return f"<Farmer id={self.id} user_id={self.user_id} farm={self.farm_name}>"
 