import hmac
import hashlib
from datetime import datetime
from typing import Optional


import razorpay
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


from app.config import settings
from app.models.user_model import User
from app.models.order_model import Order, OrderStatus
from app.models.vendor_order import VendorOrder, VendorOrderStatus
from app.models.payment_model import payment, PaymentStatus, OrderType
from app.schemas.payment import PaymentInitiateRequest, PaymentInitiateResponse,PaymentVerifyResponse, PaymentVerifyRequest,RefundRequest, RefundResponse




def get_razorpay_client() -> razorpay.Client:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Razorpay keys not configured. Add them..")
        
        return razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        

def initiate_payment(payer : User, payload : PaymentInitiateRequest, db : Session,) -> PaymentInitiateResponse:
    
    amount = None
    product_order = None
    vendor_order = None
    
    
    if payload.order_type == OrderType.PRODUCT:
        product_order = db.query(Order).filter(
            Order.id == payload.order_id,
            Order.buyer_id == payer.id,
        ).first()
        
        
        if not product_order:
            raise HTTPException(status_code=404, detail="Product order not found.")
        
        if product_order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Order is already '{product_order.status}'. Cannot initiate payment.")
            
        amount = product_order.final_amount
        
        
    elif payload.order_type == OrderType.VENDOR:
        vendor_order = db.query(VendorOrder).filter(
            VendorOrder.id == payload.order_id,
            VendorOrder.buyer_id == payer.id,
        ).first()
        
        
        if not vendor_order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor order not found")
        
        
        
        if vendor_order.status != VendorOrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Order is already '{vendor_order.status}'. Cannot initiate payment.")
            
            
        amount = vendor_order.total_amount
        
    existing_payment = None
    if payload.order_type == OrderType.PRODUCT:
        existing_payment = db.query(payment).filter(
            payment.product_order_id == payload.order_id,
            payment.status.in_([PaymentStatus.CREATED, PaymentStatus.PAID]),
        ).first()
    else:
        existing_payment = db.query(payment).filter(
            payment.vendor_order_id == payload.order_id,
            payment.status.in_([PaymentStatus.CREATED, PaymentStatus.PAID]),
        ).first()
 
    if existing_payment and existing_payment.status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This order has already been paid."
        )
 

    client = get_razorpay_client()
 
    # Razorpay expects amount in paise (1 INR = 100 paise)
    amount_paise = int(amount * 100)
 
    rzp_order = client.order.create({
        "amount":   amount_paise,
        "currency": "INR",
        "payment_capture": 1,   # auto-capture on payment success
        "notes": {
            "order_type": payload.order_type,
            "order_id":   payload.order_id,
            "payer_id":   payer.id,
            "payer_name": payer.full_name,
        }
    })
 

    payment = payment(
        payer_id          = payer.id,
        order_type        = payload.order_type,
        product_order_id  = product_order.id if product_order else None,
        vendor_order_id   = vendor_order.id  if vendor_order  else None,
        razorpay_order_id = rzp_order["id"],
        amount            = amount,
        currency          = "INR",
        status            = PaymentStatus.CREATED,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
 
    return PaymentInitiateResponse(
        razorpay_order_id = rzp_order["id"],
        amount            = amount,
        currency          = "INR",
        payment_id        = payment.id,
        key_id            = settings.RAZORPAY_KEY_ID,
    )
 
 

def verify_payment(
    payer:   User,
    payload: PaymentVerifyRequest,
    db:      Session,
) -> PaymentVerifyResponse:
    """
    Step 2 of payment flow.
    Called by frontend after Razorpay popup closes with success.
    - Verifies the HMAC-SHA256 signature (prevents fraud)
    - Marks payment as PAID
    - Updates the order status to CONFIRMED
    """
 
    # Find the payment record
    payment = db.query(payment).filter(
        payment.razorpay_order_id == payload.razorpay_order_id,
        payment.payer_id == payer.id,
    ).first()
 
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")
 
    if payment.status == PaymentStatus.PAID:
        return PaymentVerifyResponse(
            success = True,
            message = "Payment already verified.",
            payment_id = payment.id,
            status = payment.status,
        )
 

    # Razorpay signs: razorpay_order_id + "|" + razorpay_payment_id
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected  = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
 
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        # Signature mismatch — mark as failed
        payment.status = PaymentStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed. Possible fraud attempt."
        )
 

    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature  = payload.razorpay_signature
    payment.status = PaymentStatus.PAID
    payment.paid_at = datetime.utcnow()
 

    if payment.order_type == OrderType.PRODUCT and payment.product_order_id:
        order = db.query(Order).filter(Order.id == payment.product_order_id).first()
        if order:
            order.status = OrderStatus.CONFIRMED
 
    elif payment.order_type == OrderType.VENDOR and payment.vendor_order_id:
        v_order = db.query(VendorOrder).filter(
            VendorOrder.id == payment.vendor_order_id
        ).first()
        if v_order:
            v_order.status = VendorOrderStatus.CONFIRMED
 
    db.commit()
 
    return PaymentVerifyResponse(
        success = True,
        message = "Payment verified successfully. Order confirmed.",
        payment_id = payment.id,
        status = PaymentStatus.PAID,
    )
 
 

