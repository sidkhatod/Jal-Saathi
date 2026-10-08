import duckdb

csv_path = 'raw/soil-nutrient-analysis.csv'
parquet_path = 'processed/soil_haryana.parquet'

print("--- 3. Value Column ---")
query_val = f"""
SELECT nutrient_name, 
       MIN(value) as min_val, 
       MAX(value) as max_val, 
       AVG(value) as mean_val, 
       COUNT(DISTINCT value) as dist_cnt,
       SUM(CASE WHEN CAST(value AS DOUBLE) != CAST(CAST(value AS DOUBLE) AS INTEGER) THEN 1 ELSE 0 END) == 0 as is_int_only
FROM '{parquet_path}'
GROUP BY nutrient_name
ORDER BY nutrient_name
"""
print(duckdb.query(query_val).to_df().to_string())

print("\n--- 3b. 5 Random Villages ---")
query_vil = f"""
SELECT village_name, nutrient_name, nutrient_level, value
FROM '{parquet_path}'
WHERE village_name IN (
    SELECT village_name FROM (
        SELECT DISTINCT village_name FROM '{parquet_path}' WHERE village_name IS NOT NULL LIMIT 5
    )
)
AND nutrient_name = 'Nitrogen'
ORDER BY village_name
"""
print(duckdb.query(query_vil).to_df().to_string())

print("\n--- 4. Delhi spelling ---")
query_states = f"""
SELECT DISTINCT state_name FROM read_csv('{csv_path}', quote='"', ignore_errors=true, header=true)
WHERE LOWER(state_name) LIKE '%delhi%' OR LOWER(state_name) LIKE '%nct%' OR LOWER(state_name) LIKE '%capital%'
"""
print(duckdb.query(query_states).fetchall())

print("\n--- 5. Years completeness ---")
query_years = f"""
SELECT year, count(*) as rows, count(DISTINCT village_name) as villages, count(DISTINCT district_name) as districts
FROM read_csv('{csv_path}', quote='"', ignore_errors=true, header=true)
GROUP BY year
ORDER BY year
"""
print(duckdb.query(query_years).to_df().to_string())

print("\n--- 6. Coverage Median rows ---")
query_cov = f"""
WITH vil_counts AS (
    SELECT district_name, village_name, count(*) as row_cnt
    FROM '{parquet_path}'
    WHERE district_name IN ('Karnal', 'Kurukshetra')
    GROUP BY district_name, village_name
)
SELECT district_name, count(DISTINCT village_name) as records_villages, median(row_cnt) as median_rows_per_village
FROM vil_counts
GROUP BY district_name
"""
print(duckdb.query(query_cov).to_df().to_string())
