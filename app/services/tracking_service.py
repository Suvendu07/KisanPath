from datetime import datetime, timedelta, timezone, date

from sqlalchemy.orm import Session

from app.models.payment_model import OrderType
from app.models.order_tracking import OrderTracking



STATUS_MESSAGES = {
    "pending" : {
        "title" : "Order Placed",
        "description" : "your order has been placed. waiting for payment confirmation."
    },
    
    "confirmed" : {
        "title" : "order confirmed",
        "description" : "Payment received. your order has been confrimed.",
    },
    
    "processing" : {
        "title" : "Preparing your order.",
        "description" : "The seller is packing your order.",
    },
    
    "shipped" : {
        "title" : "Order shipped",
        "description" : "Your order has left the seller and is on its way.",
    },
    
    "out_for_delivery" : {
        "title" : "Out for delivery",
        "description" : "Your order is out for delivery and will arive today.",
    },
    
    
    "delivered" : {
        "title":       "Delivered",
        "description": "Your order has been delivered. Thank you for shopping with KisanPath!",
    },
    
    "cancelled": {
        "title":       "Order Cancelled",
        "description": "This order has been cancelled.",
    },            
}



ESTIMATED_DELIVERY_DAYS  = 5


def estimate_delivery_date() -> date:
    """Simple flat estimate, set when payment is confirmed."""
    return (datetime.now(timezone.utc) + timedelta(days=ESTIMATED_DELIVERY_DAYS)).date()




def add_tracking_event(
    db : Session, order_type : OrderType, order_id : int, status : str, location : str = None, custom_title : str = None, custom_description : str = None,
) -> OrderTracking:
    
    message = STATUS_MESSAGES.get(status, {
        "title" : status.replace("_", "").title(),
        "description" : f"Order statu updated to '{status}'.",
    })
    
    
    event = OrderTracking(
        order_type = order_type,
        product_order_id = order_id if order_type == OrderType.PRODUCT else None,
        vendot_order_id = order_id if order_type == OrderType.VENDOR else None,
        status = status,
        title = custom_title or message["title"],
        description = custom_description or message["description"],
        location = location,
    )
    
    db.add(event)
    db.flush()
    return event




def get_timeline_events(db: Session, order_type: OrderType, order_id: int) -> list:
    """Raw timeline rows, oldest → newest. Ownership checks happen in the caller."""
  
    query = db.query(OrderTracking)
    
    if order_type == OrderType.PRODUCT:
        query = query.filter(OrderTracking.product_order_id == order_id)
        
    else:
        query = query.filter(OrderTracking.vendor_order_id == order_id)
    return query.order_by(OrderTracking.created_at.asc()).all()