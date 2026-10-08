import re

files = {
    "t11": r"C:\Users\DELL\.gemini\antigravity-ide\brain\5f770e44-dca0-41de-b26b-d1ac90c00f5e\.system_generated\steps\187\content.md",
    "t22": r"C:\Users\DELL\.gemini\antigravity-ide\brain\5f770e44-dca0-41de-b26b-d1ac90c00f5e\.system_generated\steps\188\content.md",
    "t19": r"C:\Users\DELL\.gemini\antigravity-ide\brain\5f770e44-dca0-41de-b26b-d1ac90c00f5e\.system_generated\steps\189\content.md"
}

for name, path in files.items():
    print(f"\n--- {name} ---")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        matches = []
        for i, line in enumerate(lines):
            l = line.lower()
            if 'rice' in l or 'wheat' in l or 'clay' in l or 'loam' in l or 'sand' in l:
                matches.append(line.strip())
        print(f"Found {len(matches)} matches.")
        for m in matches[:10]:
            print(m)
    except Exception as e:
        print(e)
