from pydantic import BaseModel
from typing import Optional, List

class Advisory(BaseModel):
    name: str
    crop: str
    problem_name: str
    type: str # e.g. "disease", "pest", "deficiency"
    growth_stage: Optional[str] = None
    symptoms: Optional[str] = None
    organic_option: Optional[str] = None
    chemical_option: Optional[str] = None
    weather_constraints: Optional[str] = None
    source_url: Optional[str] = None
    source_org: Optional[str] = None
    source_quote: Optional[str] = None
    reviewed: bool = False
