from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

from app.models.vendor_product_model import BulkUnit
from app.models.vendor_order import VendorOrderStatus, BuyerType




class VendorProductCreate(BaseModel):
    crop_name : str
    crop_variety : Optional[str] = None
    description : Optional[str] = None
    price_per_unit : float
    unit : BulkUnit = BulkUnit.QUINTAL
    stock_quantity : float
    min_order_quantity : float = 1.0
    available_at : Optional[str] = None
    
    
    
    @field_validator("price_per_unit")
    @classmethod
    def price_positive(cls, value):
        
        if value <= 0:
            raise ValueError("Price must be greater than zero")
        
        return value
    
    
    @field_validator("stock_quantity")
    @classmethod
    def stock_non_negative(cls, value):
        
        if value < 0:
            raise ValueError("Stock quantity can't be negative")
        
        return value
    
    
    @field_validator("min_order_quantity")
    @classmethod
    def min_order_positive(cls , value):
        
        if value <= 0:
            raise ValueError("Minimum order quantity must be greater than zerro")
        
        return value
    
    
    

class VendorProductUpdate(BaseModel):
    crop_name : Optional[str] = None
    crop_variety : Optional[str] = None
    description : Optional[str] = None
    price_per_unit : Optional[float] = None
    unit : Optional[BulkUnit] = None
    stock_quantity : Optional[float] = None
    min_order_quantity : Optional[float] = None
    available_at : Optional[str] = None
    is_available : Optional[bool] = None
    
    
    


class VendorProductResponse(BaseModel):
    id : int
    vendor__id : int
    crop_name : str
    crop_veriety : Optional[str]
    description : Optional[str]
    price_per_unit:  float
    unit:  BulkUnit
    stock_quantity: float
    min_order_quantity: float
    available_at:  Optional[str]
    is_available:  bool
    created_at:  datetime
    updated_at:  datetime
 

    vendor_name:        Optional[str] = None
    vendor_location:    Optional[str] = None
 
    model_config = {"from_attributes": True}
    
    
    


class VendorPurchaseRequest(BaseModel):
    vendor_product_id: int
    quantity:  float
    delivery_address:  str
    delivery_city:  Optional[str] = None
    delivery_pincode:  Optional[str] = None
    notes:  Optional[str] = None
 
    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than zero.")
        return v
 
 
 

class VendorOrderResponse(BaseModel):
    id: int
    vendor_product_id:  Optional[int]
    crop_name: str
    price_per_unit:     float
    unit:  str
    quantity: float
    total_amount: float
    buyer_id: Optional[int]
    buyer_type: BuyerType
    delivery_address: str
    delivery_city: Optional[str]
    delivery_pincode: Optional[str]
    status: VendorOrderStatus
    tracking_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime]
 
    model_config = {"from_attributes": True}
 