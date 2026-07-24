import httpx
from datetime import datetime
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.ai import WeatherCondition, WeatherForecastDay, WeatherResponse




def detect_season(month : int) -> str:
    
    if month in [6,7,8,9,10,11]:
        return "Kharif"
    
    elif month in [11,12,1,2,3,4]:
        return "Rabi"
    
    else:
        return "Zaid"
    
    
def generate_farming_tip(condition : str, rain_mm : float, temp_c : float, humidity : int,) -> str:
    
    condition_lower = condition.lower()
    
    if rain_mm > 20:
        return "Heavy rainfall expected. Avoid spraying pesticides.Ensure field drainage."
    
    elif rain_mm > 5:
        return "Light rain expected. Good time to transplant seedings. Hold off on irrigation."
    
    
    
    elif temp_c > 40:
        return "Extreme heat expected. water your crops early moring or late evening only."
    
    elif temp_c < 10:
        return "Cold conditions. Cover nursery beds. Frost risk for sensitive crops."
    
    elif humidity > 85:
        return "High humidity. Watch for fungal diseases. Apply preventive fungicide if needed."
    
    elif "sunny" in condition_lower or "clear" in condition_lower:
        return "Clear sunny day. Good for harvesting and drying grains."
    
    elif "thunder" in condition_lower or "storm" in condition_lower:
        return "Thunderstorms likely. Secure farm equipment. Do not work in open fields."
    
    else:
        return "Moderate conditions. Good day for regular farm activities."
    
    
    
    
    
def check_showing_alert(temp_c : float, rain_mm : float, humidity : int) -> str | None:
    
    if rain_mm > 30:
        return "Heavy rainfall - delay sowing to avoid seed sowing."
    
    
    if temp_c > 42:
        return "Extreme heat - wait for temerature to drop before sowing."
    
    if temp_c < 8:
        return "Very cold condition - not suitable for most crops right now."
    
    if humidity > 90:
        return "Very high humidity - disease risk is high. Monitor closely after sowing."
    
    return None





def get_current_weather(location : str) -> WeatherResponse:
    
    if not settings.WEATHER_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="weather API key not configured. Add WEATHER_API_KEY to your .env file.")
        
        
    # url = f"{settings.WEATHER_API_KEY}/forecast.json"
    url = "http://api.weatherapi.com/v1/forecast.json"
    
    
    params = {
        "key" : settings.WEATHER_API_KEY,
        "q" : location,
        "days" : 3,
        "api" : "no",
        "alerts" : "no",
    }
    
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Weather API request timed out. Please try again."
        )
        
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Location '{location}' not found. Try a city name or pincode.")
            
            
            
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Weather API error. please try again later."
        )
        
        
        
    loc = data["location"]
    current = data["current"]
    forecast_days = data["forecast"]["forecastday"]
    
    
    current_weather = WeatherCondition(
        temp_c = current["temp_c"],
        humidity = current["humidity"],
        rainfall_mm = current.get("precip_mm", 0.0),
        wind_kph = current["wind_kph"],
        condition = current["condition"]["text"],
        icon = "https:" + current["condition"]["icon"],
        uv_index = current.get("uv", 0.0),
        is_day = bool(current.get("is_day", 1)),
    )
    
    
    forecast = []
    
    for day in forecast_days:
        d = day["day"]
        tip = generate_farming_tip(
            condition = d["condition"]["text"],
            rain_mm= d.get("totalprecip_mm", 0.0),
            temp_c=d["avgtemp_c"],
            humidity=d["avghumidity"],
        )
        
        
        forecast.append(WeatherForecastDay(
            date = day["date"],
            max_temp_c = d["maxtemp_c"],
            min_temp_c = d["mintemp_c"],
            avg_humidity = d["avghumidity"],
            total_rain_mm = d.get("toatalprecip_mm", 0.0),
            condition = d["condition"]["text"],
            farming_tip = tip,
        ))
        
        
    month = datetime.now().month
    season = detect_season(month)
    alert = check_showing_alert(
        temp_c=current["temp_c"],
        rain_mm=current.get("precip_mm",0.0),
        humidity = current["humidity"],
    )
    
    
    return WeatherResponse(
        location = f"{loc['name']}, {loc['region']}",
        country = loc["country"],
        current = current_weather,
        forecast = forecast,
        season = season,
        sowing_alert = alert,
    )
    
    
    


def get_weather_for_crop_recommendation(location : str) -> dict:
    
    try:
        
        w = get_current_weather(location)
        return {
            "temperature" : w.current.temp_c,
            "humidity" : w.current.humidity,
            "rainfall" : w.current.rainfall_mm,
            "season" : w.season,
        }
        
    except HTTPException:
        
        return {
            "temperature" : 25.0,
            "humidity" : 65.0,
            "rainfall" : 100.0,
            "season" : detect_season(datetime.now().month),
        }