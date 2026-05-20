from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

from app.models.user_model import UserRole


# class UserRegisterRequest(BaseModel):
#     full_name: str
#     email:     EmailStr
#     phone:     Optional[str] = None
#     password:  str
#     role:      UserRole = UserRole.USER    # default role is buyer

#     @field_validator("password")
#     @classmethod
#     def password_strength(cls, v):
#         if len(v) < 6:
#             raise ValueError("Password must be at least 6 characters long.")
#         return v

#     @field_validator("full_name")
#     @classmethod
#     def name_not_empty(cls, v):
#         if not v.strip():
#             raise ValueError("Full name cannot be empty.")
#         return v.strip()



# class FarmerRegisterRequest(BaseModel):
#     farm_name : str
#     farm_size_acres : str
#     farm_location : str
#     aadhar_number : str
#     kisan_id : str



class BaseRegisterRequest(BaseModel):
    full_name : str
    email : EmailStr
    phone : Optional[str] = None
    hashed_password : str
    adress : str
    city : Optional[str] = None
    state : Optional[str] = None
    pincode : Optional[str] = None

    
    @field_validator("hashed_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) <6:
            raise ValueError("Password must be at least 6 charcters long")
        
        return v
    
    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Full name can't be empty")
        return v.strip()
    
    
    
class UserRegister(BaseRegisterRequest):
    pass    
    
    
class FarmerRegister(BaseRegisterRequest):
    farm_name : str
    farm_size_acres : str
    farm_location : str
    aadhar_number : str
    kisan_id : str
    
    
class VendorRegister(BaseRegisterRequest):
    business_name : str
    business_type : str
    gst_number : str
    license_number : str
    mandi_name : str
    mandi_location : str




class LoginRequest(BaseModel):
    email:    EmailStr
    password: str




class TokenResponse(BaseModel):
    message:   str = "Login successful"
    role:      UserRole
    user_id:   int
    full_name: str




class AccessTokenResponse(BaseModel):
    message: str = "Token refreshed successfully"




class UserResponse(BaseModel):
    id:            int
    full_name:     str
    email:         str
    phone:         Optional[str]
    role:          UserRole
    is_active:     bool
    is_verified:   bool
    profile_image: Optional[str]
    adress:       Optional[str]
    city:          Optional[str]
    state:         Optional[str]
    pincode:       Optional[str]
    created_at:    datetime

    # Tells Pydantic to read from SQLAlchemy model attributes directly
    model_config = {"from_attributes": True}