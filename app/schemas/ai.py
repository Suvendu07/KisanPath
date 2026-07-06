from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional



class WeatherRequest(BaseModel):
    location : str

    
class WeatherCondition(BaseModel):
    temp_c : float
    humidity : int
    rainfall_mm : float
    wind_kph : float
    condition : str
    icon : str
    uv_index : float
    is_day : bool
    
    

class WeatherForecastDay(BaseModel):
    date : str
    max_temp_c : float
    min_temp_c : float
    avg_humidity : int
    total_rain_mm : float
    condition : str
    farming_tip : str

    


class WeatherResponse(BaseModel):
    location : str
    country : str
    current : WeatherCondition
    forecast : List[WeatherForecastDay]
    season : str
    sowing_alert : Optional[str] = None
    
    
    
class ChatMessage(BaseModel):
    role : str
    content : str

    

class ChatRequest(BaseModel):
    message : str
    session_id : str
    language : str = "English"
    history : List[ChatMessage] = []
    
    
    @field_validator("message")
    @classmethod
    def message_not_empty(cls, value):
        
        if not value.strip():
            raise ValueError("Message can't be empty.")
        
        return value.strip()
    
    


class ChatResponse(BaseModel):
    reply : str
    session_id : str
    history : List[ChatMessage]
    
    
    
class RagRequest(BaseModel):
    question : str
    top_k : int = 3
    
    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Question can't be empty.")
        return v.strip()
    
    
class RagSource(BaseModel):
    source : str
    page : int
    excerpt : str

    
    
class RagResponse(BaseModel):
    answer : str
    sources : List[RagSource]
    question : str

    
    
    
class AgentRequest(BaseModel):
    query : str
    location : Optional[str] = None
    context : Optional[str] = None
    
    
class AgentStep(BaseModel):
    step_name : str
    input : str
    output : str
    tool_used : Optional[str] = None
    
    
class AgentResponse(BaseModel):
    final_answer : str
    steps : List[AgentStep]
    total_steps : int

    
class Diseaseinfo(BaseModel):
    disease_name : str
    confidence : float
    serverity : str
    cause : str
    symptoms : str
    treatment : str
    prevention : str
    is_healthy : bool
    
    
class DiseaseDetectionResponse(BaseModel):
    weed_name : str
    confidence : float
    is_weed : bool
    description : str
    control_method : str

    
class PricePredictionRequest(BaseModel):
    crop_name : str
    state : str
    month : int
    year : int
    
    @field_validator("month")
    @classmethod
    def month_valid(cls, value):
        if not (1 <= value <= 12):
            raise ValueError("Month must be between 1 and 12.")
        return value
    
    
    @field_validator("year")
    @classmethod
    def valid_year(cls, value):
        if value < 2020:
            raise ValueError("Year must be 2020 or later.")
        return value
    
    
class PricePredictionResponse(BaseModel):
    crop_name : str
    state : str
    month : int
    year : int
    prediction_price : float
    price_range : dict
    confidence : str
    trend : str
    note : str
    model_ready : bool

    
    
class CropRecommendRequest(BaseModel):
    nitrogen : float
    phosphorus : float
    potassium : float
    ph : float
    location : str

    @field_validator("ph")
    @classmethod
    def valid_ph(cls, value):
        if not (0 <= value <= 14):
            raise ValueError("PH must be between 0 and 14.")
        
        return value
    
    
    
class CropRecommendResponse(BaseModel):
    recommended_crop : str
    cofidence : float
    top_3_crops : List[dict]
    weather_used : WeatherCondition
    growing_tips : str
    best_season : str
    model_ready : bool

    
    
class FertilizerRecommendRequest(BaseModel):
    crop_name : str
    nitrogen : float
    phosphorus : float
    potassium : float
    soil_type : str

    
class FertilizerRecommendResponse(BaseModel):
    crop_name : str
    soil_type : str
    fertilizer_name : str
    description : str
    how_to_apply : str
    quantity_per_acer : str
    npk_suggestion : dict
    note : str