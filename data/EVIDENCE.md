# Evidence Report

## Advisories (User-Verified)

### `data/advisories/paddy_blast.yaml`
- **Field:** `symptoms`, `organic_option`, `chemical_option`, `weather_constraints`
- **Source URL:** https://biolens-ai.com/blog/rice-blast-disease-identification-treatment/
- **Status:** Manually verified and provided by the user. 
- **CIB&RC Registration Evidence:** 
  - *Trifloxystrobin 25% + Tebuconazole 50% WG (Nativo)*: CIB&RC Registered for Rice (Paddy) leaf blast and neck blast.
  - *Tricyclazole 45% + Hexaconazole 10% WG*: CIB&RC Registered for Rice (Paddy) blast.

### `data/advisories/wheat_rust.yaml`
- **Field:** `symptoms`, `organic_option`, `chemical_option`, `weather_constraints`
- **Source URL:** https://silks.csb.gov.in/dhubri/diseases-and-pests-of-food-plants/
- **Status:** Manually verified and provided by the user. 
- **CIB&RC Registration Evidence:** Not directly searched; user-verified.

## Crop Parameters (FAO-56)

### `data/crops/paddy.yaml`
- **Source URL:** https://www.fao.org/3/x0490e/x0490e0b.htm
- **Status:** Values (`kc_ini`, `kc_mid`, `kc_end`, `stage_*_days`) were manually verified and provided by the user.
- **Field `max_root_depth_m`**: Kept at user's derived midpoint `0.75` with `# range: 0.5-1.00` stored alongside.
- **Field `depletion_fraction`**:
  - **Value:** `0.20`
  - **Verbatim quote:** Table 22: "Ranges of maximum effective rooting depth (Zr), and soil water depletion fraction for no stress (p), for common crops" | Row: "Rice" | Depletion fraction (p): "0.20"

### `data/crops/wheat.yaml`
- **Source URL:** https://www.fao.org/3/x0490e/x0490e0b.htm
- **Status:** Values (`kc_ini`, `kc_mid`, `kc_end`, `stage_*_days`) were manually verified and provided by the user.
- **Field `max_root_depth_m`**: Kept at user's derived midpoint `1.65` with `# range: 1.5-1.80` stored alongside.
- **Field `depletion_fraction`**:
  - **Value:** `0.55`
  - **Verbatim quote:** Table 22: "Ranges of maximum effective rooting depth (Zr), and soil water depletion fraction for no stress (p), for common crops" | Row: "Winter wheat" | Depletion fraction (p): "0.55"
