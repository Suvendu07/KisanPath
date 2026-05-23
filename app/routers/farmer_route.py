from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.models.product_model import Product
from app.schemas.farmer import FarmerProfileUpdate, ProductCreate, ProductUpdate, ProductResponse
from app.services.farmer_service import get_farmer, get_dashboard, get_profile, update_profile, upload_image, list_products,create_products, update_product, delete_product, get_farmer_orders
from app.core.permision import require_farmer



router = APIRouter(prefix="/farmer")




@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):

    return get_dashboard(current_user, db)




@router.get("/profile")
def profile(current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    return get_profile(current_user, db)




@router.put("/profile/update")
def update(payload : FarmerProfileUpdate,farmer : Farmer = Depends(get_farmer), user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    
    return update_profile(payload, farmer, user, db)




@router.post("/upload/image")
def upload(image : UploadFile, farmer : Farmer = Depends(get_farmer),current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
        
    return upload_image(image, farmer, db)




@router.get("/products")
def list_product(farmer : Farmer = Depends(get_farmer),db : Session = Depends(get_db)):
        
    return list_products(farmer, db)



@router.post("/products/create")
def products(payload : ProductCreate = Depends(ProductCreate.as_form), image : UploadFile = File(None),farmer : Farmer = Depends(get_farmer) ,db: Session = Depends(get_db)):
    
    return create_products(payload,image, farmer, db)




@router.put("/farmer/products/update")
def update(product_id : int, payload : ProductUpdate, farmer : Farmer = Depends(get_farmer), db : Session = Depends(get_db)):
    
    return update_product(product_id, payload,farmer,db)




@router.delete("/farmer/products/delete")
def delete(product_id : int, farmer : Farmer = Depends(get_farmer), db : Session = Depends(get_db)):
    
    return delete_product(product_id, farmer, db)



@router.get("/farmer/orders")
def get_orders(farmer : Farmer = Depends(get_farmer), db : Session = Depends(get_db)):
    
    return get_farmer_orders(farmer, db)