from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

from app.models.user_model import UserRole
from fastapi import Form



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
    
    
    @field_validator("email")
    @classmethod
    def email_val(cls, v):
        if not v.endswith("gmail.com"):
            raise ValueError(
                "Only Gmail address Allowed"
            )
            
        return v
    

    @classmethod
    def as_form(
        cls,
        full_name: str = Form(...),
        email: EmailStr = Form(...),
        phone: Optional[str] = Form(None),
        hashed_password: str = Form(...),
        adress: str = Form(...),
        city: Optional[str] = Form(None),
        state: Optional[str] = Form(None),
        pincode: Optional[str] = Form(None),
    ):
        return cls(
            full_name=full_name,
            email=email,
            phone=phone,
            hashed_password=hashed_password,
            adress=adress,
            city=city,
            state=state,
            pincode=pincode,
        )
        
       
       
        
class UserRegister(BaseRegisterRequest):
    pass    
    
    
    
    
class FarmerRegister(BaseRegisterRequest):
    farm_name : str
    farm_size_acres : str
    farm_location : str
    aadhar_number : str
    kisan_id : str


    @classmethod
    def as_form(
        cls,
        full_name: str = Form(...),
        email: EmailStr = Form(...),
        phone: Optional[str] = Form(None),
        hashed_password: str = Form(...),
        adress: str = Form(...),
        city: Optional[str] = Form(None),
        state: Optional[str] = Form(None),
        pincode: Optional[str] = Form(None),

        farm_name: str = Form(...),
        farm_size_acres: str = Form(...),
        farm_location: str = Form(...),
        aadhar_number: str = Form(...),
        kisan_id: str = Form(...),
    ):
        return cls(
            full_name=full_name,
            email=email,
            phone=phone,
            hashed_password=hashed_password,
            adress=adress,
            city=city,
            state=state,
            pincode=pincode,

            farm_name=farm_name,
            farm_size_acres=farm_size_acres,
            farm_location=farm_location,
            aadhar_number=aadhar_number,
            kisan_id=kisan_id,
        )
        
  
  
        
class VendorRegister(BaseRegisterRequest):
    business_name : str
    business_type : str
    gst_number : str
    license_number : str
    mandi_name : str
    mandi_location : str


    @classmethod
    def as_form(
        cls,
        full_name: str = Form(...),
        email: EmailStr = Form(...),
        phone: Optional[str] = Form(None),
        hashed_password: str = Form(...),
        adress: str = Form(...),
        city: Optional[str] = Form(None),
        state: Optional[str] = Form(None),
        pincode: Optional[str] = Form(None),

        business_name: str = Form(...),
        business_type: str = Form(...),
        gst_number: str = Form(...),
        license_number: str = Form(...),
        mandi_name: str = Form(...),
        mandi_location: str = Form(...),
    ):
        return cls(
            full_name=full_name,
            email=email,
            phone=phone,
            hashed_password=hashed_password,
            adress=adress,
            city=city,
            state=state,
            pincode=pincode,

            business_name=business_name,
            business_type=business_type,
            gst_number=gst_number,
            license_number=license_number,
            mandi_name=mandi_name,
            mandi_location=mandi_location,
        )


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