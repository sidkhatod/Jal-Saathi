import pandas as pd
import duckdb

codebook_path = 'raw/Soil_Nutrient_Analysis_codebook.xlsx'
csv_path = 'raw/soil-nutrient-analysis.csv'

# Let's inspect all sheets in the codebook
excel_file = pd.ExcelFile(codebook_path)
print(f"Sheets: {excel_file.sheet_names}")
for sheet in excel_file.sheet_names:
    print(f"\n--- Sheet: {sheet} ---")
    df = pd.read_excel(codebook_path, sheet_name=sheet)
    print(df.to_string())

# Find out what years exist in the CSV using DuckDB
print("\n--- Years in CSV ---")
query = f"SELECT DISTINCT year FROM read_csv_auto('{csv_path}') ORDER BY year"
years = duckdb.query(query).fetchall()
print([y[0] for y in years])
