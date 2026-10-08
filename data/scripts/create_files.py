import os

files = {
    "weather.py": """import os
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
""",
    "soil_hydraulics.py": """import os
import json
from pydantic import BaseModel

class SoilHydraulics(BaseModel):
    texture_class: str
    field_capacity_mm_per_m: float
    wilting_point_mm_per_m: float
    available_water_capacity_mm_per_m: float
    citation: str

# FAO-56 Table 19: Soil water characteristics for different soil types
TEXTURE_LOOKUP = {
    "clay": SoilHydraulics(
        texture_class="clay",
        field_capacity_mm_per_m=340.0,
        wilting_point_mm_per_m=210.0,
        available_water_capacity_mm_per_m=130.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm"
    ),
    "loam": SoilHydraulics(
        texture_class="loam",
        field_capacity_mm_per_m=270.0,
        wilting_point_mm_per_m=130.0,
        available_water_capacity_mm_per_m=140.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm"
    ),
    "sand": SoilHydraulics(
        texture_class="sand",
        field_capacity_mm_per_m=100.0,
        wilting_point_mm_per_m=40.0,
        available_water_capacity_mm_per_m=60.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm"
    )
}

def get_soil_hydraulics(lat: float, lon: float) -> SoilHydraulics:
    '''
    Given a lat/lon, return the soil hydraulics. 
    Currently falls back to a generalized 'loam' class as a robust default 
    until ISRIC SoilGrids API geometry parsing is safely integrated.
    '''
    return TEXTURE_LOOKUP["loam"]
""",
    "crops/__init__.py": "",
    "crops/schema.py": """from pydantic import BaseModel, HttpUrl

class CropParameters(BaseModel):
    name: str
    kc_ini: float
    kc_mid: float
    kc_end: float
    stage_ini_days: int
    stage_dev_days: int
    stage_mid_days: int
    stage_late_days: int
    max_root_depth_m: float
    depletion_fraction: float
    citation_url: HttpUrl
""",
    "crops/paddy.yaml": """name: "paddy"
kc_ini: 1.05
kc_mid: 1.20
kc_end: 0.90
stage_ini_days: 30
stage_dev_days: 30
stage_mid_days: 40
stage_late_days: 20
max_root_depth_m: 0.6
depletion_fraction: 0.2
citation_url: "https://www.fao.org/3/X0490E/x0490e0b.htm"
""",
    "crops/wheat.yaml": """name: "wheat"
kc_ini: 0.30
kc_mid: 1.15
kc_end: 0.25
stage_ini_days: 30
stage_dev_days: 30
stage_mid_days: 40
stage_late_days: 30
max_root_depth_m: 1.2
depletion_fraction: 0.55
citation_url: "https://www.fao.org/3/X0490E/x0490e0b.htm"
""",
    "advisories/__init__.py": "",
    "advisories/schema.py": """from pydantic import BaseModel, HttpUrl
from typing import Optional

class Advisory(BaseModel):
    crop: str
    growth_stage: str
    problem_name: str
    type: str
    symptoms: str
    organic_option: Optional[str] = None
    chemical_option: Optional[str] = None
    weather_constraints: Optional[str] = None
    source_url: HttpUrl
    reviewed: bool = False
""",
    "advisories/loader.py": """import os
import yaml
from .schema import Advisory

def load_reviewed_advisories(advisories_dir='advisories'):
    reviewed = []
    for f in os.listdir(advisories_dir):
        if f.endswith('.yaml'):
            with open(os.path.join(advisories_dir, f), 'r') as file:
                data = yaml.safe_load(file)
                adv = Advisory(**data)
                if adv.reviewed:
                    reviewed.append(adv)
    return reviewed
""",
    "advisories/paddy_blast.yaml": """crop: "paddy"
growth_stage: "tillering"
problem_name: "Rice Blast"
type: "disease"
symptoms: "Spindle shaped spots with grey centre and brown margin on leaves"
chemical_option: "Tricyclazole 75 WP @ 0.6 g/lit water"
organic_option: "Pseudomonas fluorescens @ 10g/lit water"
source_url: "https://iari.res.in/en/rice-blast-management"
reviewed: false
""",
    "advisories/wheat_rust.yaml": """crop: "wheat"
growth_stage: "heading"
problem_name: "Yellow Rust"
type: "disease"
symptoms: "Yellow pustules arranged in parallel lines on leaves"
chemical_option: "Propiconazole 25 EC @ 1 ml/lit water"
source_url: "http://www.hau.ac.in/yellow-rust"
reviewed: false
""",
    "fertiliser/__init__.py": "",
    "fertiliser/schema.py": """from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

class FertiliserRule(BaseModel):
    crop: str
    rating_n: Optional[str] = None
    rating_p: Optional[str] = None
    rating_k: Optional[str] = None
    recommended_n_kg_ha: Optional[float] = None
    recommended_p_kg_ha: Optional[float] = None
    recommended_k_kg_ha: Optional[float] = None
    timing_notes: Optional[str] = None
    citation_url: HttpUrl
    reviewed: bool = False
""",
    "fertiliser/fertiliser_rules.yaml": """- crop: "wheat"
  rating_n: "Medium"
  rating_p: "Medium"
  rating_k: "Medium"
  recommended_n_kg_ha: 150.0
  recommended_p_kg_ha: 60.0
  recommended_k_kg_ha: 40.0
  timing_notes: "Half N, full P & K at sowing. Remaining N at first irrigation."
  citation_url: "http://www.hau.ac.in/wheat-fertiliser"
  reviewed: false
- crop: "paddy"
  rating_n: "Low"
  rating_p: "Medium"
  rating_k: "Medium"
  recommended_n_kg_ha: 150.0
  timing_notes: "Increase N by 25% for low rating. Split N into 3 doses."
  citation_url: "http://www.hau.ac.in/paddy-fertiliser"
  reviewed: false
""",
    "upload.py": """import argparse
import os
import boto3

def upload_processed(bucket_name, env, dry_run=True):
    s3 = boto3.client('s3')
    base_dir = 'processed'
    full_bucket = f"{bucket_name}-{env}"
    
    print(f"Uploading {base_dir} to s3://{full_bucket} (Dry Run: {dry_run})")
    
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist.")
        return
        
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # Remove 'processed/' from the key
            s3_key = os.path.relpath(local_path, base_dir).replace(os.sep, '/')
            
            if s3_key.startswith("soil_"):
                s3_key = f"soil/{s3_key}"
            
            if dry_run:
                print(f"[DRY-RUN] Would upload {local_path} to s3://{full_bucket}/{s3_key}")
            else:
                print(f"Uploading {local_path} to s3://{full_bucket}/{s3_key}")
                s3.upload_file(local_path, full_bucket, s3_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default="jal-saathi-datasets")
    parser.add_argument("--env", default="dev")
    parser.add_argument("--execute", action="store_true", help="Actually perform the upload")
    args = parser.parse_args()
    
    upload_processed(args.bucket, args.env, dry_run=not args.execute)
""",
    "tests/test_crops.py": """import os
import yaml
from crops.schema import CropParameters

def test_crop_parameters_validity():
    crops_dir = os.path.join(os.path.dirname(__file__), '../crops')
    for f in os.listdir(crops_dir):
        if f.endswith('.yaml'):
            with open(os.path.join(crops_dir, f), 'r') as file:
                data = yaml.safe_load(file)
                parsed = CropParameters(**data)
                assert parsed.citation_url is not None
""",
    "tests/test_advisories.py": """import os
import pytest
from advisories.loader import load_reviewed_advisories

def test_loader_filters_unreviewed():
    advisories_dir = os.path.join(os.path.dirname(__file__), '../advisories')
    reviewed = load_reviewed_advisories(advisories_dir)
    assert len(reviewed) == 0
""",
    "tests/test_weather.py": """import pytest
from weather import WeatherClient

@pytest.mark.slow
@pytest.mark.network
def test_open_meteo_live():
    client = WeatherClient(cache_dir='processed/test-weather-cache')
    forecast = client.get_7_day_forecast(lat=29.68, lon=76.99)
    assert len(forecast) > 0
    assert forecast[0].precipitation_sum >= 0
"""
}

for path, content in files.items():
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
print("Files generated.")
