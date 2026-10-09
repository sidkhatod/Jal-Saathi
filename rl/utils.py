import os
import sys
import yaml
import numpy as np

# Adjust path to import from the data module which is at project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.soil_hydraulics import get_soil_hydraulics, SoilHydraulics, TEXTURE_LOOKUP
from data.weather import WeatherClient, DailyForecast

def load_crop_config(crop_name: str, required_keys: list) -> dict:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'crops', f'{crop_name}.yaml')
    # Allow testing override
    if os.environ.get("USE_FAKE_CONFIG"):
        config_path = os.path.join(os.path.dirname(__file__), 'tests', 'fixtures', f'{crop_name}_fake.yaml')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Crop configuration not found at {config_path}")
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    missing_keys = []
    for key in required_keys:
        if key not in config or config[key] is None:
            missing_keys.append(key)
            
    if missing_keys:
        raise ValueError(f"Crop config {crop_name}.yaml is missing or has null values for required keys: {missing_keys}")
        
    return config

def get_forecast(daily_weather: list, current_day: int, noise_std_rain: float = 0.0, noise_std_et0: float = 0.0) -> np.ndarray:
    """
    Returns a 3-day forecast of [Rain, ET0] starting from current_day.
    Forecast = actual + noise.
    """
    forecast = []
    for offset in range(3):
        day_idx = current_day + offset
        if day_idx < len(daily_weather):
            w = daily_weather[day_idx]
            rain = max(0.0, w.precipitation_sum + np.random.normal(0, noise_std_rain))
            et0 = max(0.0, w.et0_fao_evapotranspiration + np.random.normal(0, noise_std_et0))
            forecast.extend([rain, et0])
        else:
            # Pad with zeros if end of season
            forecast.extend([0.0, 0.0])
    return np.array(forecast, dtype=np.float32)

def generate_noise_model(forecast_accuracy: str = "high"):
    if forecast_accuracy == "high":
        return {"rain_std": 1.0, "et0_std": 0.2}
    elif forecast_accuracy == "medium":
        return {"rain_std": 3.0, "et0_std": 0.5}
    else:
        return {"rain_std": 0.0, "et0_std": 0.0}
