import os
import uuid
import shutil

from fastapi import (status,HTTPException,Depends,UploadFile
)

from sqlalchemy.orm import (Session,joinedload
)

from app.config import settings
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.models.farmer_product_model import Product
from app.models.order_model import OrderItem
from app.models.vendor_order import VendorOrder, BuyerType

from app.schemas.farmer import (
    ProductResponse,
    FarmerProfileResponse,
    FarmerProfileUpdate,
    ProductCreate,
    ProductUpdate
)


from app.core.permision import require_farmer
from app.database import get_db


from app.models.order_model import Order, OrderStatus
from app.models.payment_model import OrderType
from app.services import tracking_service
 
 

FARMER_TRANSITIONS = {OrderStatus.CONFIRMED:  OrderStatus.PROCESSING,OrderStatus.PROCESSING: OrderStatus.SHIPPED,}


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}



def get_farmer_by_user(
    user: User,
    db: Session
):

    farmer = db.query(Farmer).filter(
        Farmer.user_id == user.id
    ).first()

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer profile not found"
        )

    return farmer



def get_farmer(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    return get_farmer_by_user(current_user, db)



def save_upload(
    file: UploadFile,
    subfolder: str
) -> str:

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, WEBP are allowed"
        )

    folder = os.path.join(
        settings.UPLOAD_DIR,
        subfolder
    )

    os.makedirs(folder, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1]

    filename = f"{uuid.uuid4()}.{ext}"

    filepath = os.path.join(
        folder,
        filename
    )

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return f"/uploads/{subfolder}/{filename}"




def build_profile_response(
    farmer: Farmer,
    user: User
) -> dict:

    return {
        "id": farmer.id,
        "farm_name": farmer.farm_name,
        "farm_size_acres": farmer.farm_size_acres,
        "farm_location": farmer.farm_location,
        "farm_image": farmer.farm_image,
        "is_approved": farmer.is_approved,

        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "city": user.city,
        "state": user.state,
        "profile_image": user.profile_image
    }



def product_response(
    product: Product
) -> dict:

    data = ProductResponse.model_validate(
        product
    ).model_dump()

    if product.farmer and product.farmer.user:

        data["farmer_name"] = (
            product.farmer.user.full_name
        )

        data["farmer_city"] = (
            product.farmer.user.city
        )

    return data



def get_dashboard(
    user: User,
    db: Session
):

    farmer = get_farmer_by_user(user, db)

    total_products = db.query(Product).filter(
        Product.farmer_id == farmer.id
    ).count()

    active_products = db.query(Product).filter(
        Product.farmer_id == farmer.id,
        Product.is_available == True
    ).count()

    total_orders = db.query(OrderItem).join(
        Product
    ).filter(
        Product.farmer_id == farmer.id
    ).count()

    return {
        "farmer_name": user.full_name,
        "is_approved": farmer.is_approved,
        "total_products": total_products,
        "active_products": active_products,
        "total_orders": total_orders
    }



def get_profile(
    user: User,
    db: Session
):

    farmer = get_farmer_by_user(user, db)

    return build_profile_response(
        farmer,
        user
    )



def update_profile(
    payload,
    farmer,
    user,
    db: Session
):

    farmer_fields = [
        "farm_name",
        "farm_size_acres",
        "farm_location",
        "aadhar_number",
        "kisan_id",
        "bio"
    ]

    for field in farmer_fields:

        value = getattr(payload, field)

        if value is not None:
            setattr(farmer, field, value)

    user_fields = [
        "full_name",
        "phone",
        "address",
        "city",
        "state",
        "pincode"
    ]

    for field in user_fields:

        value = getattr(payload, field)

        if value is not None:
            setattr(user, field, value)

    db.commit()

    db.refresh(farmer)

    return build_profile_response(
        farmer,
        user
    )



def upload_image(
    image,
    farmer,
    db: Session
):

    path = save_upload(
        image,
        "farmer_image"
    )

    farmer.farm_image = path
    
    if farmer.user:
        farmer.user.profile_image = path


    db.commit()

    db.refresh(farmer)

    return {
        "message": "Image uploaded successfully",
        "image_url": path
    }



def list_products(
    farmer,
    db: Session
):

    products = (
        db.query(Product)
        .options(
            joinedload(Product.farmer)
            .joinedload(Farmer.user)
        )
        .filter(
            Product.farmer_id == farmer.id
        )
        .all()
    )

    return [
        product_response(product)
        for product in products
    ]



def create_products(
    payload,
    image,
    farmer,
    db: Session
):

    if not farmer.is_approved:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your farmer account must be approved "
                "by admin before listing products."
            )
        )

    image_path = None

    if image:
        image_path = save_upload(
            image,
            "product_images"
        )

    new_product = Product(
        farmer_id=farmer.id,
        image=image_path,
        **payload.model_dump()
    )

    db.add(new_product)

    db.commit()

    db.refresh(new_product)

    return {
        "message": "Product created successfully",
        "product_id": new_product.id
    }



