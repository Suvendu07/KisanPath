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
    if not settings.RA