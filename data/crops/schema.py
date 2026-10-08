from pydantic import BaseModel
from typing import Optional

class CropParameters(BaseModel):
    name: str
    kc_ini: Optional[float] = None
    kc_mid: Optional[float] = None
    kc_end: Optional[float] = None
    stage_ini_days: Optional[int] = None
    stage_dev_days: Optional[int] = None
    stage_mid_days: Optional[int] = None
    stage_late_days: Optional[int] = None
    max_root_depth_m: Optional[float] = None
    depletion_fraction: Optional[float] = None
    citation_url: str
