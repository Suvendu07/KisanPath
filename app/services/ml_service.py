import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from PIL import Image
import io


from app.schemas.ai import (
    DiseaseDetectionResponse, Diseaseinfo,
    WeedDetectionResponse, WeedInfo,
    PricePredictionRequest, PricePredictionResponse,
    CropRecommendRequest, CropRecommendResponse,
    FertilizerRecommendRequest, FertilizerRecommendResponse,
    WeatherCondition,
)

from app.services.weather_service import get_weather_for_crop_recommendation



BASE = Path(__file__).resolve().parent.parent.parent / "ml_models"
DISEASE = BASE / "crop_disease"
WEED = BASE / "weed_detection"
PRICE = BASE / "crop_price"
CROP_REC = BASE / "crop_recommender"


class ModelRegistry:
    
    def __int__(self):
        self.disease_model = None
        self.disease_labels = None
        self.weed_model = None
        self.weed_labels = None
        self.price_model = None
        self.price_encoders = None
        self.price_features = None
        self.crop_rec_model = None
        self.crop_rec_encoder = None
        self.crop_rec_scaler = None
        self.crop_rec_info = None
        
        
    def load_all(self):
        self.load_disease()
        self.load_weed()
        self.load_price()
        self.load_crop_rec()
        
        print("ML model registry initialized.")
        
        
    def _load_disease(self):
        try:
            import tensorflow as tf
            mp = DISEASE / "model.h5"
            lp = DISEASE / "class_labels.json"
            
            if mp.exists() and lp.exists():
                self.disease_model = tf.keras.models.load_model(str(mp))
                self.disease_labels = json.load(open(lp))
                
                print("crop disease model loaded.")
                
            else:
                print("Crop disease model not found yet.")
                
                
        except Exception as e:
            print(f" Disease model error: {e}")
            
            
    def _load_weed(self):
        try:
            import tensorflow as tf
            mp = WEED / "model.h5"
            lp = WEED / "class_labels.json"
            if mp.exists() and lp.exists():
                self.weed_model = tf.keras.load_model(str(mp))
                self.weed_labels = json.load(open(lp))
                print("weed detection model loaded.")
                
            else:
                print("weed model not found yet")
                
                
        except Exception as e:
            print(f"Weed model error : {e}")
            
            
    def _load_price(self):
        try:
            mp = PRICE / "model.pkl"
            ep = PRICE / "encoders.pkl"
            fp = PRICE / "feature_columns.json"
            
            if mp.exists():
                self.price_model = pickle.load(open(mp, "rb"))
                self.price_encoders = pickle.load(open(ep, "rb"))
                self.price_features = json.load(open(fp))
                print("crop price model loaded.")
                
            else:
                print("crop price model not found yet.")
                
        except Exception as e:
            print(f" Price model error : {e}")
            
            
    
    def _load_crop_rec(self):
        try:
            mp = CROP_REC / "model.pkl"
            lep = CROP_REC / "label_encoder.pkl"
            sp = CROP_REC / "scaler.pkl"
            ip = CROP_REC / "model_info.json"
            if mp.exists():
                self.crop_rec_model = pickle.load(open(mp,  "rb"))
                self.crop_rec_encoder = pickle.load(open(lep, "rb"))
                self.crop_rec_scaler = pickle.load(open(sp,  "rb"))
                self.crop_rec_info = json.load(open(ip))
                print(" Crop recommender model loaded.")
            else:
                print(" Crop recommender not found yet.")
        except Exception as e:
            print(f"Crop recommender error: {e}")
 
 
registry = ModelRegistry()




def preprocess_image(file : UploadFile, size = (224,224)) -> np.ndarray:
    
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Only JPEG, PNG, or Webp images are allowed.")
        
        
    content = file.file.read()
    img = Image.open(io.BytesIO(content)).convert("RGB").resize(size)
    arr = np.array(img) / 255.0
    return np.expand_dims(arr, axis=0)




