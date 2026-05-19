from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import User, UserRole
from app.models.farmer_model import Farmer
from app.models.vendor_model import Vendor
from app.core.security import hash_password, verify_password
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


def register_user(data: RegisterRequest, db: Session) -> User:
 

    # Check duplicate email
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # Check duplicate phone
    if data.phone:
        existing_phone = db.query(User).filter(User.phone == data.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists."
            )

    # Create base user
    new_user = User(
        full_name       = data.full_name,
        email           = data.email,
        phone           = data.phone,
        hashed_password = hash_password(data.password),
        role            = data.role,
    )
    db.add(new_user)
    db.flush()   # get new_user.id without committing yet

    # Auto-create role-specific profile
    if data.role == UserRole.FARMER:
        db.add(Farmer(user_id=new_user.id))

    elif data.role == UserRole.VENDOR:
        db.add(Vendor(
            user_id       = new_user.id,
            business_name = data.full_name,   # placeholder, vendor can update later
        ))

    db.commit()
    db.refresh(new_user)
    return new_user


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