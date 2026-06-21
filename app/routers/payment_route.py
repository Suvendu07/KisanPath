from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session


from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.permision import require_admin
from app.models.user_model import User
from app.models.payment_model import OrderType
from app.schemas.payment import PaymentInitiateRequest, PaymentInitiateResponse, PaymentVerifyRequest, PaymentVerifyResponse, RefundRequest, RefundResponse


from app.services import payment_service


router = APIRouter(prefix="/Payment", tags=["Payment"])


@router.post("/initiate", response_model=PaymentInitiateResponse)
def initiate_payment(payload : PaymentInitiateRequest, current_user : User = Depends(get_current_user), db : Session = Depends(get_db),):
    
    return payment_service.initiate_payment(payload, current_user, db)



@router.post("/verify", response_model= PaymentVerifyResponse)
def verify_payment(payload : PaymentVerifyRequest, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    
    return payment_service.verify_payment(payload, current_user, db)



@router.post("/cancel")
def cancel_order(order_type : OrderType, order_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    
    return payment_service.cancel_order(order_type, order_id, current_user, db)




@router.get("/history")
def payment_history(current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    
    return payment_service.get_payment_history(current_user, db)




@router.post("/refund", response_model=RefundResponse)
def refund_payment(payload : RefundRequest, current_user : User = Depends(require_admin), db : Session = Depends(get_db)):
    
    return payment_service.refund_payment(payload, db)




@router.get("/admin/all")
def all_payment(pay_status : str = None, order_type : str = None, current_user : User = Depends(require_admin), db : Session = Depends(get_db),):
    
    from app.models.payment_model import Payment, PaymentStatus
    
    query = db.query(Payment)
    if pay_status:
        query = query.filter(Payment.status == pay_status)
        
    if order_type:
        query = query.filter(Payment.order_type == order_type)
        
        
    payments = query.order_by(Payment.created_at.desc()).all()
    
    
    return [
        {
            "id":                  p.id,
            "payer_name":          p.payer.full_name if p.payer else None,
            "order_type":          p.order_type,
            "amount":              p.amount,
            "status":              p.status,
            "razorpay_order_id":   p.razorpay_order_id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "created_at":          p.created_at,
            "paid_at":             p.paid_at,
        }
        for p in payments
    ]