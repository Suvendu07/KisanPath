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