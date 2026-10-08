import pandas as pd
import sys
import numpy as np

csv_path = 'raw/soil-nutrient-analysis.csv'
codebook_path = 'raw/Soil_Nutrient_Analysis_codebook.xlsx'

print("--- Codebook ---")
try:
    codebook = pd.read_excel(codebook_path)
    print(codebook.head(10).to_string())
except Exception as e:
    print(f"Error reading codebook: {e}")

print("\n--- Reading CSV ---")
df = pd.read_csv(csv_path)

print(f"Row count: {len(df):,}")
print(f"Columns: {list(df.columns)}")

print("\n--- States/Districts ---")
state_cols = [c for c in df.columns if 'state' in c.lower()]
dist_cols = [c for c in df.columns if 'dist' in c.lower()]

if state_cols:
    sc = state_cols[0]
    states = df[sc].dropna().unique()
    print(f"States covered ({len(states)}):")
    print(states)
else:
    print("No state column found.")
    
if dist_cols:
    dc = dist_cols[0]
    dists = df[dc].dropna().unique()
    print(f"Districts covered ({len(dists)}):")
    # Only print first 20 districts to avoid massive output
    print(dists[:20], "... and more.")
else:
    print("No district column found.")

print("\n--- Null Rates ---")
null_rates = (df.isnull().sum() / len(df)) * 100
for col, rate in null_rates.items():
    print(f"{col}: {rate:.2f}% null")

print("\n--- Nutrient Checks ---")
def check_col(terms):
    # To avoid matching 'in', 'on', 'and' etc, we do specific checks for N, P, K
    matches = []
    for c in df.columns:
        cl = c.lower()
        for t in terms:
            if t == 'n' and (cl == 'n' or cl.startswith('n_') or cl.endswith('_n')): matches.append(c)
            elif t == 'p' and (cl == 'p' or cl.startswith('p_') or cl.endswith('_p')): matches.append(c)
            elif t == 'k' and (cl == 'k' or cl.startswith('k_') or cl.endswith('_k')): matches.append(c)
            elif len(t) > 1 and t in cl: matches.append(c)
    return list(set(matches))

print("pH:", check_col(['ph']))
print("EC:", check_col(['ec', 'electrical']))
print("Organic Carbon:", check_col(['oc', 'organic', 'carbon']))
print("N (Nitrogen):", check_col(['n', 'nitrogen']))
print("P (Phosphorus):", check_col(['p', 'phosphorus', 'phosphate']))
print("K (Potassium):", check_col(['k', 'potassium']))
print("Micronutrients (Zn, Fe, Cu, Mn, B):", check_col(['zn', 'zinc', 'fe', 'iron', 'cu', 'copper', 'mn', 'manganese', 'b', 'boron']))
