from datetime import datetime
import os
import uuid

from fastapi import HTTPException, status,UploadFile
from sqlalchemy.orm import Session

from app.models.user_model import User, UserRole
from app.models.farmer_model import Farmer
from app.models.vendor_model import Vendor
from app.core.security import hash_password, verify_password, create_reset_token, verify_reset_token
from app.schemas.auth import  LoginRequest, TokenResponse
from app.utils.email import send_reset_email
from app.config import settings
from app.services.email_service import send_welcome_email
1


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}



def check_exist(db , email, phone):
    existing = db.query(User).filter((User.email == email) | (User.phone == phone)).first()
    
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An Account with this email or phone number is exist")
    
    
    
def save_upload(file: UploadFile, subfolder: str) -> str:

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG are allowed"
        )

    folder = os.path.join(settings.UPLOAD_DIR, subfolder)

    os.makedirs(folder, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1]

    filename = f"{uuid.uuid4()}.{ext}"

    filepath = os.path.join(folder, filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    return f"/uploads/{subfolder}/{filename}"



def upload_image(image , user , db : Session):
    
    # farmer = get_farmer(user, db)
    path = save_upload(image, "profile_image")
    user.profile_image = path
    db.commit()
    
    return {
        "message" : "Image upload successfully"
    }
    



def register_user(data , image , db : Session):
    
    existing = check_exist(db, data.email, data.phone)
    
    
    user_data = data.model_dump()
    
    hashed_pwd = hash_password(user_data.pop("hashed_password"))
    
    profile_image = None

    if image:
        profile_image = save_upload(image, "profile_image")
    
    new_user = User(
        **user_data,
        hashed_password = hashed_pwd,
        role = UserRole.USER,
        profile_image = profile_image
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    
    send_welcome_email(
        recipient_email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value
    )
    
    
    return {
        "message" : "User Register Successfully"
    }




    
def register_farmer(data, image, db):
    
    
    existing = check_exist(db, data.email, data.phone)

    profile_image = None

    if image:
        profile_image = save_upload(image, "profile_image")

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
        role=UserRole.FARMER,
        profile_image=profile_image
    )

    db.add(new_user)

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
    
    send_welcome_email(recipient_email=new_user.email,
                       full_name=new_user.full_name,
                       role = new_user.role.value
                       )
    
    
    return {
        "message": "Farmer registered successfully"
    }
    
    
    
    
    
def register_vendor(data, image, db: Session):

    existing = check_exist(db, data.email, data.phone)

    profile_image = None

    if image:
        profile_image = save_upload(image, "profile_image")

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
        role=UserRole.VENDOR,
        profile_image=profile_image
    )

    db.add(new_user)

    db.flush()

    # Create Vendor
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
    
    send_welcome_email(recipient_email=new_user.email,
                       full_name=new_user.full_name,
                       role = new_user.role.value
                       )

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
    
    
    


def forget_password(payload, db):
    user = (db.query(User).filter(User.email == payload.email).first())
    
    
    if user:
        token = create_reset_token(user.email)
        
        send_reset_email(user.email, token)
        
        
    return {
        "message" : "If the email exists, a password reset kink has been sent."
    }
    
    
    
    
def reset_password(payload, db):
    
    email = verify_reset_token(payload.token)
    
    if not email:
        
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    
    
    user = (db.query(User).filter(User.email == email).first())
    
    
    if not user:

        raise HTTPException(status_code=404, detail="User not found")

    user.hash_password = hash_password(payload.new_password)

    db.commit()

    return {
        "message":
        "Password reset successful"
    }