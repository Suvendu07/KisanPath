from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from app.models.order_model import OrderStatus


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone:     Optional[str] = None
    address:   Optional[str] = None
    city:      Optional[str] = None
    state:     Optional[str] = None
    pincode:   Optional[str] = None


class OrderItemIn(BaseModel):
    """One product line inside an order."""
    product_id: int
    quantity:   float

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than zero.")
        return v


class OrderCreate(BaseModel):
    items:            List[OrderItemIn]
    delivery_address: str
    delivery_city:    Optional[str] = None
    delivery_pincode: Optional[str] = None
    notes:            Optional[str] = None

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Order must have at least one item.")
        return v


class OrderItemResponse(BaseModel):
    id:             int
    product_id:     Optional[int]
    product_name:   str
    quantity:       float
    unit:           str
    price_per_unit: float
    subtotal:       float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id:               int
    buyer_id:         Optional[int]
    delivery_address: str
    delivery_city:    Optional[str]
    delivery_pincode: Optional[str]
    total_amount:     float
    delivery_charge:  float
    final_amount:     float
    status:           OrderStatus
    tracking_id:      Optional[str]
    notes:            Optional[str]
    created_at:       datetime
    updated_at:       datetime
    delivered_at:     Optional[datetime]
    items:            List[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    product_id: int
    order_id:   int
    rating:     float
    title:      Optional[str] = None
    review:     Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v):
        if not (1.0 <= v <= 5.0):
            raise ValueError("Rating must be between 1 and 5.")
        return round(v, 1)


class FeedbackResponse(BaseModel):
    id:         int
    user_id:    int
    product_id: int
    order_id:   Optional[int]
    rating:     float
    title:      Optional[str]
    review:     Optional[str]
    image:      Optional[str]
    created_at: datetime

    # Display names
    user_name:    Optional[str] = None
    product_name: Optional[str] = None

    model_config = {"from_attributes": True}