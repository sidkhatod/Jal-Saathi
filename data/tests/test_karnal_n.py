import duckdb
from soil_api import get_soil_rating
import os

def test_karnal_nitrogen_fallback():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, '..', 'processed', 'soil_haryana_district.parquet')
    
    karnal_code_df = duckdb.query(f"SELECT DISTINCT district_code FROM '{path}' WHERE LOWER(district_name) = 'karnal'").df()
    assert not karnal_code_df.empty, "Karnal not found"
    karnal_code = str(karnal_code_df.iloc[0]['district_code'])
    
    rating = get_soil_rating(district_code=karnal_code)
    
    assert 'Nitrogen' in rating, "Nitrogen not resolved"
    assert rating['Nitrogen']['year_used'] == '2023-24', f"Expected 2023-24, got {rating['Nitrogen']['year_used']}"
    assert rating['Nitrogen']['level_used'] == 'district', "Should fallback to district level"
