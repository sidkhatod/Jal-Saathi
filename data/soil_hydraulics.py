import os
from pydantic import BaseModel
from typing import Optional

class SoilHydraulics(BaseModel):
    texture_class: str
    field_capacity_mm_per_m: float
    wilting_point_mm_per_m: float
    citation: str
    texture_source: Optional[str] = None

    @property
    def available_water_capacity_mm_per_m(self) -> float:
        return self.field_capacity_mm_per_m - self.wilting_point_mm_per_m

# FAO-56 Table 19: Soil water characteristics for different soil types
# Ranges (m3/m3 converted to mm/m):
# Sand: FC 70-170, WP 20-70
# Loam: FC 200-300, WP 70-170
# Clay: FC 320-400, WP 200-240
# Rule used: Median of ranges (derived).
TEXTURE_LOOKUP = {
    "clay": SoilHydraulics(
        texture_class="clay",
        field_capacity_mm_per_m=360.0,
        wilting_point_mm_per_m=220.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm#table19",
        texture_source="default"
    ),
    "loam": SoilHydraulics(
        texture_class="loam",
        field_capacity_mm_per_m=250.0,
        wilting_point_mm_per_m=120.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm#table19",
        texture_source="default"
    ),
    "sand": SoilHydraulics(
        texture_class="sand",
        field_capacity_mm_per_m=120.0,
        wilting_point_mm_per_m=45.0,
        citation="https://www.fao.org/3/x0490e/x0490e0c.htm#table19",
        texture_source="default"
    )
}

def get_soil_hydraulics(lat: float, lon: float) -> SoilHydraulics:
    return TEXTURE_LOOKUP["loam"]
