from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.product_model import Product
from app.models.feedback_model import Feedback
from app.models.farmer_model import Farmer
from app.models.order_model import Order




DELIVERY_CHARGE = 40.0




def get_dashboard(user , db : Session):
    
    total_orders = db.query(Order).filter(Order.buyer_id == user.id).count()
    
    pending_orders = db.query(Order).filter(Order.buyer_id == user.id , Order.status == "pending",).count()
    
    deliverd_orders = db.query(Order).filter(Order.buyer_id == user.id, Order.status == "delivered",).count()
    
    
    total_feedback = db.query(Feedback).filter(Feedback.user_id == user.id).count()
    
    
    return {
        "buyer_name" : user.full_name,
        "total_order" : total_orders,
        "pending_orders" : pending_orders,
        "delivered_orders" : deliverd_orders,
        "total_feedback" : total_feedback,
    }