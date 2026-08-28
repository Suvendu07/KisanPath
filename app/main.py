from fastapi import FastAPI
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth_route import router as auth_router
from app.models import farmer_product_model, user_model, farmer_model, vendor_model, order_model, feedback_model, mandi_model, vendor_order, vendor_product_model, payment_model, order_tracking, agent_session
from app.routers.admin_route import router as admin_router
from app.routers.farmer_route import router as farmer_router
from app.routers.vendor_route import router as vendor_router
from app.routers.user_route import router as user_router
from app.routers.payment_route import router as payment_router
from app.routers.ai_chat import router as ai_router
from app.routers.agent import router as agent_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from app.config import settings
import os




BASE_DIR = Path(__file__).resolve().parent.parent


# Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev only). In production, use Alembic migrations."""
 
    # Import all models here so Base knows about them before create_all
    from app.models import farmer_product_model, user_model, farmer_model, vendor_model, order_model, feedback_model, mandi_model, vendor_order, vendor_product_model, payment_model, order_tracking, agent_session
    Base.metadata.create_all(bind=engine)
 
    # Create required directories
    os.makedirs(settings.UPLOAD_DIR,        exist_ok=True)
    os.makedirs(settings.KNOWLEDGE_BASE_DIR,exist_ok=True)
    os.makedirs(settings.VECTOR_STORE_DIR,  exist_ok=True)
 
    # Load all ML models once at startup
    from app.services.ml_service import registry
    registry.load_all()
 
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    print("Application shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agriculture Platform API — Admin, Farmer, User, Vendor",
    docs_url="/docs",        # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:5174", 
        "http://127.0.0.1:5174",
        "http://localhost:3000"
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

@app.get("/home")
def home_page():
    return {
        "messsage" : "page loaded"
    }
    
    
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(farmer_router)
app.include_router(vendor_router)
app.include_router(user_router)
app.include_router(payment_router)
app.include_router(ai_router)
app.include_router(agent_router)