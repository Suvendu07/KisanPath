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
    
    
    
def get_profile(user):
    
    return {
        "id" : user.id,
        "full_name" : user.full_name,
        "email" : user.email,
        "phone" : user.phone,
        "adress" : user.adress,
        "city" : user.city,
        "state" : user.state,
        "pincode" : user.pincode,
        "profile_image" : user.profile_image,
        "created_at" : user.created_at,
        }
    
    
    

def update_profile(payload, user , db):
    
    for field, value in payload.model_dump(exclude_none = True).items():
        setattr(user, field, value)
         
    db.commit()
    db.refresh(user)
    
    return {
        "message" : "Profile updated successfully"
    }