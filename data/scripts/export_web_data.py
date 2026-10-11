import os
import sys
import json
import yaml
import duckdb
import pandas as pd

# Paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
WEB_PUBLIC_DATA = os.path.join(REPO_ROOT, "web", "public", "data")
os.makedirs(WEB_PUBLIC_DATA, exist_ok=True)

# Add data/ to path for soil_api
sys.path.insert(0, DATA_DIR)
try:
    from soil_api import get_soil_rating
except ImportError:
    get_soil_rating = None

def export_districts():
    districts = {
        "Karnal": {
            "name": "Karnal",
            "state": "Haryana",
            "latitude": 29.68,
            "longitude": 76.99,
            "is_pilot": True,
            "soil_file": "soil_Karnal.json"
        },
        "Kurukshetra": {
            "name": "Kurukshetra",
            "state": "Haryana",
            "latitude": 29.96,
            "longitude": 76.82,
            "is_pilot": True,
            "soil_file": "soil_Kurukshetra.json"
        }
    }
    
    out_path = os.path.join(WEB_PUBLIC_DATA, "districts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(districts, f, indent=2)
    print(f"[OK] Exported {len(districts)} pilot districts to {out_path}")
    return districts

def export_crops():
    wheat_file = os.path.join(DATA_DIR, "crops", "wheat.yaml")
    paddy_file = os.path.join(DATA_DIR, "crops", "paddy.yaml")

    with open(wheat_file, "r", encoding="utf-8") as f:
        wheat_data = yaml.safe_load(f)

    with open(paddy_file, "r", encoding="utf-8") as f:
        paddy_data = yaml.safe_load(f)

    crops = {
        "wheat": {
            "name": "wheat",
            "display_name_en": "Wheat",
            "display_name_hi": "गेहूं",
            "season": "Rabi",
            "kc_ini": wheat_data.get("kc_ini"),
            "kc_mid": wheat_data.get("kc_mid"),
            "kc_end": wheat_data.get("kc_end"),
            "max_root_depth_m": wheat_data.get("max_root_depth_m"),
            "depletion_fraction": wheat_data.get("depletion_fraction"),
            "stages": [
                {
                    "stage_id": "ini",
                    "name_en": "Crown Root Initiation",
                    "name_hi": "शीर्ष जड़ विकास (CRI)",
                    "days": wheat_data.get("stage_ini_days", 20),
                    "description_en": "First critical irrigation window for vigorous root crown establishment.",
                    "description_hi": "मजबूत जड़ों के विकास के लिए पहली महत्वपूर्ण सिंचाई।"
                },
                {
                    "stage_id": "dev",
                    "name_en": "Tillering & Stem Elongation",
                    "name_hi": "कल्ले निकलना व तने का विकास",
                    "days": wheat_data.get("stage_dev_days", 30),
                    "description_en": "Vegetative canopy expansion; maintain adequate root-zone moisture.",
                    "description_hi": "वानस्पतिक वृद्धि; जड़ क्षेत्र में पर्याप्त नमी बनाए रखें।"
                },
                {
                    "stage_id": "mid",
                    "name_en": "Flowering & Grain Filling",
                    "name_hi": "फूल आना व दाना भरना",
                    "days": wheat_data.get("stage_mid_days", 60),
                    "description_en": "Highest water consumption phase; avoid stress days during grain milky stage.",
                    "description_hi": "सर्वाधिक जल खपत का समय; दाने के दूधिया चरण में नमी की कमी न होने दें।"
                },
                {
                    "stage_id": "late",
                    "name_en": "Ripening & Maturity",
                    "name_hi": "पकना व कटाई",
                    "days": wheat_data.get("stage_late_days", 30),
                    "description_en": "Gradual drying off; withhold late irrigations before harvesting.",
                    "description_hi": "फसल का पकना; कटाई से पूर्व सिंचाई रोक दें।"
                }
            ],
            "total_days": (
                wheat_data.get("stage_ini_days", 20) +
                wheat_data.get("stage_dev_days", 30) +
                wheat_data.get("stage_mid_days", 60) +
                wheat_data.get("stage_late_days", 30)
            )
        },
        "paddy": {
            "name": "paddy",
            "display_name_en": "Paddy (Rice)",
            "display_name_hi": "धान",
            "season": "Kharif",
            "kc_ini": paddy_data.get("kc_ini"),
            "kc_mid": paddy_data.get("kc_mid"),
            "kc_end": paddy_data.get("kc_end"),
            "max_root_depth_m": paddy_data.get("max_root_depth_m"),
            "depletion_fraction": paddy_data.get("depletion_fraction"),
            "percolation_rate_mm_day": paddy_data.get("percolation_rate"),
            "bund_height_m": paddy_data.get("bund_height"),
            "stages": [
                {
                    "stage_id": "ini",
                    "name_en": "Transplanting & Establishment",
                    "name_hi": "रोपाई व स्थापना",
                    "days": paddy_data.get("stage_ini_days", 20),
                    "description_en": "Shallow water ponding after seedling transplanting.",
                    "description_hi": "पौध रोपाई के बाद खेत में हल्का पानी बनाए रखें।"
                },
                {
                    "stage_id": "dev",
                    "name_en": "Active Tillering",
                    "name_hi": "कल्ले निकलना (टिलरिंग)",
                    "days": paddy_data.get("stage_dev_days", 20),
                    "description_en": "Canopy growth; intermittent drying can be practiced to promote deep roots.",
                    "description_hi": "कल्लों का विकास; गहरी जड़ों के लिए आंतरायिक सिंचाई।"
                },
                {
                    "stage_id": "mid",
                    "name_en": "Panicle & Flowering",
                    "name_hi": "बालियां निकलना व फूल आना",
                    "days": paddy_data.get("stage_mid_days", 30),
                    "description_en": "Critical reproductive phase; maintain standing water layer.",
                    "description_hi": "अत्यंत संवेदनशील चरण; खेत में पानी की परत बनाए रखें।"
                },
                {
                    "stage_id": "late",
                    "name_en": "Grain Ripening",
                    "name_hi": "दाना पकना",
                    "days": paddy_data.get("stage_late_days", 20),
                    "description_en": "Drain field 10-14 days before harvest.",
                    "description_hi": "कटाई से 10-14 दिन पूर्व खेत से पानी निकाल दें।"
                }
            ],
            "total_days": (
                paddy_data.get("stage_ini_days", 20) +
                paddy_data.get("stage_dev_days", 20) +
                paddy_data.get("stage_mid_days", 30) +
                paddy_data.get("stage_late_days", 20)
            )
        }
    }

    out_path = os.path.join(WEB_PUBLIC_DATA, "crops.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(crops, f, indent=2)
    print(f"[OK] Exported crops calendar (wheat: {crops['wheat']['total_days']}d, paddy: {crops['paddy']['total_days']}d) to {out_path}")
    return crops

def export_soil_for_districts():
    # Identify district codes from parquet
    soil_parquet = os.path.join(DATA_DIR, "processed", "soil_haryana_district.parquet")
    if not os.path.exists(soil_parquet):
        # Fallback to main soil parquet
        soil_parquet = os.path.join(DATA_DIR, "soil", "Soil_Health_Haryana.parquet")

    district_code_df = duckdb.query(f"""
        SELECT DISTINCT district_name, district_code 
        FROM '{soil_parquet}'
        WHERE LOWER(district_name) IN ('karnal', 'kurukshetra')
    """).df()

    print("[DEBUG] District codes found:")
    print(district_code_df)

    dist_map = {}
    for _, row in district_code_df.iterrows():
        d_name = row['district_name']
        d_code = str(row['district_code'])
        # Normalize name
        norm_name = "Karnal" if "karnal" in d_name.lower() else "Kurukshetra"
        dist_map[norm_name] = d_code

    for dist_name, code in dist_map.items():
        ratings = {}
        if get_soil_rating:
            ratings = get_soil_rating(district_code=code)
        
        # If ratings empty, query direct from parquet
        if not ratings:
            q = f"""
                SELECT nutrient_name, nutrient_level, year, n_samples
                FROM '{soil_parquet}'
                WHERE district_code = '{code}'
            """
            raw_df = duckdb.query(q).df()
            for nutrient in raw_df['nutrient_name'].unique():
                n_df = raw_df[raw_df['nutrient_name'] == nutrient].sort_values('year', ascending=False)
                best_year = n_df.iloc[0]['year']
                year_df = n_df[n_df['year'] == best_year]
                dom_row = year_df.sort_values('n_samples', ascending=False).iloc[0]
                dist = {r['nutrient_level']: int(r['n_samples']) for _, r in year_df.iterrows()}
                ratings[nutrient] = {
                    "dominant_level": dom_row['nutrient_level'],
                    "distribution": dist,
                    "level_used": "district",
                    "year_used": best_year,
                    "n_samples": int(year_df['n_samples'].sum())
                }

        formatted = {
            "district": dist_name,
            "district_code": code,
            "nutrients": ratings
        }

        out_path = os.path.join(WEB_PUBLIC_DATA, f"soil_{dist_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, indent=2)
        print(f"[OK] Exported real soil ratings for {dist_name} to {out_path} ({len(ratings)} nutrients)")

if __name__ == "__main__":
    print("--- Exporting Web Data from Repo Real Datasets ---")
    export_districts()
    export_crops()
    export_soil_for_districts()
    print("--- Done ---")
