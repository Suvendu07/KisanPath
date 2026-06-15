from pydantic import BaseModel
from typing import Optional
from datetime import datetime


from app.models.payment_model import PaymentStatus, OrderType




class PaymentInitiateRequest(BaseModel):
    order_type : OrderType
    order_id : int
    
    
    
class PaymentVerifyRequest(BaseModel):
    razorpay_order_id : str
    razorpay_payment_id : str
    razorpay_signature : str

    
class PaymentVerifyResponse(BaseModel):
    success : bool
    message : str
    payment_id : int
    status : PaymentStatus
    
    

class RefundRequest(BaseModel):
    payment_id : int
    refund_amount : Optional[float] = None
    reason : Optional[str] = None
    
    
    
class RefundResponse(BaseModel):
    success : bool
    message : str
    refund_id : str
    refund_amount : float
    
    
    
class PaymentHistoryItem(BaseModel):
    id: int
    order_type : OrderType
    product_order_id: Optional[int]
    vendor_order_id: Optional[int]
    razorpay_order_id: str
    razorpay_payment_id:  Optional[str]
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime
    paid_at: Optional[datetime]
 
    model_config = {"from_attributes": True}