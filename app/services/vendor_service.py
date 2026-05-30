from sqlalchemy.orm import Session
from datetime import date
from fastapi import HTTPException, Depends,status
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
    

    return {
        
    "business_name": vendor.business_name,
    "business_type":vendor.business_type,
    "gst_number":vendor.gst_number,
    "license_number":vendor.license_number,
    "mandi_name":vendor.mandi_name,
    "mandi_location":vendor.mandi_location,
    "bio":vendor.bio,


    "full_name" : user.full_name,
    "email" : user.email,
    "phone": user.phone,
    "city": user.city,
    "state" :user.state,
    "profile_image" : user.profile_image,
    
    }



def build_price_response(price: MandiPrice, db: Session) -> dict:
    data   = MandiPriceResponse.model_validate(price).model_dump()
    vendor = db.query(Vendor).filter(Vendor.id == price.vendor_id).first()
    if vendor and vendor.user:
        data["vendor_name"] = vendor.user.full_name
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
        "today_prices" : today_prices,
    }
    

    
def get_profile(user, db : Session):
    
    vendor = get_vendor(user, db)
    
    return build_profile_response(user, vendor)




def update_profile(payload, current_user , db : Session):
    
    vendor = get_vendor(current_user, db)
    
    
    vendor_fields = ["business_name","business_type", "gst_number", "license_number", "mandi_name", "mandi_location", "bio"]
    
    for field in vendor_fields:
        
        value = getattr(payload, field)
        
        if value is not None:
            setattr(vendor, field, value)
            
            
    user_fields = ["full_name", "phone", "address", "city", "state", "pincode"]
    
    for field in user_fields:
        value = getattr(payload, field)
        
        if value is not None:
            setattr(vendor, field, value)
            
            
    db.commit()
    db.refresh(vendor)
    
    return {"message" : "Profile update successfully"}




def get_all_prices(crop_name: str, state: str, db: Session) -> list:
    """Public — no role restriction. Farmers and users can view market rates."""
    query = db.query(MandiPrice)
    if crop_name:
        query = query.filter(MandiPrice.crop_name.ilike(f"%{crop_name}%"))
    if state:
        query = query.filter(MandiPrice.state.ilike(f"%{state}%"))
    prices = query.order_by(MandiPrice.price_date.desc()).all()
    return [build_price_response(p, db) for p in prices]




def list_own_prices(user , db : Session):
    
    vendor = get_vendor(user, db)
    
    prices = db.query(MandiPrice).filter(MandiPrice.vendor_id == vendor.id).order_by(MandiPrice.price_date.desc()).all()
    
    return [build_price_response(p, db) for p in prices]





def create_price(payload, user, db : Session):
    
    vendor = get_vendor(user, db)
    
    if not vendor.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your vendor account must be approved by admin before posting prices")
    
    
    prices = MandiPrice(vendor_id =vendor.id, **payload.model_dump())
    
    db.add(prices)
    db.commit()
    db.refresh(prices)
    
    return {
        "message" : "Price set successfully"
    }
    
    
    
    
def update_price(payload, price_id , user, db : Session):
    
    vendor = get_vendor(user, db)
    
    price = db.query(MandiPrice).filter(MandiPrice.id == price_id, MandiPrice.vendor_id == vendor.id).first()
    
    
    
    if not price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mandi price entry not found")
    
    
    for field, value in payload.model_dump(exclude_none = True).items():
        setattr(price, field, value)
        
        
    db.commit()
    db.refresh(price)
    
    return {
        "message" : "Price updated successfully"
    }
    
    
    
def delete_Price(price_id, user, db: Session):
    
    vendor = get_vendor(user, db)
    
    price = db.query(MandiPrice).filter(MandiPrice.id == price_id, MandiPrice.vendor_id == vendor.id).first()
    
    
    if not price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="price not found")
    
    
    db.delete(price)
    db.commit()
    
    return {
        "message" : "Price deleted successfully"
    }