import os
import re

FORBIDDEN_WORDS = ["mock", "hardcoded", "fixture", "placeholder", "lorem"]
DOSE_BRAND_STRINGS = ["kg/ha", "g/l", "ml/l", "nativo", "karathane", "sulfex"]

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def scan_forbidden_words():
    print("--- 1. Scanning src/i18n and public/data for forbidden words ---")
    target_dirs = [
        os.path.join(ROOT_DIR, "src", "i18n"),
        os.path.join(ROOT_DIR, "public", "data")
    ]
    
    findings = []
    for t_dir in target_dirs:
        if not os.path.exists(t_dir):
            continue
        for root, _, files in os.walk(t_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        for word in FORBIDDEN_WORDS:
                            if re.search(r'\b' + re.escape(word) + r'\b', line, re.IGNORECASE):
                                findings.append(f"{file_path}:{idx}: contains forbidden word '{word}' -> {line.strip()[:80]}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    if not findings:
        print("[PASS] Zero forbidden words found in src/i18n and public/data.")
    else:
        print(f"[FAIL] Found {len(findings)} matches:")
        for match in findings:
            print(f"  {match}")
    return len(findings)

def scan_build_for_doses():
    print("\n--- 2. Scanning dist/ for dose or brand strings ---")
    dist_dir = os.path.join(ROOT_DIR, "dist")
    if not os.path.exists(dist_dir):
        print("[FAIL] dist/ directory does not exist! Run npm run build first.")
        return 1

    findings = []
    text_extensions = ('.html', '.js', '.css', '.json')
    for root, _, files in os.walk(dist_dir):
        for file in files:
            if not file.endswith(text_extensions):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                for target in DOSE_BRAND_STRINGS:
                    if target.lower() in content:
                        findings.append(f"{file_path}: contains '{target}'")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    if not findings:
        print("[PASS] Zero dose or commercial brand strings found in dist/.")
    else:
        print(f"[FAIL] Found {len(findings)} matches:")
        for match in findings:
            print(f"  {match}")
    return len(findings)

if __name__ == "__main__":
    c1 = scan_forbidden_words()
    c2 = scan_build_for_doses()
    total = c1 + c2
    print(f"\nFinal Result: {'PASS (0 violations)' if total == 0 else f'FAIL ({total} violations)'}")
    exit(0 if total == 0 else 1)