DISEASE_DB = {
    "healthy": {
        "severity": "None",
        "cause":    "No disease detected.",
        "symptoms": "Plant appears healthy.",
        "treatment":"No treatment needed.",
        "prevention":"Continue good agronomic practices.",
    },
    "default": {
        "severity": "Moderate",
        "cause":    "Fungal, bacterial, or viral pathogen.",
        "symptoms": "Visible spots, discoloration, or lesions on leaves.",
        "treatment":"Apply appropriate fungicide/bactericide. Remove affected parts.",
        "prevention":"Ensure proper spacing, drainage, crop rotation.",
    },
}




def get_disease_info(name : str) -> dict:
    return DISEASE_DB["healthy"] if "healthy" in name.lower() else DISEASE_DB["default"]




def predict_disease(file : UploadFile) -> DiseaseDetectionResponse:
    
    if registry.disease_model is None:
        stub = Diseaseinfo(
            disease_name="Model not loaded yet",
            confidence=0.0, serverity="N/A",
            cause="Traing in progress",
            symptoms="N/A", treatment="N/A", prevention="N/A",
            is_healthy=False,
        )
        
        
        return DiseaseDetectionResponse(
            success = False, top_preict = stub,
            predictions = [stub], model_ready = False,
        )
        
        
    arr = preprocess_image(file)
    preds = registry.disease_model.predict(arr)[0]
    top3 = preds.argsort()[-3:][::-1]
    results = []
    
    
    
    for idx in top3:
        name = registry.disease_labels.get(str(idx), "Unknown")
        info = get_disease_info(name)
        results.append(Diseaseinfo(
            disease_name=name.replace("_", " ").title(),
            confidence = round(float(preds[idx]) * 100, 2),
            serverity=info["serverity"],
            cause=info["cause"],
            symptoms=info["symptoms"],
            treatment=info["treatment"],
            prevention=info["prevention"],
            is_healthy="healthy" in name.lowe(),
        ))
        
        
    return DiseaseDetectionResponse(
        success = True, top_prediction = results[0],
        predictions = results, model_ready = True,
    )
    
    
    
    
WEED_DB = {
    "Negative": {
        "description":    "No weed detected. Field is clean.",
        "control_method": "No action needed.",
    },
    "default": {
        "description":    "Invasive weed competing with crops for nutrients.",
        "control_method": "Apply selective herbicide or manual removal at early stage.",
    },
}




def predict_weed(file : UploadFile) -> WeedDetectionResponse:
    if registry.weed_model is None:
        stub = WeedInfo(
            weed_name="Model not loaded yet",
            confidence=0.0, is_weed=False,
            description="Training in progress.",
            control_method="N/A",
        )
        
        return WeedDetectionResponse(
            success=False, top_prediction=stub,predictions=[stub], weed_detected=False, model_ready=False,
        )
        
        
    arr = preprocess_image(file)
    preds = registry.weed_model.predict(arr)[0]
    top3 = preds.argsort()[-3:][::-1]
    results = []
    
    
    for idx in top3:
        name = registry.weed_labels.get(str(idx), "Unknown")
        details = WEED_DB.get(name , WEED_DB["default"])
        results.append(WeedInfo(
            weed_name=name,
            confidence=round(float(preds[idx]) * 100, 2),
            is_weed=name != "Negative",
            description=details["description"],
            control_method=details["control_method"],
        ))
        
        
    return WeedDetectionResponse(
        success=True, top_prediction=results[0],
        predictions=results,
        weed_detected=results[0].is_weed,
        model_ready=True,
    )
    
    


