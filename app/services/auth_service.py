from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import User, UserRole
from app.models.farmer_model import Farmer
from app.models.vendor_model import Vendor
from app.core.security import hash_password, verify_password
from app.schemas.auth import  LoginRequest, TokenResponse, UserRegister, FarmerRegister, VendorRegister


# def register_user(data: RegisterRequest, db: Session) -> User:
 

#     # Check duplicate email
#     existing = db.query(User).filter(User.email == data.email).first()
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="An account with this email already exists."
#         )

#     # Check duplicate phone
#     if data.phone:
#         existing_phone = db.query(User).filter(User.phone == data.phone).first()
#         if existing_phone:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="An account with this phone number already exists."
#             )

#     # Create base user
#     new_user = User(
#         full_name       = data.full_name,
#         email           = data.email,
#         phone           = data.phone,
#         hashed_password = hash_password(data.password),
#         role            = data.role,
#     )
#     db.add(new_user)
#     db.flush()   # get new_user.id without committing yet

#     # Auto-create role-specific profile
#     if data.role == UserRole.FARMER:
#         db.add(Farmer(user_id=new_user.id))

#     elif data.role == UserRole.VENDOR:
#         db.add(Vendor(
#             user_id       = new_user.id,
#             business_name = data.full_name,   # placeholder, vendor can update later
#         ))

#     db.commit()
#     db.refresh(new_user)
#     return new_user

def check_exist(db , email, phone):
    existing = db.query(User).filter((User.email == email) | (User.phone == phone)).first()
    
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An Account with this email or phone number is exist")
    
    
    

def register_user(data , db : Session):
    
    existing = check_exist(db, data.email, data.phone)
    
    
    user_data = data.model_dump()
    
    hashed_pwd = hash_password(user_data.pop("hashed_password"))
    
    new_user = User(**user_data,
                    hashed_password = hashed_pwd, role = UserRole.USER)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message" : "User Register Successfully"
    }


    
def register_farmer(data, db):
    
    
    existing = check_exist(db, data.email, data.phone)


    # Create User First
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.hashed_password),
        adress=data.adress,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        role=UserRole.FARMER
    )

    db.add(new_user)

    # Generate user.id before commit
    db.flush()

    # Create Farmer Profile
    new_farmer = Farmer(
        user_id=new_user.id,
        farm_name=data.farm_name,
        farm_size_acres=data.farm_size_acres,
        farm_location=data.farm_location,
        aadhar_number=data.aadhar_number,
        kisan_id=data.kisan_id
    )

    db.add(new_farmer)

    db.commit()

    return {
        "message": "Farmer registered successfully"
    }
    
    
    
def register_vendor(data, db: Session):

    existing = check_exist(db, data.email, data.phone)

    # Create User
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.hashed_password),
        adress=data.adress,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        role=UserRole.VENDOR
    )

    db.add(new_user)

    # Generate user.id
    db.flush()

    # Create Vendor Profile
    new_vendor = Vendor(
        user_id=new_user.id,
        business_name=data.business_name,
        business_type=data.business_type,
        gst_number=data.gst_number,
        license_number=data.license_number,
        mandi_name=data.mandi_name,
        mandi_location=data.mandi_location
    )

    db.add(new_vendor)

    db.commit()

    return {
        "message": "Vendor Registered Successfully"
    }




def login_user(data: LoginRequest, db: Session) -> TokenResponse:
  
    user = db.query(User).filter(User.email == data.email).first()

    # Same error message for wrong email or wrong password (security best practice)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support."
        )

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    return TokenResponse(
        role      = user.role,
        user_id   = user.id,
        full_name = user.full_name,
    )