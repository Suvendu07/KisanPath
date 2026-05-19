from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date

from app.models.mandi_model import PriceUnit


class VendorProfileUpdate(BaseModel):
    business_name:    Optional[str] = None
    business_type:    Optional[str] = None
    gst_number:       Optional[str] = None
    license_number:   Optional[str] = None
    mandi_name:       Optional[str] = None
    mandi_location:   Optional[str] = None
    bio:              Optional[str] = None

    # From the base User table
    full_name:        Optional[str] = None
    phone:            Optional[str] = None
    address:          Optional[str] = None
    city:             Optional[str] = None
    state:            Optional[str] = None
    pincode:          Optional[str] = None


class VendorProfileResponse(BaseModel):
    id:               int
    business_name:    str
    business_type:    Optional[str]
    gst_number:       Optional[str]
    license_number:   Optional[str]
    mandi_name:       Optional[str]
    mandi_location:   Optional[str]
    is_approved:      bool
    bio:              Optional[str]
    created_at:       datetime

    # Nested user info
    full_name:        str
    email:            str
    phone:            Optional[str]
    city:             Optional[str]
    state:            Optional[str]

    model_config = {"from_attributes": True}


class MandiPriceCreate(BaseModel):
    crop_name:      str
    crop_variety:   Optional[str]  = None
    min_price:      float
    max_price:      float
    modal_price:    float
    unit:           PriceUnit       = PriceUnit.QUINTAL
    mandi_name:     str
    mandi_location: Optional[str]  = None
    state:          Optional[str]  = None
    price_date:     date
    notes:          Optional[str]  = None

    @field_validator("max_price")
    @classmethod
    def max_must_be_gte_min(cls, v, info):
        min_price = info.data.get("min_price")
        if min_price is not None and v < min_price:
            raise ValueError("max_price must be >= min_price.")
        return v

    @field_validator("modal_price")
    @classmethod
    def modal_between_min_max(cls, v, info):
        min_p = info.data.get("min_price")
        max_p = info.data.get("max_price")
        if min_p is not None and max_p is not None:
            if not (min_p <= v <= max_p):
                raise ValueError("modal_price must be between min_price and max_price.")
        return v


class MandiPriceUpdate(BaseModel):
    crop_name:      Optional[str]       = None
    crop_variety:   Optional[str]       = None
    min_price:      Optional[float]     = None
    max_price:      Optional[float]     = None
    modal_price:    Optional[float]     = None
    unit:           Optional[PriceUnit] = None
    mandi_name:     Optional[str]       = None
    mandi_location: Optional[str]       = None
    state:          Optional[str]       = None
    price_date:     Optional[date]      = None
    notes:          Optional[str]       = None


class MandiPriceResponse(BaseModel):
    id:             int
    vendor_id:      int
    crop_name:      str
    crop_variety:   Optional[str]
    min_price:      float
    max_price:      float
    modal_price:    float
    unit:           PriceUnit
    mandi_name:     str
    mandi_location: Optional[str]
    state:          Optional[str]
    price_date:     date
    notes:          Optional[str]
    created_at:     datetime

    # Vendor info for display
    vendor_name:    Optional[str] = None

    model_config = {"from_attributes": True}