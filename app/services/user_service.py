from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.product_model import Product
from app.models.feedback_model import Feedback
from app.models.farmer_model import Farmer
from app.models.order_model import Order, OrderItem
import uuid



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
        
        
    products = query.order_by(Product.created_at.desc()).all()

    
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




def place_order(payload, user , db):
    
    total_amount = 0.0
    order_items = []
    
    
    for item_in in payload.items:
        product = db.query(Product).filter(Product.id == item_in.product_id,
                                           Product.is_available == True,).first()
        
        
        if not product:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product id {item_in.product_id} not found or unavailable.")
    
    
        if product.stock_quantity < item_in.quantity:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for '{product.name}'."
                             f"Available: {product.stock_quantity} {product.unit}")
        
        
        
        subtotal = round(item_in.quantity * product.price_per_unit , 2)
        total_amount += subtotal
    
    
    
    
        order_items.append(OrderItem(
            product_id= product.id,
            product_name= product.name,
            quantity= item_in.quantity,
            unit= product.unit,
            price_per_unit = product.price_per_unit,
            subtotal= subtotal,
    ))
    
    
        product.stock_quantity -=item_in.quantity
        
    
     
    final_amount = round(total_amount + DELIVERY_CHARGE, 2)
    tracking_id  = f"AGR-{uuid.uuid4().hex[:8].upper()}"
 
    order = Order(
        buyer_id         = user.id,
        delivery_address = payload.delivery_address,
        delivery_city    = payload.delivery_city,
        delivery_pincode = payload.delivery_pincode,
        total_amount     = round(total_amount, 2),
        delivery_charge  = DELIVERY_CHARGE,
        final_amount     = final_amount,
        tracking_id      = tracking_id,
        notes            = payload.notes,
    )
    db.add(order)
    db.flush()
 
    for item in order_items:
        item.order_id = order.id
        db.add(item)
 
    db.commit()
    db.refresh(order)
    return {
        "message":     "Order placed successfully.",
        "order_id":    order.id,
        "tracking_id": tracking_id,
    }





def list_order(user , db):
    
    orders = db.query(Order).filter(Order.buyer_id == user.id).order_by(Order.created_at.desc()).all()
    
    
    return [
        {
            "order_id":    o.id,
            "status":      o.status,
            "final_amount":o.final_amount,
            "tracking_id": o.tracking_id,
            "created_at":  o.created_at,
            "items_count": len(o.items),
        }
        for o in orders
    ]
 
 
 
 
def get_order_details(order_id, user, db):
    
    details = db.query(Order).filter(Order.id == order_id, Order.buyer_id == user.id).first()
    
    
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    
    return details



