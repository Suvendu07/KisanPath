import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional



from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings


logger = logging.getLogger(__name__)
TMPL_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
BASE_TMPL = TMPL_DIR / "base.html"
APP_URL = "http:localhost:5173"




def get_mail_config() -> ConnectionConfig:
    
    return ConnectionConfig(
        MAIL_USERNAME= settings.MAIL_USER,
        MAIL_PASSWORD= settings.EMAIL_PASSWORD,
        MAIL_FROM= settings.MAIL_FROM,
        MAIL_FROM_NAME= settings.MAIL_FROM_NAME,
        MAIL_PORT= settings.EMAIL_PORT,
        MAIL_SERVER=settings.EMAIL_HOST,
        MAIL_STARTTLS=settings.MAIL_TLS,
        MAIL_SSL_TLS=settings.MAIL_SSL,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    
    
    
def render_template(template_name : str, data : dict) -> str:
    
    tmpl_path  = TMPL_DIR / template_name
    if not tmpl_path.exists():
        raise FileNotFoundError(f"Email template not found: {template_name}. Looked in: {tmpl_path.absolute()}")
    
    
    content = tmpl_path.read_text(encoding = "utf-8")
    base_html = BASE_TMPL.read_text(encoding = "utf-8")
    full_html = base_html.replace("{{content}}", content)
    
    
    
    data = {"app_url" : APP_URL, **data}
    for key, value in data.items():
        full_html = full_html.replace(f"{{{{{key}}}}}", str(value) if value is not None else "")
        
    return full_html
    
    
    
def plain_text(data : dict) -> str:
    
    lines = ["KisanPath -- India's Agriculture MarketPlace", "=" * 40]
    
    for k, v in data.items():
        
        if k not in ("app_url",) and v:
            lines.append(f"{k.replace('_',' ').title()}: {v}")
            
    lines += ["=" * 40, "© 2025 KisanPath. All rights reserved."]
    
    return "\n".join(lines)



async def send_mail(
    recipient : str,
    subject : str,
    template_name : str,
    data : dict,
) -> bool:
    
    if not settings.MAIL_ENABLED:
        logger.info(f"[MAIL OFF] would send '{subject}' to{recipient}")
        return True
    
    
    if not settings.MAIL_USER or not settings.EMAIL_PASSWORD:
        logger.warning("Mail credentials missing - skipping send.")
        return False
    
    
    try:
        html = render_template(template_name, {**data, "subject" : subject})
        msg = MessageSchema(
            subject = f"KisanPath - {subject}",
            recipients=[recipient],
            body=html,
            subtype=MessageType.html,
            alternative_body=plain_text(data),
        )
        
        
        await FastMail(get_mail_config()).send_message(msg)
        
        logger.info(f"Email sent : '{subject}' to {recipient}")
        
        return True
    
    except Exception as e:
        logger.error(f"Email failed to {recipient} : {e}")
        return False
    
    
    
    
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")



async def notify_order_placed(
    buyer_email: str,
    buyer_name: str,
    order_id: int,
    tracking_id: str,
    total_amount: float,
    delivery_charge:  float,
    final_amount: float,
    delivery_address: str,
    farmer_email: Optional[str]  = None,
    farmer_name: Optional[str]  = None,
    product_name: Optional[str]  = None,
    quantity: Optional[float]= None,
    unit: Optional[str]  = None,
    delivery_city: Optional[str]  = None,
) -> None:
    
    
    await send_mail(buyer_email, f"Order Placed - #{order_id}", "order_placed.html",{
        "buyer_name" : buyer_name,
        "order_id" : order_id,
        "tracking_id" : tracking_id,
        "total_amount" : f"{total_amount:.2f}",
        "delivery_charge" : f"{delivery_charge:.2f}",
        "final_amount" : f"{final_amount:.2f}",
        "delivery_address" : delivery_address,
    })
    
    
    if farmer_email and farmer_name:
         await send_mail(farmer_email, f"New Order — #{order_id}", "new_order_farmer.html", {
            "farmer_name": farmer_name,
            "order_id": order_id,
            "tracking_id": tracking_id,
            "product_name": product_name or "Your Product",
            "quantity": quantity or "",
            "unit": unit or "",
            "amount": f"{final_amount:.2f}",
            "delivery_city":delivery_city or delivery_address,
        })
 
 
 


async def notify_payment_confirmed(
    buyer_email: str,
    buyer_name: str,
    order_id: int,
    tracking_id: str,
    amount_paid: float,
    razorpay_payment_id: str,
    estimated_delivery: str,
    delivery_days: int = 5,
) -> None:
    
    await send_mail(buyer_email, f"Payment Confirmed — Order #{order_id}", "payment_confirmed.html", {
        "buyer_name": buyer_name,
        "order_id": order_id,
        "tracking_id": tracking_id,
        "amount_paid": f"{amount_paid:.2f}",
        "razorpay_payment_id": razorpay_payment_id,
        "estimated_delivery": estimated_delivery,
        "delivery_days": delivery_days,
    })
    
    
    
    
    
STATUS_CONFIG = {
    "processing":       ("Preparing Your Order",   "🔧", "badge-blue",   "Your order is being prepared."),
    "shipped":          ("Order Shipped",           "📦", "badge-blue",   "Your order is on its way!"),
    "out_for_delivery": ("Out for Delivery",        "🚚", "badge-orange", "Your order will arrive today!"),
    "delivered":        ("Delivered Successfully",  "✅", "badge-green",  "Thank you for shopping with KisanPath!"),
    "cancelled":        ("Order Cancelled",         "❌", "badge-red",    "Your order has been cancelled."),
}





async def notify_order_status_update(
    buyer_email: str,
    buyer_name: str,
    order_id: int,
    tracking_id: str,
    new_status: str,
    estimated_delivery: Optional[str] = None,
) -> None:
    cfg = STATUS_CONFIG.get(new_status, (
        new_status.replace("_", " ").title(), "📋", "badge-blue", ""
    ))
    await send_mail(buyer_email, f"Order Update — {cfg[0]}", "order_status_update.html", {
        "buyer_name": buyer_name,
        "order_id": order_id,
        "tracking_id": tracking_id,
        "status_title": cfg[0],
        "status_emoji": cfg[1],
        "badge_class": cfg[2],
        "status_label": new_status.replace("_", " ").upper(),
        "status_message": cfg[3],
        "updated_at": _now(),
        "estimated_delivery": estimated_delivery or "",
    })
    
    
    
async def notify_order_cancelled(
    buyer_email: str,
    buyer_name: str,
    order_id: int,
    tracking_id: str,
    cancel_reason: str  = "Cancelled by user",
    refund_applicable: bool = False,
    refund_amount: float= 0.0,
) -> None:
    await send_mail(buyer_email, f"Order Cancelled — #{order_id}", "order_cancelled.html", {
        "buyer_name": buyer_name,
        "order_id": order_id,
        "tracking_id": tracking_id,
        "cancelled_at": _now(),
        "cancel_reason": cancel_reason,
        "refund_applicable": "true" if refund_applicable else "",
        "refund_amount": f"{refund_amount:.2f}" if refund_applicable else "",
    })
    
    
    
async def notify_refund_issued(
    buyer_email: str,
    buyer_name: str,
    order_id: int,
    refund_id: str,
    refund_amount: float,
    refund_reason: str = "Refund requested",
) -> None:
    await send_mail(buyer_email, f"Refund Initiated — Rs.{refund_amount:.2f}", "refund_issued.html", {
        "buyer_name": buyer_name,
        "order_id": order_id,
        "refund_id": refund_id,
        "refund_amount": f"{refund_amount:.2f}",
        "refund_reason": refund_reason,
        "refunded_at": _now(),
    })
    
    
    
    
async def notify_vendor_order_placed(
    vendor_email: str,
    vendor_name: str,
    buyer_email: str,
    buyer_name: str,
    order_id: int,
    tracking_id: str,
    crop_name: str,
    quantity: float,
    unit: str,
    total_amount: float,
    buyer_type: str,
    delivery_address: str,
) -> None:
    # Vendor new order alert
    await send_mail(vendor_email, f"New Bulk Order — #{order_id}", "vendor_order_placed.html", {
        "seller_name": vendor_name,
        "order_id": order_id,
        "tracking_id": tracking_id,
        "crop_name": crop_name,
        "quantity": quantity,
        "unit": unit,
        "total_amount": f"{total_amount:.2f}",
        "buyer_type": buyer_type.upper(),
        "delivery_address":delivery_address,
    })
    # Buyer confirmation
    await send_mail(buyer_email, f"Bulk Order Placed — #{order_id}", "order_placed.html", {
        "buyer_name": buyer_name,
        "order_id": order_id,
        "tracking_id": tracking_id,
        "total_amount": f"{total_amount:.2f}",
        "delivery_charge": "0.00",
        "final_amount": f"{total_amount:.2f}",
        "delivery_address":delivery_address,
    })
 
 
 
 
async def notify_account_approved(
    user_email: str,
    user_name:  str,
    role: str,
) -> None:
    await send_mail(user_email, f"Your {role} Account is Approved!", "account_approved.html", {
        "user_name": user_name,
        "email": user_email,
        "role": role.title(),
        "approved_at": _now(),
    })