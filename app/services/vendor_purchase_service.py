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
    
    
    
    

# Public -- Browse Vendor Product

def browse_vendor_product(crop_name , state, db):
    
    data = db.query(VendorProduct).filter(VendorProduct.is_available == True, VendorProduct.stock_quantity > 0)
    
    if crop_name:
        query = query.filter(VendorProduct.crop_name.ilike(f"{crop_name}"))
        
    data = query.order_by(VendorProduct.created_at.desc()).all()
    
    return [build_listing_response(1, db) for i in data]




def get_vendor_listing_details(listing_id , db : Session):
    
    data = db.query(VendorProduct).filter(VendorProduct.id == listing_id, 
                                          VendorProduct.is_available == True,).first()
    
    
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data not found or no longer available.")
    
    return build_listing_response(data, db)




def place_vendor_purchase(
    buyer:      User,
    buyer_type: BuyerType,
    payload:    VendorPurchaseRequest,
    db:         Session,
) -> dict:
 
 
    # Step 1 — Find the listing
    listing = db.query(VendorProduct).filter(
        VendorProduct.id == payload.vendor_product_id,
    ).first()
 
    if not listing:
        raise HTTPException(status_code=404, detail="Vendor listing not found.")
 
    if not listing.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{listing.crop_name}' is currently not available."
        )
 
    # Step 2 — Check minimum order quantity
    if payload.quantity < listing.min_order_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Minimum order quantity for '{listing.crop_name}' is "
                f"{listing.min_order_quantity} {listing.unit}. "
                f"You requested {payload.quantity} {listing.unit}."
            )
        )
 
    # Step 3 — Check stock availability
    if payload.quantity > listing.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Not enough stock for '{listing.crop_name}'. "
                f"Available: {listing.stock_quantity} {listing.unit}, "
                f"Requested: {payload.quantity} {listing.unit}."
            )
        )
 
    # Step 4 — Calculate total and deduct stock
    total_amount           = round(payload.quantity * listing.price_per_unit, 2)
    listing.stock_quantity = round(listing.stock_quantity - payload.quantity, 3)
 
    # Mark listing unavailable if stock runs out
    if listing.stock_quantity <= 0:
        listing.is_available = False
 
    # Step 5 — Create order record
    tracking_id = f"VND-{uuid.uuid4().hex[:8].upper()}"
 
    order = VendorOrder(
        vendor_product_id = listing.id,
        crop_name         = listing.crop_name,
        price_per_unit    = listing.price_per_unit,
        unit              = listing.unit,
        quantity          = payload.quantity,
        total_amount      = total_amount,
        buyer_id          = buyer.id,
        buyer_type        = buyer_type,
        delivery_address  = payload.delivery_address,
        delivery_city     = payload.delivery_city,
        delivery_pincode  = payload.delivery_pincode,
        notes             = payload.notes,
        tracking_id       = tracking_id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
 
    # Step 6 — Return confirmation
    return {
        "message":      "Purchase order placed successfully.",
        "order_id":     order.id,
        "tracking_id":  tracking_id,
        "crop_name":    listing.crop_name,
        "quantity":     payload.quantity,
        "unit":         listing.unit,
        "total_amount": total_amount,
        "status":       order.status,
        "vendor_name":  listing.vendor.user.full_name if listing.vendor and listing.vendor.user else None,
    }
 
 



def get_my_vendor_orders(buyer: User, buyer_type: BuyerType, db: Session) -> list:
    """Returns all vendor purchases made by this farmer or user."""
    orders = db.query(VendorOrder).filter(
        VendorOrder.buyer_id   == buyer.id,
        VendorOrder.buyer_type == buyer_type,
    ).order_by(VendorOrder.created_at.desc()).all()
 
    return [
        {
            "order_id":     o.id,
            "crop_name":    o.crop_name,
            "quantity":     o.quantity,
            "unit":         o.unit,
            "total_amount": o.total_amount,
            "status":       o.status,
            "tracking_id":  o.tracking_id,
            "created_at":   o.created_at,
        }
        for o in orders
    ]
 
 
 
 
def get_vendor_order_detail(buyer: User, order_id: int, db: Session) -> VendorOrderResponse:
    """Returns full detail of a single vendor order."""
    order = db.query(VendorOrder).filter(
        VendorOrder.id       == order_id,
        VendorOrder.buyer_id == buyer.id,
    ).first()
 
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
 
    return order