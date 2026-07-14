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
def chat(payload : ChatRequest, current_user = Depends(get_current_user)):
    
    return handle_service_error(langchain_service.chat_with_agri_ai, payload)



