from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.services.vendor_service import get_dashboard, get_profile, get_vendor, update_profile, get_all_prices, list_own_prices,create_price, delete_Price, update_price
from app.models.user_model import User
from app.models.vendor_model import Vendor
from app.core.permision import require_vendor, get_current_user
from sqlalchemy.orm import Session
from app.schemas.vendor import VendorProfileResponse, VendorProfileUpdate,MandiPriceCreate, MandiPriceUpdate
from app.schemas.vendor_product import VendorProductCreate, VendorProductUpdate, VendorProductResponse, VendorOrderResponse, VendorPurchaseRequest
from app.services.vendor_purchase_service import list_vendor_product, create_vendor_product, update_vendor_Product, delete_vendor_product, browse_vendor_product, get_vendor_listing_details




router = APIRouter(prefix="/vendor",
                   tags=["vendor"])




@router.get("/dashboard")
def dashboard(current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return get_dashboard(current_user, db)




@router.get("/profile")
def profile(current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return get_profile(current_user, db)




@router.put("/profile/update")
def profile_update(payload : VendorProfileUpdate, current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return update_profile(payload, current_user, db)




@router.get("/mandi-prices/all", summary="[Public] All mandi prices")
def all_mandi_prices(
    crop_name:    str  = None,
    state:        str  = None,
    db:           Session = Depends(get_db),
):
    return get_all_prices(crop_name, state, db)




@router.get("/own-price")
def get_own_price(user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return list_own_prices(user, db)





@router.post("/create/price")
def set_price(payload : MandiPriceCreate, current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return create_price(payload, current_user, db)




@router.put("/update/price")
def price_update(payload : MandiPriceUpdate, price_id : int, current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return update_price(payload, price_id, current_user, db)





@router.delete("/delete/price")
def price_delete(price_id : int, user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return delete_Price(price_id, user, db)




@router.get("/listing/products")
def list_products(vendor : Vendor = Depends(get_vendor), db : Session = Depends(get_db)):
    
    return list_vendor_product(vendor, db)




@router.post("/create/products")
def create_products(payload : VendorProductCreate, current_user : Vendor = Depends(get_vendor), db : Session = Depends(get_db)):
    
    return create_vendor_product(payload, current_user, db)




@router.put("/updates/products")
def update_products(payload : VendorProductUpdate, product_id : int, current_user : Vendor = Depends(get_vendor), db : Session = Depends(get_db)):
    
    return update_vendor_Product(payload, product_id,current_user, db)




@router.delete("/delete/products")
def delete_products(product_id : int, vendor : Vendor = Depends(get_vendor), db : Session = Depends(get_db)):
    
    return delete_vendor_product(product_id, vendor, db)




@router.get("/browse/products")
def browse_product(current_user : User = Depends(get_current_user), crop_name : str = None, db : Session = Depends(get_db)):
    
    return browse_vendor_product(crop_name, db)




@router.get("/products/details")
def get_vendor_listings(listing_id : int , db : Session = Depends(get_db)):
    
    return get_vendor_listing_details(listing_id, db)