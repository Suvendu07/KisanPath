from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.config import settings



GEMINI_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "models/embedding-001"



def _check_key() -> None:
    
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
            "Add it to your .env file."
            
        )
        
        
def get_llm(temperature : float = 0.7, max_tokens : int = 1024) -> ChatGoogleGenerativeAI:
    
    _check_key()
    return ChatGoogleGenerativeAI(
        model = GEMINI_MODEL,
        google_api_key = settings.GEMINI_API_KEY,
        temperature = temperature,
        max_tokens = max_tokens,
    )
    
    
def get_strict_llm() -> ChatGoogleGenerativeAI:
    
    _check_key()
    return ChatGoogleGenerativeAI(
        model = GEMINI_MODEL,
        google_api_key = settings.GEMINI_API_KEY,
        temperature = 0.4,
        max_tokens = 2048,
    )
    
def get_creative_llm() -> ChatGoogleGenerativeAI:
   
    _check_key()
    return ChatGoogleGenerativeAI(
        model = GEMINI_MODEL,
        google_api_key = settings.GEMINI_API_KEY,
        temperature = 0.4,
        max_tokens = 2048,
    )

def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    
    _check_key()
    return GoogleGenerativeAIEmbeddings(
        model = EMBEDDING_MODEL,
        google_api_key = settings.GEMINI_API_KEY,
    )