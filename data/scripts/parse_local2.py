import pandas as pd

paths = {
    "11_12": r"C:\Users\DELL\.gemini\antigravity-ide\brain\5f770e44-dca0-41de-b26b-d1ac90c00f5e\.system_generated\steps\187\content.md",
    "22": r"C:\Users\DELL\.gemini\antigravity-ide\brain\5f770e44-dca0-41de-b26b-d1ac90c00f5e\.system_generated\steps\188\content.md",
    "19": r"C:\Users\DELL\.gemini\antigravity-ide\brain\5f770e44-dca0-41de-b26b-d1ac90c00f5e\.system_generated\steps\189\content.md"
}

for name, path in paths.items():
    print(f"\n--- {name} ---")
    try:
        tables = pd.read_html(path)
        for i, df in enumerate(tables):
            text = df.to_string().lower()
            if 'rice' in text or 'wheat' in text or 'sand' in text or 'clay' in text:
                print(f"Table {i} matches!")
                mask = df.apply(lambda row: row.astype(str).str.contains('Rice|Wheat|Sand|Clay|Loam|Texture', case=False).any(), axis=1)
                print(df[mask].to_string())
    except Exception as e:
        print(e)
