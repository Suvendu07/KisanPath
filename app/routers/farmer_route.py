from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.schemas.farmer import FarmerProfileUpdate, ProductCreate, ProductUpdate, ProductResponse
from app.services.farmer_service import get_dashboard, get_profile
from app.core.permision import require_farmer

router = APIRouter()




@router.get("/farmer/dashboard")
def dashboard(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):

    return get_dashboard(current_user, db)




@router.get("/farmer/profile")
def profile(current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    return get_profile(current_user, db)