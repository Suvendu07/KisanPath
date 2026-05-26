from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.product_model import Product
from app.models.feedback_model import Feedback
from app.models.farmer_model import Farmer
from app.schemas.user import UserProfileUpdate, OrderCreate, OrderResponse, FeedbackCreate



DELIVERY_CHARGE = 40.0


