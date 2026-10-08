import pandas as pd

csv_path = 'raw/soil-nutrient-analysis.csv'
df = pd.read_csv(csv_path, usecols=['nutrient_name', 'nutrient_type', 'nutrient_level'])

print("Nutrient Names:", df['nutrient_name'].dropna().unique())
print("Nutrient Types:", df['nutrient_type'].dropna().unique())
print("Nutrient Levels:", df['nutrient_level'].dropna().unique())
