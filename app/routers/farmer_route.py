from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.models.product_model import Product
from app.schemas.farmer import FarmerProfileUpdate, ProductCreate, ProductUpdate, ProductResponse
from app.services.farmer_service import get_farmer, get_dashboard, get_profile, update_profile, upload_image, list_products,create_products, update_product, delete_product
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
def update(payload : FarmerProfileUpdate,farmer : Farmer = Depends(get_farmer), user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    
    return update_profile(payload, farmer, user, db)




@router.post("/farmer/upload/image")
def upload(image : UploadFile, farmer : Farmer = Depends(get_farmer),current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
        
    return upload_image(image, farmer, db)




@router.get("/farmer/products")
def list_product(farmer : Farmer = Depends(get_farmer),db : Session = Depends(get_db)):
        
    return list_products(farmer, db)



@router.post("/farmer/create_products")
def products(payload : ProductCreate, farmer : Farmer = Depends(get_farmer) ,db: Session = Depends(get_db)):
    
    return create_products(payload, farmer, db)