from fastapi import APIRouter, Depends, UploadFile, File
from app.schemas.user import UserProfileUpdate, OrderCreate, OrderResponse, FeedbackCreate
from app.models.user_model import User
from sqlalchemy.orm import Session
from app.services.user_service import get_dashboard, get_profile, update_profile, browse_product, place_order,list_order, get_order_details, submit_feedback, list_own_feedback, get_product_details, get_order_tracking
from app.core.permision import require_user
from app.database import get_db
from app.services.vendor_purchase_service import browse_vendor_product, get_vendor_listing_details, place_vendor_purchase, get_my_vendor_orders, get_vendor_order_detail, get_vendor_order_tracking
from app.models.vendor_order import BuyerType
from app.schemas.vendor_product import VendorPurchaseRequest, VendorOrderResponse




router = APIRouter(prefix="/user",
                   tags=["user"])




@router.get("/dahsboard")
def dashboard(current_user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return get_dashboard(current_user, db)




@router.get("/profile")
def profile(current_user : User = Depends(require_user)):
    
    return get_profile(current_user)


@router.post("/upload/image")
def upload_image(image: UploadFile = File(...), current_user: User = Depends(require_user), db: Session = Depends(get_db)):
    from app.services.user_service import upload_user_image
    return upload_user_image(image, current_user, db)





@router.put("/profile/update")
def update(payload : UserProfileUpdate, user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return update_profile(payload, user, db)




@router.get("/browse-product")
def browse(category : str = None, search : str = None, min_price : float = None, max_price : float = None, is_organic : bool = None, db : Session = Depends(get_db)):
    
    return browse_product(category, search, min_price, max_price, is_organic, db)




@router.get("/products/{product_id}")
def product_details(product_id : int, current_user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return product_details(product_id, db)




@router.post("/place/order")
def order(payload : OrderCreate, user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return place_order(payload, user, db)




@router.get("/list/orders")
def list(user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    
    return list_order(user, db)




@router.get("/order/details")
def details(order_id : int, user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return get_order_details(order_id, user, db)




@router.post("/feedback")
def feedback(payload : FeedbackCreate, user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return submit_feedback(payload, user, db)




@router.get("/get-feedback")
def get(user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return list_own_feedback(user , db)




@router.get("/vendor-listing")
def browse_listing(current_user : User = Depends(require_user), crop_name : str = None, db : Session = Depends(get_db)):
    
    return browse_vendor_product(crop_name, db)




@router.get("/vendor-listing/{listing_id}")
def get_listing(listing_id : int,current_user : User = Depends(require_user),db : Session = Depends(get_db)):
    
    return get_vendor_listing_details(listing_id, db)





@router.post("/vendor-purchase")
def user_buy_from_vendor(payload : VendorPurchaseRequest,current_user : User = Depends(require_user), buyer_type = BuyerType.USER, db : Session = Depends(get_db)):
    
    return place_vendor_purchase(payload, current_user, buyer_type, db)





@router.get("/vendor-orders")
def user_vendor_order_history(current_user : User = Depends(require_user), buyer_type = BuyerType.USER, db : Session = Depends(get_db)):
    
    return get_my_vendor_orders(current_user, buyer_type, db)




@router.get("/vendor-orders/{order_id}")
def user_vendor_order_details( order_id : int, buyer : User = Depends(require_user),db : Session = Depends(get_db)):
    
    return get_vendor_order_detail(order_id, buyer, db)




@router.get("/order/{order_id}/tracking")
def track_order(order_id : int, current_user: User = Depends(require_user), db : Session = Depends(get_db)):
    
    return get_order_tracking(current_user, order_id, db)




@router.get("/vendor-orders/{order_id}/tracking")
def track_vendor_order(order_id : int, current_user : User = Depends(require_user), db : Session = Depends(get_db)):
    
    return get_vendor_order_tracking(current_user, order_id, db)