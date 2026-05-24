from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.services.vendor_service import get_dashboard, get_profile, get_vendor
from app.models.user_model import User
from app.core.permision import require_vendor
from sqlalchemy.orm import Session



router = APIRouter(prefix="/vendor",
                   tags=["vendor"])




@router.get("/dashboard")
def dashboard(current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return get_dashboard(current_user, db)




@router.get("/profile")
def profile(current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return get_profile(current_user, db)