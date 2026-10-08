import os
import json
import requests
from pydantic import BaseModel
from typing import List, Optional

class DailyForecast(BaseModel):
    date: str
    precipitation_sum: float
    precipitation_probability_max: int
    wind_speed_10m_max: float
    temperature_2m_max: float
    temperature_2m_min: float
    et0_fao_evapotranspiration: float

class WeatherClient:
    def __init__(self, cache_dir='processed/weather-cache'):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        
    def get_7_day_forecast(self, lat: float, lon: float) -> List[DailyForecast]:
        cache_file = os.path.join(self.cache_dir, f"{lat}_{lon}_forecast.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return [DailyForecast(**d) for d in json.load(f)]
                
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", 
                     "precipitation_probability_max", "wind_speed_10m_max", "et0_fao_evapotranspiration"],
            "timezone": "auto"
        }
        resp = requests.get(self.base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        daily = data.get('daily', {})
        results = []
        for i in range(len(daily.get('time', []))):
            results.append(DailyForecast(
                date=daily['time'][i],
                precipitation_sum=daily['precipitation_sum'][i],
                precipitation_probability_max=daily['precipitation_probability_max'][i] if daily.get('precipitation_probability_max') else 0,
                wind_speed_10m_max=daily['wind_speed_10m_max'][i],
                temperature_2m_max=daily['temperature_2m_max'][i],
                temperature_2m_min=daily['temperature_2m_min'][i],
                et0_fao_evapotranspiration=daily['et0_fao_evapotranspiration'][i]
            ))
            
        with open(cache_file, 'w') as f:
            json.dump([r.model_dump() for r in results], f)
            
        return results
