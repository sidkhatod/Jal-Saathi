from pydantic import BaseModel
from typing import Optional, List

class Advisory(BaseModel):
    name: str
    crop: str
    problem_name: str
    type: str # e.g. "disease", "pest", "deficiency"
    growth_stage: Optional[str] = None
    symptoms: Optional[str] = None
    control_measures: Optional[List[str]] = None
    source_url: Optional[str] = None
    reviewed: bool = False
