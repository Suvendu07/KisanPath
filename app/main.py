from fastapi import FastAPI
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth_route import router as auth_router
from app.models import user_model, farmer_model, vendor_model, product_model, order_model, feedback_model, mandi_model
from app.routers.admin_route import router as admin_router
from app.routers.farmer_route import router as farmer_router
from fastapi.staticfiles import StaticFiles


Base.metadata.create_all(bind=engine)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/home")
def home_page():
    return {
        "messsage" : "page loaded"
    }
    
    
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(farmer_router)