def refund_payment(payload: RefundRequest, db: Session) -> RefundResponse:
    """
    Admin issues a refund via Razorpay.
    - Full refund if refund_amount is None
    - Partial refund if refund_amount is specified
    """
    payment = db.query(payment).filter(payment.id == payload.payment_id).first()
 
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
 
    if payment.status != PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund a payment with status '{payment.status}'."
        )
 
    if not payment.razorpay_payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay payment ID missing. Cannot process refund."
        )
 
    refund_amount = payload.refund_amount or payment.amount
    if refund_amount > payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund amount ₹{refund_amount} exceeds paid amount ₹{payment.amount}."
        )
 

    client = get_razorpay_client()
 
    refund = client.payment.refund(
        payment.razorpay_payment_id,
        {
            "amount": int(refund_amount * 100),   # paise
            "notes":  {"reason": payload.reason or "Requested by admin"},
        }
    )
 

    payment.status  = PaymentStatus.REFUNDED
    payment.refund_id  = refund["id"]
    payment.refund_amount = refund_amount
    payment.refund_reason = payload.reason
 
    # Cancel the linked order
    if payment.order_type == OrderType.PRODUCT and payment.product_order_id:
        order = db.query(Order).filter(Order.id == payment.product_order_id).first()
        if order:
            order.status = OrderStatus.CANCELLED
 
    elif payment.order_type == OrderType.VENDOR and payment.vendor_order_id:
        v_order = db.query(VendorOrder).filter(
            VendorOrder.id == payment.vendor_order_id
        ).first()
        if v_order:
            v_order.status = VendorOrderStatus.CANCELLED
 
    db.commit()
 
    return RefundResponse(
        success = True,
        message = f"Refund of ₹{refund_amount} processed successfully.",
        refund_id = refund["id"],
        refund_amount = refund_amount,
    )
 
 


def cancel_order(
    user: User,
    order_type: OrderType,
    order_id: int,
    db: Session,
) -> dict:
    """
    User cancels an order BEFORE paying.
    Simply marks the order as CANCELLED and restores stock.
    """
    if order_type == OrderType.PRODUCT:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.buyer_id == user.id,
        ).first()
 
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
 
        if order.status not in [OrderStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status '{order.status}'. "
                       "Only pending orders can be cancelled."
            )
 
        # Restore stock for each item
        from app.models.farmer_product_model import Product
        for item in order.items:
            if item.product_id:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()
                if product:
                    product.stock_quantity += item.quantity
                    product.is_available    = True
 
        order.status = OrderStatus.CANCELLED
 
    elif order_type == OrderType.VENDOR:
        v_order = db.query(VendorOrder).filter(
            VendorOrder.id == order_id,
            VendorOrder.buyer_id == user.id,
        ).first()
 
        if not v_order:
            raise HTTPException(status_code=404, detail="Vendor order not found.")
 
        if v_order.status not in [VendorOrderStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status '{v_order.status}'."
            )
 
        # Restore vendor stock
        from app.models.vendor_product_model import VendorProduct
        listing = db.query(VendorProduct).filter(
            VendorProduct.id == v_order.vendor_product_id
        ).first()
        if listing:
            listing.stock_quantity += v_order.quantity
            listing.is_available = True
 
        v_order.status = VendorOrderStatus.CANCELLED
 
    db.commit()
    return {"message": "Order cancelled successfully."}
 
 


def get_payment_history(user: User, db: Session) -> list:
    """Returns all payments made by a user."""
    payments = db.query(payment).filter(
        payment.payer_id == user.id
    ).order_by(payment.created_at.desc()).all()
 
    return [
        {
            "id": p.id,
            "order_type": p.order_type,
            "product_order_id": p.product_order_id,
            "vendor_order_id": p.vendor_order_id,
            "razorpay_order_id": p.razorpay_order_id,
            "razorpay_payment_id":  p.razorpay_payment_id,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "created_at": p.created_at,
            "paid_at": p.paid_at,
        }
        for p in payments
    ]