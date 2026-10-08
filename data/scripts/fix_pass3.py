import duckdb

meas_parquet = 'processed/soil_haryana_measured.parquet'

print("--- 1. Village Match/Mismatch Analysis (by code) ---")
query_a2 = f"""
WITH vil_nut_totals AS (
    SELECT state_code, district_code, block_code, village_code, nutrient_name, SUM(value) as total_samples
    FROM '{meas_parquet}'
    GROUP BY state_code, district_code, block_code, village_code, nutrient_name
),
vil_matches AS (
    SELECT state_code, district_code, block_code, village_code,
           COUNT(DISTINCT total_samples) as distinct_totals,
           MIN(total_samples) as min_total,
           MAX(total_samples) as max_total
    FROM vil_nut_totals
    GROUP BY state_code, district_code, block_code, village_code
)
SELECT 
    COUNT(*) as total_villages,
    SUM(CASE WHEN distinct_totals = 1 THEN 1 ELSE 0 END) as matching_villages,
    SUM(CASE WHEN distinct_totals > 1 THEN 1 ELSE 0 END) as mismatch_villages
FROM vil_matches
"""
print(duckdb.query(query_a2).to_df().to_string())

print("\n--- 2. Per-district has_n table (both years) ---")
query_n = f"""
SELECT year, district_name,
       SUM(CASE WHEN nutrient_name = 'Nitrogen' THEN 1 ELSE 0 END) > 0 as has_n
FROM '{meas_parquet}'
GROUP BY year, district_name
ORDER BY year, district_name
"""
print(duckdb.query(query_n).to_df().to_string())

print("\n--- 2. Rebuilding Parquets with year, codes ---")
duckdb.query(f"""
COPY (
    SELECT district_name, district_code, block_name, block_code, nutrient_name, nutrient_level, year, SUM(value) as n_samples
    FROM '{meas_parquet}'
    GROUP BY district_name, district_code, block_name, block_code, nutrient_name, nutrient_level, year
) TO 'processed/soil_haryana_block.parquet' (FORMAT PARQUET);

COPY (
    SELECT district_name, district_code, nutrient_name, nutrient_level, year, SUM(value) as n_samples
    FROM '{meas_parquet}'
    GROUP BY district_name, district_code, nutrient_name, nutrient_level, year
) TO 'processed/soil_haryana_district.parquet' (FORMAT PARQUET);

COPY (
    SELECT district_name, district_code, block_name, block_code, village_name, village_code, nutrient_name, nutrient_level, year, SUM(value) as n_samples
    FROM '{meas_parquet}'
    GROUP BY district_name, district_code, block_name, block_code, village_name, village_code, nutrient_name, nutrient_level, year
) TO 'processed/soil_haryana_village.parquet' (FORMAT PARQUET);
""")
print("Done reconstructing parquets.")
