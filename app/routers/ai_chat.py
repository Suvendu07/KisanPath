from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.schemas.ai import ChatRequest
from app.services.langchain_service import chat_with_agri_ai
from app.models.user_model import User
from app.core.dependencies import get_current_user


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
    
    return handle_service_error(chat_with_agri_ai, payload)