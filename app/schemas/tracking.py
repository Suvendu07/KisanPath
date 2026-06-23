from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


from app.models.order_model import OrderStatus
from app.models.vendor_order import VendorOrderStatus



class TrackingEvent(BaseModel):
    status : str
    title : str
    description : Optional[str]
    location : Optional[str]
    created_at : datetime
    
    model_config = {"from_attributes": True}
    
    
class OrderTrackingReponse(BaseModel):
    order_id : int
    order_type : str
    current_status : str
    tracking_id : Optional[str]
    estimate_deliver_date : Optional[date]
    timeline : List[TrackingEvent]
    
    
    
class FarmerOrderStatusUpdate(BaseModel):
    status : OrderStatus
    
    
class VendorOrderStatusupdate(BaseModel):
    status : VendorOrderStatus