def predict_price(payload : PricePredictionRequest) -> PricePredictionResponse:
    
    if registry.price_model is None:
        return PricePredictionResponse(
            crop_name=payload.crop_name, state=payload.state,
            month=payload.month, year = payload.year,
            prediction_price=0.0, price_range={"min" : 0, "max" : 0},
            confidence = "N/A", trend="N/A",
            note="Price prediction model not loaded yet. Training in progress.",
            model_ready=False,
        )
        
        
    le_crop = registry.price_encoders["crop"]
    le_state = registry.price_encoders["state"]
    
    
    if payload.crop_name not in le_crop.classes_:
        raise HTTPException(
            status_code=400, detail=f"Crop '{payload.crop_name}' not in training data."
        )
          
    if payload.state not in le_state:
        raise HTTPException(
            status_code=400, detail=f"state '{payload.state}' not in training data."
        )
        
    
    X = np.array([[
        le_crop.transform([payload.crop_name])[0],
        le_state.transform([payload.state])[0],
        payload.month, payload.year,
    ]])
    
    predicted = round(float(registry.price_model.predict(X)[0]), 2)
    margin = predicted * 0.10
    trend = ("Rising"  if payload.month in [10,11,12,1] else
             "Falling" if payload.month in [4,5,6] else "Stable")
    
    
    return PricePredictionResponse(
        crop_name=payload.crop_name, state=payload.state,
        month = payload.month, year = payload.year,
        prediction_price=predicted,
        price_range={"min" : round(predicted - margin, 2), "max" : round(predicted + margin, 2)},
        confidence="high" if registry.price_features.get("r2", 0) > 0.8 else "Medium",
        trend=trend,
        note=f"Predicted model price for {payload.crop_name} in {payload.state} : {predicted}/quintal.",
        model_ready=True
    )    
    
    
    
    
    
GROWING_TIPS = {
    "rice":      "Needs standing water. Best in hot humid climate.",
    "wheat":     "Cool weather crop. Sow November–December.",
    "maize":     "Warm season. Needs well-drained soil.",
    "default":   "Follow local agronomic practices for best yield.",
}
BEST_SEASON = {
    "rice":      "Kharif (June–November)",
    "wheat":     "Rabi (November–April)",
    "maize":     "Kharif / Zaid",
    "default":   "Consult local agriculture department.",
}




def recommend_crop(payload : CropRecommendRequest) -> CropRecommendResponse:
    
    weather_data = get_weather_for_crop_recommendation(payload.location)
    
    
    weather_obj = WeatherCondition(
        temp_c = weather_data["temperature"],
        humidity=int(weather_data["humidity"]),
        rainfall_mm=weather_data["rainfall"],
        wind_kph=0.0,
        condition="Live data fetched",
        icon="",
        uv_index=0.0,
        is_day=True,
    )
    
    
    if registry.crop_rec_model is None:
        stub = {"crop" : "Model not loaded", "confidence": 0.0}
        return CropRecommendResponse(
            recommended_crop="Model not loaded.",
            confidence = 0.0,
            top_3_crops=[stub],
            weather_used=weather_obj,
            growing_tips="Training in progress.",
            best_season="N/A", model_ready=False,
        )
        
        
        
    x = np.array([[
        payload.nitrogen,
        payload.phosphorus,
        payload.potassium,
        weather_data["temperature"],
        weather_data["humidity"],
        payload.ph,
        weather_data["rainfall"],
    ]])
    
    
    X_scaled = registry.crop_rec_scaler.transform(x)
    proba = registry.crop_rec_model.predict_prob(X_scaled)[0]
    top3_idx = proba.argsort()[-3:][::-1]
    
    top3 = [
        {"crop": registry.crop_rec_encoder.classes_[i],
         "confidence": round(float(proba[i]) * 100, 2)}
        for i in top3_idx
    ]
    
    
    best = top3[0]["crop"]
    
    return CropRecommendResponse(
        recommended_crop=best,
        confidence = top3[0]["confidence"],
        top_3_crops=top3,
        weather_used=weather_obj,
        growing_tips=GROWING_TIPS.get(best, GROWING_TIPS["default"]),
        best_season=BEST_SEASON.get(best, BEST_SEASON["default"]),
        model_ready=True,
    )
    
    
    
def recommend_fertilizer_rule_based(
    crop_name : str,
    nitrogen : float,
    phosphorus : float,
    potassium : float,
    soil_type : str,
) -> dict:
    
    from app.ml_models.fertilizer.recommender import recommend_fertilizer
    return recommend_fertilizer(crop_name, nitrogen, phosphorus, potassium, soil_type)



def recommend_fertilizer(payload : FertilizerRecommendRequest) -> FertilizerRecommendResponse:
    
    result = recommend_fertilizer_rule_based(
        payload.crop_name, payload.nitrogen,
        payload.phosphorus, payload.potassium, payload.soil_type,
    )
    
    return FertilizerRecommendResponse(**result, note=result.get("note", ""))
