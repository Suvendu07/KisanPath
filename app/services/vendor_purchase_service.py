import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import User
from app.models.vendor_model import Vendor
from app.models.vendor_product_model import VendorProduct
from app.models.vendor_order import VendorOrder, BuyerType, VendorOrderStatus
from app.services.vendor_service import get_vendor
from app.schemas.vendor_product import VendorProductCreate, VendorProductUpdate, VendorProductResponse, VendorOrderResponse, VendorPurchaseRequest





def build_listing_response(listing : VendorProduct, db : Session):
    data = VendorOrderResponse.model_validate(listing).model_dump()
    
    if listing.vendor and listing.vendor.user:
        data["vendor_name"]     = listing.vendor.user.full_name
        data["vendor_location"] = listing.vendor.mandi_location
    return data




def list_vendor_product(vendor , db : Session):
    data = db.query(VendorProduct).filter(VendorProduct.vendor_id == vendor.id).order_by(VendorProduct.created_at.desc()).all()
    
    return [build_listing_response(1, db) for i in data]




def create_vendor_product(payload, vendor , db : Session):
    
    
    if not vendor.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your vendor account must be approved by admin before listing products.")
    
    data = VendorProduct(vendor_id = vendor.id, **payload.model_dump(exclude_none = True))
    
    
    db.add(data)
    db.commit()
    db.refresh(data)
    
    return build_listing_response(data, db)




def update_vendor_Product(payload ,product_id, vendor, db : Session):
    
    data = db.query(VendorProduct).filter(VendorProduct.id == product_id, VendorProduct.vendor_id == vendor.id)
    
    
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data not found")
    
    
    for field, value in payload.model_dumo(exclude_none = True).items():
        setattr(data, field, value)
        
        
    db.commit()
    db.refresh(data)
    
    return build_listing_response(data, db)




def delete_vendor_product(product_id, vendor, db : Session):
    
    data = db.query(VendorProduct).filter(VendorProduct.id == product_id, VendorProduct.vendor_id == vendor.id).first()
    
    
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data not found.")
    
    db.delete(data)
    db.commit()
    
    return {
        "message" : "Product deleted successfully"
    }