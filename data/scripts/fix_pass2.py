import duckdb
import os

parquet_path = 'processed/soil_haryana.parquet'
csv_path = 'raw/soil-nutrient-analysis.csv'
meas_parquet = 'processed/soil_haryana_measured.parquet'

print("--- A.5 & A.4 Rebuild Parquets with measured values ---")
query_rebuild = f"""
COPY (
    SELECT 
        id, year, state_name, state_code, district_name, district_code, block_name, block_code,
        trim(regexp_replace(village_name, '\\([0-9]+\\)', '')) as village_name,
        regexp_extract(village_name, '\\(([0-9]+)\\)', 1) as village_code_suffix,
        village_code, nutrient_type, nutrient_name, nutrient_level, value
    FROM read_csv('{csv_path}', quote='"', ignore_errors=true, header=true)
    WHERE LOWER(state_name) LIKE '%haryana%' AND value > 0
) TO '{meas_parquet}' (FORMAT PARQUET);
"""
duckdb.query(query_rebuild)

print("--- A.1 Measured Coverage ---")
query_a1 = f"""
SELECT year, district_name,
       COUNT(DISTINCT village_name) as measured_villages,
       COUNT(DISTINCT block_name) as measured_blocks,
       SUM(CASE WHEN nutrient_name = 'Soil Ph' THEN 1 ELSE 0 END) > 0 as has_ph,
       SUM(CASE WHEN nutrient_name = 'Electrical Conductivity' THEN 1 ELSE 0 END) > 0 as has_ec,
       SUM(CASE WHEN nutrient_name = 'Organic Carbon' THEN 1 ELSE 0 END) > 0 as has_oc,
       SUM(CASE WHEN nutrient_name = 'Nitrogen' THEN 1 ELSE 0 END) > 0 as has_n,
       SUM(CASE WHEN nutrient_name = 'Phosphorus' THEN 1 ELSE 0 END) > 0 as has_p,
       SUM(CASE WHEN nutrient_name = 'Potassium' THEN 1 ELSE 0 END) > 0 as has_k
FROM '{meas_parquet}'
GROUP BY year, district_name
ORDER BY year, district_name
"""
print(duckdb.query(query_a1).to_df().to_string())

print("\n--- A.2 Mismatches in Village Totals ---")
query_a2 = f"""
WITH vil_nut_totals AS (
    SELECT village_name, nutrient_name, SUM(value) as total_samples
    FROM '{meas_parquet}'
    GROUP BY village_name, nutrient_name
),
vil_matches AS (
    SELECT village_name, 
           COUNT(DISTINCT total_samples) as distinct_totals,
           MIN(total_samples) as min_total,
           MAX(total_samples) as max_total
    FROM vil_nut_totals
    GROUP BY village_name
)
SELECT 
    COUNT(*) as total_villages,
    SUM(CASE WHEN distinct_totals = 1 THEN 1 ELSE 0 END) as matching_villages,
    SUM(CASE WHEN distinct_totals > 1 THEN 1 ELSE 0 END) as mismatch_villages
FROM vil_matches
"""
print(duckdb.query(query_a2).to_df().to_string())

print("\n--- A.2 Describe Mismatches (Sample) ---")
print(duckdb.query(f"SELECT * FROM (WITH vil_nut_totals AS (SELECT village_name, nutrient_name, SUM(value) as total_samples FROM '{meas_parquet}' GROUP BY village_name, nutrient_name), vil_matches AS (SELECT village_name, COUNT(DISTINCT total_samples) as distinct_totals, MIN(total_samples) as min_total, MAX(total_samples) as max_total FROM vil_nut_totals GROUP BY village_name) SELECT * FROM vil_matches WHERE distinct_totals > 1 LIMIT 5)").to_df().to_string())

print("\n--- A.2 10 Largest Single-Row Values ---")
query_largest = f"""
SELECT village_name, nutrient_name, nutrient_level, value
FROM '{meas_parquet}'
ORDER BY value DESC
LIMIT 10
"""
print(duckdb.query(query_largest).to_df().to_string())

print("\n--- A.3 Karnal and Kurukshetra Measured vs Total ---")
query_a3 = f"""
SELECT district_name, year, COUNT(DISTINCT village_name) as measured_villages, COUNT(DISTINCT block_name) as measured_blocks
FROM '{meas_parquet}'
WHERE district_name IN ('Karnal', 'Kurukshetra')
GROUP BY district_name, year
ORDER BY district_name, year
"""
print(duckdb.query(query_a3).to_df().to_string())

print("\n--- A.4 Rebuilding Aggregated Parquets ---")
duckdb.query(f"""
COPY (
    SELECT district_name, block_name, nutrient_name, nutrient_level, SUM(value) as n_samples
    FROM '{meas_parquet}'
    WHERE year = '2024-25'
    GROUP BY district_name, block_name, nutrient_name, nutrient_level
) TO 'processed/soil_haryana_block.parquet' (FORMAT PARQUET);

COPY (
    SELECT district_name, nutrient_name, nutrient_level, SUM(value) as n_samples
    FROM '{meas_parquet}'
    WHERE year = '2024-25'
    GROUP BY district_name, nutrient_name, nutrient_level
) TO 'processed/soil_haryana_district.parquet' (FORMAT PARQUET);

COPY (
    SELECT district_name, block_name, village_name, nutrient_name, nutrient_level, SUM(value) as n_samples
    FROM '{meas_parquet}'
    WHERE year = '2024-25'
    GROUP BY district_name, block_name, village_name, nutrient_name, nutrient_level
) TO 'processed/soil_haryana_village.parquet' (FORMAT PARQUET);
""")
print("Done reconstructing parquets.")
