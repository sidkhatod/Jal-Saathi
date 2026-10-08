import pandas as pd
import duckdb
import os

os.makedirs('processed', exist_ok=True)
codebook_path = 'raw/Soil_Nutrient_Analysis_codebook.xlsx'
csv_path = 'raw/soil-nutrient-analysis.csv'

# Step 1: Read Codebook
print("--- Codebook Definitions ---")
df = pd.read_excel(codebook_path, sheet_name=0, header=1)
for col in ['value', 'nutrient_type', 'nutrient_level', 'year']:
    row = df[df['Variable Name'] == col]
    if not row.empty:
        print(f"{col}: {row.iloc[0]['Variable Description']}")
    else:
        print(f"{col}: Not found")

# Step 1b: Extract years
print("\n--- Processing Years ---")
query = f"SELECT DISTINCT year FROM read_csv('{csv_path}', quote='\"', ignore_errors=true, header=true) ORDER BY year"
years = duckdb.query(query).fetchall()
print("Years in CSV:", [y[0] for y in years])

# Step 2: Create Parquet files
print("\n--- Writing Parquet Files ---")
# Haryana
duckdb.query(f"""
COPY (
    SELECT * FROM read_csv('{csv_path}', quote='\"', ignore_errors=true, header=true)
    WHERE LOWER(state_name) LIKE '%haryana%'
) TO 'processed/soil_haryana.parquet' (FORMAT PARQUET);
""")
duckdb.query("""
COPY (
    SELECT district_name, nutrient_name, nutrient_level, count(*) as cnt 
    FROM 'processed/soil_haryana.parquet'
    WHERE year = (SELECT max(year) FROM 'processed/soil_haryana.parquet')
    GROUP BY district_name, nutrient_name, nutrient_level
) TO 'processed/soil_haryana_district.parquet' (FORMAT PARQUET);
""")
duckdb.query("""
COPY (
    SELECT district_name, block_name, nutrient_name, nutrient_level, count(*) as cnt 
    FROM 'processed/soil_haryana.parquet'
    WHERE year = (SELECT max(year) FROM 'processed/soil_haryana.parquet')
    GROUP BY district_name, block_name, nutrient_name, nutrient_level
) TO 'processed/soil_haryana_block.parquet' (FORMAT PARQUET);
""")

# Delhi
duckdb.query(f"""
COPY (
    SELECT * FROM read_csv('{csv_path}', quote='\"', ignore_errors=true, header=true)
    WHERE LOWER(state_name) LIKE '%delhi%'
) TO 'processed/soil_delhi.parquet' (FORMAT PARQUET);
""")
duckdb.query("""
COPY (
    SELECT district_name, nutrient_name, nutrient_level, count(*) as cnt 
    FROM 'processed/soil_delhi.parquet'
    WHERE year = (SELECT max(year) FROM 'processed/soil_delhi.parquet')
    GROUP BY district_name, nutrient_name, nutrient_level
) TO 'processed/soil_delhi_district.parquet' (FORMAT PARQUET);
""")
duckdb.query("""
COPY (
    SELECT district_name, block_name, nutrient_name, nutrient_level, count(*) as cnt 
    FROM 'processed/soil_delhi.parquet'
    WHERE year = (SELECT max(year) FROM 'processed/soil_delhi.parquet')
    GROUP BY district_name, block_name, nutrient_name, nutrient_level
) TO 'processed/soil_delhi_block.parquet' (FORMAT PARQUET);
""")

# Step 3: Coverage Reports
print("\n--- Haryana Coverage ---")
haryana_cov = duckdb.query("""
SELECT district_name,
       COUNT(DISTINCT village_name) as villages,
       COUNT(DISTINCT block_name) as blocks,
       COUNT(DISTINCT year) as years,
       SUM(CASE WHEN nutrient_name = 'Soil Ph' THEN 1 ELSE 0 END) > 0 as has_ph,
       SUM(CASE WHEN nutrient_name = 'Electrical Conductivity' THEN 1 ELSE 0 END) > 0 as has_ec,
       SUM(CASE WHEN nutrient_name = 'Organic Carbon' THEN 1 ELSE 0 END) > 0 as has_oc,
       SUM(CASE WHEN nutrient_name = 'Nitrogen' THEN 1 ELSE 0 END) > 0 as has_n,
       SUM(CASE WHEN nutrient_name = 'Phosphorus' THEN 1 ELSE 0 END) > 0 as has_p,
       SUM(CASE WHEN nutrient_name = 'Potassium' THEN 1 ELSE 0 END) > 0 as has_k
FROM 'processed/soil_haryana.parquet'
GROUP BY district_name
ORDER BY villages DESC
""").df()
print(haryana_cov.to_string())

print("\n--- Delhi Coverage ---")
delhi_cov = duckdb.query("""
SELECT district_name,
       COUNT(DISTINCT village_name) as villages,
       COUNT(DISTINCT block_name) as blocks,
       COUNT(DISTINCT year) as years,
       SUM(CASE WHEN nutrient_name = 'Soil Ph' THEN 1 ELSE 0 END) > 0 as has_ph,
       SUM(CASE WHEN nutrient_name = 'Electrical Conductivity' THEN 1 ELSE 0 END) > 0 as has_ec,
       SUM(CASE WHEN nutrient_name = 'Organic Carbon' THEN 1 ELSE 0 END) > 0 as has_oc,
       SUM(CASE WHEN nutrient_name = 'Nitrogen' THEN 1 ELSE 0 END) > 0 as has_n,
       SUM(CASE WHEN nutrient_name = 'Phosphorus' THEN 1 ELSE 0 END) > 0 as has_p,
       SUM(CASE WHEN nutrient_name = 'Potassium' THEN 1 ELSE 0 END) > 0 as has_k
FROM 'processed/soil_delhi.parquet'
GROUP BY district_name
ORDER BY villages DESC
""").df()
print(delhi_cov.to_string())
