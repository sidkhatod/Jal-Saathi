import os

paddy_yaml = """name: "paddy"
kc_ini: 1.00
kc_mid: 1.15
kc_end: 0.60
stage_ini_days: 20
stage_dev_days: 20
stage_mid_days: 30
stage_late_days: 20
max_root_depth_m: 0.75
depletion_fraction: 0.20
citation_url: "https://www.fao.org/3/x0490e/x0490e0b.htm"
"""

wheat_yaml = """name: "wheat"
kc_ini: 0.30
kc_mid: 1.10
kc_end: 0.25
stage_ini_days: 25
stage_dev_days: 27
stage_mid_days: 57
stage_late_days: 35
max_root_depth_m: 1.25
depletion_fraction: 0.55
citation_url: "https://www.fao.org/3/x0490e/x0490e0b.htm"
"""

soil_hydraulics_py = """import os
from pydantic import BaseModel
from typing import Optional

class SoilHydraulics(BaseModel):
    texture_class: str
    field_capacity_mm_per_m: float
    wilting_point_mm_per_m: float
    available_water_capacity_mm_per_m: float
    citation: str
    texture_source: Optional[str] = None

# FAO-56 Table 19 ranges (m3/m3 converted to mm/m):
# Sand: FC 70-170, WP 20-70, AWC 50-110
# Loam: FC 200-300, WP 70-170, AWC 130-180
# Clay: FC 320-400, WP 200-240, AWC 120-200
# Rule used: Median of ranges.
TEXTURE_LOOKUP = {
    "clay": SoilHydraulics(
        texture_class="clay",
        field_capacity_mm_per_m=360.0,
        wilting_point_mm_per_m=220.0,
        available_water_capacity_mm_per_m=160.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm",
        texture_source="default"
    ),
    "loam": SoilHydraulics(
        texture_class="loam",
        field_capacity_mm_per_m=250.0,
        wilting_point_mm_per_m=120.0,
        available_water_capacity_mm_per_m=155.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm",
        texture_source="default"
    ),
    "sand": SoilHydraulics(
        texture_class="sand",
        field_capacity_mm_per_m=120.0,
        wilting_point_mm_per_m=45.0,
        available_water_capacity_mm_per_m=80.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm",
        texture_source="default"
    )
}

def get_soil_hydraulics(lat: float, lon: float) -> SoilHydraulics:
    return TEXTURE_LOOKUP["loam"]
"""

with open('crops/paddy.yaml', 'w') as f:
    f.write(paddy_yaml)
with open('crops/wheat.yaml', 'w') as f:
    f.write(wheat_yaml)
with open('soil_hydraulics.py', 'w') as f:
    f.write(soil_hydraulics_py)
