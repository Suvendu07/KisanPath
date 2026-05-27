from fastapi import APIRouter, Depends
from app.schemas.user import UserProfileUpdate, OrderCreate, OrderResponse, FeedbackCreate
from app.models.user_model import User
from sqlalchemy.orm import Session
from app.services.user_service import get_dashboard, get_profile, update_profile
from app.core.permision import require_user
from app.database import get_db




router = APIRouter(prefix="/user",
                   tags=["user"])


@router.get("/dahsboard")
def dashboard(current_user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return get_dashboard(current_user, db)




@router.get("/profile")
def profile(current_user : User = Depends(require_user)):
    
    return get_profile(current_user)




@router.put("/profile/update")
def update(payload : UserProfileUpdate, user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return update_profile(payload, user, db)