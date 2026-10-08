import pandas as pd

urls = {
    "table11_12": "https://www.fao.org/3/x0490e/x0490e0b.htm",
    "table22": "https://www.fao.org/3/x0490e/x0490e0e.htm",
    "table19": "https://www.fao.org/3/x0490e/x0490e0c.htm"
}

for name, url in urls.items():
    print(f"\n--- {name} ---")
    try:
        tables = pd.read_html(url)
        print(f"Found {len(tables)} tables")
        for i, df in enumerate(tables):
            text = df.to_string().lower()
            if 'rice' in text or 'wheat' in text or 'texture' in text or 'clay' in text:
                print(f"Table {i} matches!")
                print(df.dropna(how='all').head(30).to_string())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
