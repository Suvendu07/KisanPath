from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.permision import require_admin
from app.models.user_model import User
from app.schemas.ai import(
    ChatRequest, ChatResponse,
    RagRequest, RagResponse,
    WeatherRequest, WeatherResponse,
    DiseaseDetectionResponse,
    WeedDetectionResponse,
    PricePredictionRequest, PricePredictionResponse,
    CropRecommendRequest,CropRecommendResponse,
    FertilizerRecommendRequest, FertilizerRecommendResponse,
    AgentRequest, AgentResponse
)

from app.services import langchain_service, rag_service, langgraph_agent, weather_service, ml_service



router = APIRouter(tags=["AI"])


def handle_service_error(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

        
        
@router.post("/chat")
def chat(payload : ChatRequest, current_user : User = Depends(get_current_user)):
    
    return handle_service_error(langchain_service.chat_with_agri_ai, payload)




@router.post("/ask-docs")
def ask_docs(payload : RagRequest, current_user : User = Depends(get_current_user),):
    
    return handle_service_error(rag_service.ask_farming_docs, payload)




@router.post("/agent")
def farming_agent(payload : AgentRequest, current_user : User = Depends(get_current_user),):
    
    return handle_service_error(langgraph_agent.run_farming_agent, payload)




@router.get("/weather")
def get_weather(location : str, current_user : User = Depends(get_current_user),):
    
    return handle_service_error(weather_service.get_current_weather, location)




@router.post("/disease-detection", response_model=DiseaseDetectionResponse,)
def detect_disease(file : UploadFile = File(...), current_user : User = Depends(get_current_user),):
    
    return handle_service_error(ml_service.predict_disease, file)




@router.post("/weed-detection", response_model=WeedDetectionResponse)
def detect_weed(file : UploadFile = File(...), current_user : User = Depends(get_current_user),):
    
    return handle_service_error(ml_service.predict_weed, file)




@router.post("/price-prediction", response_model=PricePredictionRequest,)
def predict_price(payload : PricePredictionRequest, current_user : User = Depends(get_current_user)):
    
    return handle_service_error(ml_service.predict_price, payload)




@router.post("/crop-recommend", response_model=CropRecommendRequest)
def recommend_crop(payload : CropRecommendRequest, current_user : User = Depends(get_current_user),):
    
    return handle_service_error(ml_service.recommend_crop, payload)




@router.post("/fertilizer-recommend", response_model=FertilizerRecommendRequest,)
def recommend_fertilizer(payload : FertilizerRecommendRequest, current_user : User = Depends(get_current_user),):
    
    return handle_service_error(ml_service.recommend_fertilizer, payload)




@router.post("/rebuild-knowledge")
def rebuild_knowledge_base(current_user : User = Depends(require_admin),):
    
    return handle_service_error(rag_service.rebuild_vector_store)