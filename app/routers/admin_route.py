from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.permision import require_admin
from app.models.user_model import User
from app.schemas.admin import (
    DashboardStats,
    AdminUserUpdate,
    ApprovalAction,
    OrderStatusUpdate,
)
from app.services import admin_service

router = APIRouter(prefix="/admin")




@router.get("/dashboard", response_model=DashboardStats, summary="Platform overview stats")
def admin_dashboard(
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.get_dashboard(db)




@router.get("/users", summary="List all users")
def list_users(
    role:         str  = None,
    is_active:    bool = None,
    search:       str  = None,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.list_users(db, role, is_active, search)




@router.get("/users/{user_id}", summary="Get any user's detail")
def get_user(
    user_id:      int,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.get_user(user_id, db)




@router.put("/users/{user_id}", summary="Update any user's details")
def update_user(
    user_id:      int,
    payload:      AdminUserUpdate,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.update_user(user_id, payload, db)




@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
def delete_user(
    user_id:      int,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    admin_service.delete_user(user_id, current_user, db)




@router.get("/farmers", summary="List all farmer profiles")
def list_farmers(
    is_approved:  bool = None,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.list_farmers(is_approved, db)




@router.put("/farmers/{farmer_id}/approve", summary="Approve or reject a farmer")
def approve_farmer(
    farmer_id:    int,
    payload:      ApprovalAction,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.approve_farmer(farmer_id, payload, db)




@router.get("/vendors", summary="List all vendor profiles")
def list_vendors(
    is_approved:  bool = None,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.list_vendors(is_approved, db)




@router.put("/vendors/{vendor_id}/approve", summary="Approve or reject a vendor")
def approve_vendor(
    vendor_id:    int,
    payload:      ApprovalAction,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.approve_vendor(vendor_id, payload, db)




@router.get("/orders", summary="List all orders on the platform")
def list_all_orders(
    order_status: str  = None,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.list_all_orders(order_status, db)




@router.put("/orders/{order_id}/status", summary="Update any order's status")
def update_order_status(
    order_id:     int,
    payload:      OrderStatusUpdate,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.update_order_status(order_id, payload, db)




@router.get("/products", summary="List all products on the platform")
def list_all_products(
    is_available: bool = None,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    return admin_service.list_all_products(is_available, db)




@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove any product")
def delete_product(
    product_id:   int,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    admin_service.delete_product(product_id, db)