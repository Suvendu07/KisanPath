import os
import uuid
from fastapi import status, HTTPException, Depends,UploadFile
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.models.product_model import Product
from app.models.order_model import OrderItem
from app.schemas.farmer import FarmerProfileUpdate, FarmerProfileResponse, ProductCreate, ProductUpdate, ProductResponse
from app.core.permision import require_farmer
from app.database import get_db


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


# def get_farmer(user : User, db : Session) -> Farmer:
#     farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    
#     if not farmer:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer profile not found")
    
#     return farmer



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




def build_profile_response(farmer: Farmer, user: User) -> dict:

    return {
        "id": farmer.id,
        "farm_name": farmer.farm_name,
        "farm_size_acres": farmer.farm_size_acres,
        "farm_location": farmer.farm_location,

        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "city": user.city,
        "state": user.state
    }

def product_response(product : Product, db : Session) -> dict:
    
    data = ProductResponse.model_validate(product).model_dump()
    
    farmer = db.query(Farmer).filter(Farmer.id == product.farmer_id).first()
    if farmer and farmer.user:
        data["farmer_name"] = farmer.user.full_name
        data["farmer_city"] = farmer.user.city
    return data



def get_dashboard(user, db : Session):
    
    # farmer = get_farmer(user, db)
    farmer = db.query(Farmer).filter(
        Farmer.user_id == user.id
    ).first()
    
    total_products = db.query(Product).filter(Product.farmer_id == farmer.id).count()
    
    active_products = db.query(Product).filter(Product.farmer_id == farmer.id , Product.is_available == True).count()
    
    total_orders = db.query(OrderItem).join(Product).filter(Product.farmer_id == farmer.id).count()
    
    return {
        "farmer_name" : user.full_name,
        "is_approved" : farmer.is_approved,
        "total_products" : total_products,
        "active_products" : active_products,
        "total_orders" : total_orders
    }
    
    
    
def get_profile(user, db : Session):
    
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    
    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer profile not found"
        )

    # farmer = get_farmer(user, db)
    return build_profile_response(farmer, user)



def update_profile(payload,  farmer , user , db : Session):
    
    # farmer = get_farmer(user , db)
    
    farmer_fileds = ["farm_name", "farm_size_acres", "farm_location", "aadhar_number","kisan_id", "bio"]
    
    for field in farmer_fileds:
        value = getattr(payload, field)
        
        if value is not None:
            setattr(farmer, field, value)
            
            
    user_fields = ["full_name", "phone", "address", "city", "state", "pincode"]
    
    for field in user_fields:
        value = getattr(payload, field)
        
        if value is not None:
            setattr(user, field, value)
            
            
            
    db.commit()
    db.refresh(farmer)
    
    return build_profile_response(farmer, user)




def upload_image(image , farmer , db : Session):
    
    # farmer = get_farmer(user, db)
    path = save_upload(image, "farmer_image")
    farmer.farm_image = path
    db.commit()
    
    return {
        "message" : "Image upload successfully"
    }
    
    
    
def list_products(farmer : Farmer = Depends(require_farmer), db:Session = Depends(get_db)):
    
    # farmer = get_farmer(user, db)
    
    products = db.query(Product).filter(Product.farmer_id == farmer.id).all()
    
    return products



def create_products(payload : ProductCreate,farmer : Farmer = Depends(require_farmer),db : Session = Depends(get_db)):
    
    # farmer = get_farmer(user , db)
    
    if not farmer.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your farmer account must be approved by admin before listing products.")
    
    
    new_product = Product( 
        farmer_id = farmer.id,
        **payload.model_dump()
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {
        "message" : "Product created successfully"
    }
    
    
    

def update_product(product_id : int, payload : ProductUpdate, farmer : Farmer = Depends(require_farmer) , db : Session = Depends(get_db)):
    
    # farmer = get_farmer(user, db)
    
    product = db.query(Product).filter(Product.id == product_id, Product.farmer_id == farmer.id).first()
    
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Products not found")
    
    
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(product, key, value)
        
        
    db.commit()
    db.refresh(product)
    
    return {
        "message" : "Details updated successfully"
    }
    
    
    
    
def delete_product(product_id : int, farmer : Farmer = Depends(require_farmer), db : Session = Depends(get_db)):
    
    product = db.query(Product).filter(Product.id == product_id, Product.farmer_id == farmer.id).first()
    
    if not product:
       raise HTTPException(
         status_code=404,
         detail="Product not found"
    )
    
    db.delete(product)
    db.commit()
    
    
    return {
        "message" : "Product Delete successfully"
    }
    
    

def upload_product_image(product_id: int, file: UploadFile,farmer : Farmer = Depends(require_farmer) ,db: Session = Depends(get_db)) -> dict:
    # farmer  = get_farmer_or_404(user, db)
    product = db.query(Product).filter(
        Product.id        == product_id,
        Product.farmer_id == farmer.id,
    ).first()
 
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
 
    path          = save_upload(file, "product_images")
    product.image = path
    db.commit()
    return {"message": "Product image updated.", "image_url": f"/{path}"}
 
 


def get_farmer_orders(farmer : Farmer = Depends(require_farmer),  db: Session  = Depends(get_db)) -> list:
    # farmer = get_farmer_or_404(user, db)
 
    items = (
        db.query(OrderItem)
        .join(Product)
        .options(joinedload(OrderItem.order))
        .filter(Product.farmer_id == farmer.id)
        .all()
    )
 
    result      = []
    seen_orders = set()
    for item in items:
        order = item.order
        if order and order.id not in seen_orders:
            seen_orders.add(order.id)
            result.append({
                "order_id":     order.id,
                "status":       order.status,
                "created_at":   order.created_at,
                "final_amount": order.final_amount,
                "tracking_id":  order.tracking_id,
            })
    return result