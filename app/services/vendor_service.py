from sqlalchemy.orm import Session
from datetime import date
from fastapi import HTTPException, Depends
from app.schemas.vendor import VendorProfileResponse, VendorProfileUpdate, MandiPriceCreate,MandiPriceUpdate, MandiPriceResponse
from app.database import get_db
from app.models.user_model import User
from app.models.vendor_model import Vendor
from app.core.permision import require_vendor
from app.models.mandi_model import MandiPrice



def get_vendor_by_user(user: User, db : Session):
    
    vendor = db.query(Vendor).filter(Vendor.user_id == user.id).first()
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    return vendor



def get_vendor(current_user : User = Depends(require_vendor), db : Session = Depends(get_db)):
    
    return get_vendor_by_user(current_user, db)



def build_profile_response(user : User, vendor : Vendor):
    
    data = VendorProfileResponse.model_validate(vendor).model_dump()
    
    data["full_name"] = user.full_name,
    data["email"] = user.email,
    data["phone"] = user.phone,
    data["city"] = user.city,
    data["state"] = user.state
    data["profile_image"] = user.profile_image
    
    return data



def get_dashboard(user, db :Session):
    
    vendor = get_vendor(user, db)
    # vendor = db.query(Vendor).filter(Vendor.user_id == user.id)   
    
    
    total_prices = db.query(MandiPrice).filter(MandiPrice.vendor_id == vendor.id).count()
    
    today_prices = db.query(MandiPrice).filter(MandiPrice.vendor_id == vendor.id ,
                                               MandiPrice.price_date == date.today()).count()
    
    
    return{
        "vendor_name" : user.full_name,
        "business_name" : vendor.business_name,
        "is_approved" : vendor.is_approved,
        "total_prices" : total_prices,
        "today_prices" : today_prices
    }
    

    
def get_profile(user, db : Session):
    
    vendor = get_vendor(user, db)
    
    return build_profile_response(vendor, user)