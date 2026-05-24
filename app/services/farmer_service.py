import os
import uuid
import shutil

from fastapi import (
    status,
    HTTPException,
    Depends,
    UploadFile
)

from sqlalchemy.orm import (
    Session,
    joinedload
)

from app.config import settings
from app.models.user_model import User
from app.models.farmer_model import Farmer
from app.models.product_model import Product
from app.models.order_model import OrderItem

from app.schemas.farmer import (
    ProductResponse
)

from app.core.permision import require_farmer
from app.database import get_db


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