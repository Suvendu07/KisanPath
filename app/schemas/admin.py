from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.models.user_model import UserRole
from app.models.order_model import OrderStatus



class DashboardStatus(BaseModel):
    total_users : int
    total_farmers : int
    total_vendors : int
    total_buyers : int
    total_products : int
    total_orders : int
    pending_oders : int
    total_revenue : float
    pending_farmer_approvals : int
    pending_vendor_apprvals : int

    
    
class UserListItem(BaseModel):
    id : int
    full_name : str
    email = EmailStr
    phone : Optional[str]
    role : UserRole
    is_active : bool
    is_verified : bool
    created_at : datetime
    
    
    model_config = {"from_attributes" : True}
    
    
    
class AdminUserUpdate(BaseModel):
    full_name : Optional[str] = None
    phone : Optional[str] = None
    role : Optional[UserRole] = None
    is_active : Optional[bool] = None
    is_verified : Optional[bool] = None
    city : Optional[str] = None
    state : Optional[str] = None
    
    


class ApprovalAction(BaseModel):
    approve : bool
    reason : Optional[str] = None
    
    
class OrderStatusUpdate(BaseModel):
    status : OrderStatus
    tracking_id : Optional[str] = None
    notes : Optional[str] = None