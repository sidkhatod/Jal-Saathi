import os
import pandas as pd
import requests

def fetch_and_save_weather(district_name, lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "et0_fao_evapotranspiration"],
        "timezone": "auto"
    }
    print(f"Fetching {district_name} ({start_date} to {end_date})...")
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    
    daily = data.get('daily', {})
    
    df = pd.DataFrame({
        'date': daily.get('time', []),
        'temperature_2m_max': daily.get('temperature_2m_max', []),
        'temperature_2m_min': daily.get('temperature_2m_min', []),
        'precipitation_sum': daily.get('precipitation_sum', []),
        'et0_fao_evapotranspiration': daily.get('et0_fao_evapotranspiration', [])
    })
    
    # Fill NAs if any (e.g. at the very end of the archive)
    df['precipitation_sum'] = df['precipitation_sum'].fillna(0.0)
    df['et0_fao_evapotranspiration'] = df['et0_fao_evapotranspiration'].fillna(4.0)
    df['temperature_2m_max'] = df['temperature_2m_max'].fillna(25.0)
    df['temperature_2m_min'] = df['temperature_2m_min'].fillna(15.0)
    
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'processed'))
    os.makedirs(out_dir, exist_ok=True)
    
    start_year = start_date.split('-')[0]
    end_year = end_date.split('-')[0]
    out_file = os.path.join(out_dir, f"weather_{district_name.lower()}_{start_year}-{end_year}.parquet")
    
    df.to_parquet(out_file, index=False)
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    # Fetch ~14 years of data
    start_date = "2010-01-01"
    end_date = "2023-12-31"
    
    districts = {
        "Karnal": (29.68, 76.99),
        "Kurukshetra": (29.96, 76.82)
    }
    
    for name, (lat, lon) in districts.items():
        fetch_and_save_weather(name, lat, lon, start_date, end_date)
