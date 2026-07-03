from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import User, UserRole
from app.models.farmer_model import Farmer
from app.models.vendor_model import Vendor
from app.models.vendor_order import VendorOrder
from app.models.farmer_product_model import Product
from app.models.order_model import Order, OrderStatus
from app.models.payment_model import OrderType
from app.schemas.admin import (
    DashboardStats,
    UserListItem,
    AdminUserUpdate,
    ApprovalAction,
    OrderStatusUpdate,
    AdminVendorOrderStatusUpdate,
)

from app.services import tracking_service


def get_dashboard(db: Session) -> DashboardStats:
    all_orders = db.query(Order).all()
    revenue_sum = sum(
        o.final_amount for o in all_orders if o.status == "delivered"
    )

    return DashboardStats(
        total_users = db.query(User).count(),
        total_farmers = db.query(User).filter(User.role == UserRole.FARMER).count(),
        total_vendors = db.query(User).filter(User.role == UserRole.VENDOR).count(),
        total_buyers = db.query(User).filter(User.role == UserRole.USER).count(),
        total_products = db.query(Product).count(),
        total_orders = db.query(Order).count(),
        pending_orders = db.query(Order).filter(Order.status == "pending").count(),
        total_revenue = round(revenue_sum, 2),
        pending_farmer_approvals = db.query(Farmer).filter(Farmer.is_approved == False).count(),
        pending_vendor_approvals = db.query(Vendor).filter(Vendor.is_approved == False).count(),
    )




def list_users(
    db: Session,
    role: str  = None,
    is_active: bool = None,
    search: str  = None,
) -> list:
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%")
        )
    users = query.order_by(User.created_at.desc()).all()
    return [UserListItem.model_validate(u) for u in users]






def get_user(user_id: int, db: Session) -> UserListItem:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserListItem.model_validate(user)





def update_user(user_id: int, payload: AdminUserUpdate, db: Session) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    db.commit()
    return {"message": f"User {user_id} updated successfully."}





def delete_user(user_id: int, current_user: User, db: Session) -> None:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot delete their own account."
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()






def list_farmers(is_approved: bool, db: Session) -> list:
    query = db.query(Farmer)
    if is_approved is not None:
        query = query.filter(Farmer.is_approved == is_approved)

    return [
        {
            "farmer_id": f.id,
            "user_id": f.user_id,
            "full_name": f.user.full_name if f.user else None,
            "email": f.user.email     if f.user else None,
            "farm_name": f.farm_name,
            "farm_location": f.farm_location,
            "is_approved": f.is_approved,
            "kisan_id" : f.kisan_id,
            "created_at": f.created_at,
        }
        for f in query.all()
    ]





def approve_farmer(farmer_id: int, payload: ApprovalAction, db: Session) -> dict:
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    farmer.is_approved = payload.approve
    db.commit()

    action = "approved" if payload.approve else "rejected"
    return {"message": f"Farmer account {action} successfully."}





def list_vendors(is_approved: bool, db: Session) -> list:
    query = db.query(Vendor)
    if is_approved is not None:
        query = query.filter(Vendor.is_approved == is_approved)

    return [
        {
            "vendor_id": v.id,
            "user_id": v.user_id,
            "full_name": v.user.full_name  if v.user else None,
            "email": v.user.email      if v.user else None,
            "business_name":  v.business_name,
            "business_type":  v.business_type,
            "gst_number": v.gst_number,
            "license_number": v.license_number,
            "mandi_name": v.mandi_name,
            "is_approved": v.is_approved,
            "created_at": v.created_at,
        }
        for v in query.all()
    ]



def approve_vendor(vendor_id: int, payload: ApprovalAction, db: Session) -> dict:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    vendor.is_approved = payload.approve
    db.commit()

    action = "approved" if payload.approve else "rejected"
    return {"message": f"Vendor account {action} successfully."}






def list_all_orders(order_status: str, db: Session) -> list:
    query = db.query(Order)
    if order_status:
        query = query.filter(Order.status == order_status)

    return [
        {
            "order_id": o.id,
            "buyer_name": o.buyer.full_name if o.buyer else None,
            "status": o.status,
            "final_amount": o.final_amount,
            "tracking_id": o.tracking_id,
            "created_at": o.created_at,
        }
        for o in query.order_by(Order.created_at.desc()).all()
    ]




def list_all_vendor_orders(order_status: str, db: Session) -> list:
    query = db.query(VendorOrder)
    if order_status:
        query = query.filter(VendorOrder.status == order_status)

    return [
        {
            "order_id": o.id,
            "buyer_id": o.buyer_id,
            "buyer_type": o.buyer_type,
            "vendor_id": o.vendor_product_model.vendor_id if o.vendor_product_model else None,
            "crop_name": o.crop_name,
            "quantity": o.quantity,
            "unit": o.unit,
            "status": o.status,
            "total_amount": o.total_amount,
            "created_at": o.created_at,
        }
        for o in query.order_by(VendorOrder.created_at.desc()).all()
    ]
    
    
    

def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    order.status = payload.status
    if payload.tracking_id:
        order.tracking_id = payload.tracking_id
        
    if payload.notes:
        order.notes = payload.notes
        
    if payload.status == "delivered":
        order.delivered_at = datetime.utcnow()
        
    tracking_service.add_tracking_event(
        db, OrderType.PRODUCT, order.id, status=payload.status.value if hasattr(payload.status, "value") else payload.status,
        custom_description=payload.notes,
    )
    

    db.commit()
    return {"message": f"Order {order_id} status updated to '{payload.status}'."}



def update_vendor_order_status(order_id: int, payload: AdminVendorOrderStatusUpdate, db: Session) -> dict:
    order = db.query(VendorOrder).filter(VendorOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Vendor order not found.")

    order.status = payload.status
    if payload.tracking_id:
        order.tracking_id = payload.tracking_id
        
    tracking_service.add_tracking_event(
        db, OrderType.VENDOR, order.id, status=payload.status.value if hasattr(payload.status, "value") else payload.status,
        custom_description=payload.notes,
    )
    
    db.commit()
    return {"message": f"Vendor Order {order_id} status updated to '{payload.status}'."}



def list_all_products(is_available: bool, db: Session) -> list:
    query = db.query(Product)
    if is_available is not None:
        query = query.filter(Product.is_available == is_available)

    return [
        {
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price_per_unit,
            "stock": p.stock_quantity,
            "is_available": p.is_available,
            "farmer_id": p.farmer_id,
        }
        for p in query.all()
    ]




def delete_product(product_id: int, db: Session) -> None:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    db.delete(product)
    db.commit()