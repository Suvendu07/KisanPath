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
    
    
    

def browse_product(category, search, min_price, max_price, is_organic, db : Session):
    
    query = db.query(Product).filter(Product.is_available == True, Product.stock_quantity > 0,)
    
    
    if category:
        query = query.filter(Product.category == category)
        
    if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
            
    if min_price:
        query = query.filter(Product.price_per_unit >= min_price)
        
    if max_price is not None:
        query = query.filter(Product.price_per_unit <= max_price)
        
    
    if is_organic is not None:
        query = query.filter(Product.is_organic == is_organic)
        
        
    products = query.order_by(Product.created_at.desc()).all

    
    result = []
    for p in products:
        farmer = db.query(Farmer).filter(Farmer.id == p.farmer_id).first()
        result.append({
            "id":             p.id,
            "name":           p.name,
            "category":       p.category,
            "image":          p.image,
            "price_per_unit": p.price_per_unit,
            "unit":           p.unit,
            "stock_quantity": p.stock_quantity,
            "average_rating": p.average_rating,
            "total_ratings":  p.total_ratings,
            "is_organic":     p.is_organic,
            "farmer_name":    farmer.user.full_name if farmer and farmer.user else None,
            "farmer_city":    farmer.user.city      if farmer and farmer.user else None,
        })
    return result