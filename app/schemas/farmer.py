from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

from app.models.product_model import ProductCategory, ProductUnit


class FarmerProfileUpdate(BaseModel):
    farm_name:       Optional[str]   = None
    farm_size_acres: Optional[float] = None
    farm_location:   Optional[str]   = None
    aadhar_number:   Optional[str]   = None
    kisan_id:        Optional[str]   = None
    bio:             Optional[str]   = None

    # These come from the base User table
    full_name:       Optional[str]   = None
    phone:           Optional[str]   = None
    address:         Optional[str]   = None
    city:            Optional[str]   = None
    state:           Optional[str]   = None
    pincode:         Optional[str]   = None


class FarmerProfileResponse(BaseModel):
    id:              int
    farm_name:       Optional[str]
    farm_size_acres: Optional[float]
    farm_location:   Optional[str]
    farm_image:      Optional[str]
    aadhar_number:   Optional[str]
    kisan_id:        Optional[str]
    is_approved:     bool
    bio:             Optional[str]
    created_at:      datetime

    # Nested user info
    full_name:       str
    email:           str
    phone:           Optional[str]
    city:            Optional[str]
    state:           Optional[str]

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name:           str
    description:    Optional[str]  = None
    category:       ProductCategory = ProductCategory.OTHER
    price_per_unit: float
    unit:           ProductUnit     = ProductUnit.KG
    stock_quantity: float           = 0.0
    is_organic:     bool            = False

    @field_validator("price_per_unit")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than zero.")
        return v

    @field_validator("stock_quantity")
    @classmethod
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("Stock quantity cannot be negative.")
        return v


class ProductUpdate(BaseModel):
    name:           Optional[str]           = None
    description:    Optional[str]           = None
    category:       Optional[ProductCategory] = None
    price_per_unit: Optional[float]         = None
    unit:           Optional[ProductUnit]   = None
    stock_quantity: Optional[float]         = None
    is_available:   Optional[bool]          = None
    is_organic:     Optional[bool]          = None


class ProductResponse(BaseModel):
    id:             int
    farmer_id:      int
    name:           str
    description:    Optional[str]
    category:       ProductCategory
    image:          Optional[str]
    price_per_unit: float
    unit:           ProductUnit
    stock_quantity: float
    average_rating: float
    total_ratings:  int
    is_available:   bool
    is_organic:     bool
    created_at:     datetime
    updated_at:     datetime

    # Farmer info (for public product pages)
    farmer_name:    Optional[str] = None
    farmer_city:    Optional[str] = None

    model_config = {"from_attributes": True}