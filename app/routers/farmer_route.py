from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.schemas.farmer import FarmerProfileUpdate, ProductCreate, ProductUpdate, ProductResponse
from app.services.farmer_service import get_dashboard, get_profile, update_profile, upload_image
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


@router.put("/farmer/update/profile")
def update(payload : FarmerProfileUpdate, user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    
    
    return update_profile(payload, farmer, user, db)



@router.post("/farmer/upload/image")
def upload(image : UploadFile, current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    farmer = db.query(Farmer).filter(Farmer.user_id == User.id).first()
    
    return upload_image(image, farmer, db)