
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.schemas.farmer import (
    FarmerProfileUpdate,
    ProductCreate,
    ProductUpdate,
    ProductResponse
)


from app.services.farmer_service import (
    get_farmer,
    get_dashboard,
    get_profile,
    update_profile,
    upload_image,
    list_products,
    create_products,
    update_product,
    delete_product,
    get_farmer_orders,
    upload_product_image,
    get_order_tracking,
)

from app.services.vendor_purchase_service import browse_vendor_product, get_vendor_listing_details, place_vendor_purchase, get_my_vendor_orders, get_vendor_order_detail, get_vendor_order_tracking
from app.models.vendor_order import BuyerType
from app.schemas.vendor_product import VendorPurchaseRequest
from app.core.permision import require_farmer
from app.schemas.tracking import FarmerOrderStatusUpdate




router = APIRouter(
    prefix="/farmer",
    tags=["Farmer"]
)



@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    return get_dashboard(current_user, db)



@router.get("/profile")
def profile(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    return get_profile(current_user, db)


@router.put("/profile/update")
def update_profile_route(
    payload: FarmerProfileUpdate,
    farmer: Farmer = Depends(get_farmer),
    user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    return update_profile(payload, farmer, user, db)



@router.post("/upload/image")
def upload_farmer_image(
    image: UploadFile = File(...),
    farmer: Farmer = Depends(get_farmer),
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    return upload_image(image, farmer, db)



@router.get(
    "/products",
    response_model=list[ProductResponse]
)
def list_product_route(
    farmer: Farmer = Depends(get_farmer),
    db: Session = Depends(get_db)
):
    return list_products(farmer, db)




@router.post("/products/create")
def create_product_route(
    payload: ProductCreate = Depends(ProductCreate.as_form),
    image: UploadFile = File(None),
    farmer: Farmer = Depends(get_farmer),
    db: Session = Depends(get_db)
):
    return create_products(payload, image, farmer, db)




@router.put("/products/{product_id}")
def update_product_route(
    product_id: int,
    payload: ProductUpdate,
    farmer: Farmer = Depends(get_farmer),
    db: Session = Depends(get_db)
):
    return update_product(product_id, payload, farmer, db)




@router.delete("/products/{product_id}")
def delete_product_route(
    product_id: int,
    farmer: Farmer = Depends(get_farmer),
    db: Session = Depends(get_db)
):
    return delete_product(product_id, farmer, db)




@router.put("/products/{product_id}/image")
def upload_product(product_id : int, file : UploadFile = File(...), current_user : User = Depends(require_farmer), db : Session = Depends(get_db),):
    
    return upload_product_image(current_user, product_id, file, db)




@router.get("/orders")
def get_orders_route(
    farmer: Farmer = Depends(get_farmer),
    db: Session = Depends(get_db)
):
    return get_farmer_orders(farmer, db)




@router.get("/vendor-listing")
def browse_product(current_user : User = Depends(require_farmer), crop_name : str = None, db : Session = Depends(get_db)):
    
    return browse_vendor_product(crop_name , db)




@router.get("vendor-listing/{listing_id}")
def get_vendor_listing(listing_id : int, current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    return get_vendor_listing_details(listing_id, db)




@router.post("/vendor-purchase")
def vendor_purchase(payload : VendorPurchaseRequest,current_user : User = Depends(require_farmer), buyer_type = BuyerType.FARMER, db : Session = Depends(get_db)):
    
    return place_vendor_purchase(payload, current_user, buyer_type, db)





@router.get("/vendor-orders")
def farmer_vendor_order_history(current_user : User = Depends(require_farmer), buyer_type = BuyerType.FARMER, db : Session = Depends(get_db)):
    
    return get_my_vendor_orders(current_user, buyer_type, db)




@router.get("/vendor-orders/{order_id}")
def farme_vendor_order_details( order_id : int, buyer : User = Depends(require_farmer),db : Session = Depends(get_db)):
    
    return get_vendor_order_detail(order_id, buyer, db)




@router.put("orders/{order_id}/status")
def update_order_status(order_id :int, payload : FarmerOrderStatusUpdate, current_user : User = Depends(require_farmer), db : Session = Depends(get_db)):
    
    return update_order_status(current_user, order_id, payload.status, db)




@router.get("/orders/{order_id}/tracking")
def order_tracking(order_id : int, current_user : User = Depends(require_farmer), db : Session = Depends(get_db),):
    
    return get_order_tracking(current_user, order_id, db)




@router.get("/vendor-orders/{order_id}/tracking")
def vendor_order_tracking(order_id : int, current_user : User = Depends(require_farmer), db : Session = Depends(get_db),):
    
    return get_vendor_order_tracking(current_user, order_id, db)