def update_product(
    product_id,
    payload,
    farmer,
    db: Session
):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.farmer_id == farmer.id
    ).first()

    if not product:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    for key, value in payload.model_dump(
        exclude_none=True
    ).items():

        setattr(product, key, value)

    db.commit()

    db.refresh(product)

    return {
        "message": "Product updated successfully"
    }



def delete_product(
    product_id,
    farmer,
    db: Session
):

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.farmer_id == farmer.id
    ).first()

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)

    db.commit()

    return {
        "message": "Product deleted successfully"
    }




def upload_product_image(farmer, product_id : int, file : UploadFile, db : Session) -> dict:
    
    product = db.query(Product).filter(Product.id == product_id, Product.farmer_id == farmer.id).first()
    
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    
    path = save_upload(file, "product_images")
    product.image = path
    db.commit()
    
    return{
        "message" : "Product image updated.","image_url" : f"/{path}"
    }
    
    


def get_farmer_orders(
    farmer,
    db: Session
) -> list:

    items = (
        db.query(OrderItem)
        .join(Product)
        .options(
            joinedload(OrderItem.order)
        )
        .filter(
            Product.farmer_id == farmer.id
        )
        .all()
    )

    result = []

    seen_orders = set()

    for item in items:

        order = item.order

        if order and order.id not in seen_orders:

            seen_orders.add(order.id)

            result.append({
                "order_id": order.id,
                "status": order.status,
                "created_at": order.created_at,
                "final_amount": order.final_amount,
                "tracking_id": order.tracking_id,
            })

    return result




def update_order_status(farmer, order_id , new_status : OrderStatus, db : Session) -> dict:
    
    # has_item = (db.query(OrderItem).join(Product).filter(OrderItem.order_id == order_id, Product.farmer_id == farmer.id).first()
    #             )
    
    has_item = (
    db.query(OrderItem)
    .join(Product, OrderItem.product_id == Product.id)
    .join(Farmer, Product.farmer_id == Farmer.id)
    .filter(
        OrderItem.order_id == order_id,
        Farmer.user_id == farmer.id
    )
    .first()
)    
    
    if not has_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or doesn't contain your products.")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    
    allowed_next = FARMER_TRANSITIONS.get(order.status)
    
    
    # if new_status not in FARMER_ALLOWED_STATUSES:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN, detail="Farmers can pn;y set status to 'processing' or 'shipped'."
    #         "delivery and cancellation are handled by admin/buyer."
    #     )
    if allowed_next is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order is currently '{order.status.value}'."
                            "You can no longer update its status from here.")
        
        
    if new_status != allowed_next:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"From '{order.status.value}' you can only move the order to "
                            f"'{allowed_next.value}'.")
        
    


    # if order.status in (OrderStatus.CANCELLED, OrderStatus.DELIVERED):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"can't update - order is already '{order.status}'.")
    
    
    order.status = new_status
    tracking_service.add_tracking_event(db , OrderType.PRODUCT, order.id, new_status.value)
    db.commit()
    
    
    return {
        "message" : f"Order #{order.id} markedd as '{new_status.value}'."
    }    
    
    
    
    
def get_order_tracking(farmer, order_id : int , db : Session) -> dict:
    
    has_item = db.query(OrderItem).join(Product).filter(OrderItem.order_id == order_id, Product.farmer_id == Farmer.id).first()
    
    if not has_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or does't contain your products.")
    
    
    order = db.query(Order).filter(Order.id == order_id).first()
    events = tracking_service.get_timeline_events(db, OrderType.PRODUCT, order_id)
    
    
    return {
        "order_id":                 order.id,
        "order_type":               "product",
        "current_status":           order.status,
        "tracking_id":              order.tracking_id,
        "estimate_delivery_date":  order.estimate_delivery_date,
        "timeline":                 events,
    }



# def get_order_tracking(farmer, order_id, db : Session):
    
#     vendor_order = db.query(VendorOrder).filter(VendorOrder.id == order_id, VendorOrder.buyer_id == farmer.id, VendorOrder.buyer_type == BuyerType.FARMER).first()
    
#     if not vendor_order:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendot order not found.")
    
#     events = tracking_service.get_timeline_events(
#         db , OrderType.VENDOR, vendor_order.id,
#     )
    
    
#     return {
#         "order_id" : vendor_order.id,
#         "order_type" : "vendor",
#         "current_status" : vendor_order.status,
#         "tracking_id" : vendor_order.tracking_id,
#         "estimated_delivery_date" : vendor_order.estimated_delivery_date,
#         "timeline" : events
#     }