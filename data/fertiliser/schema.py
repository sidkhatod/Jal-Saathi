from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

class FertiliserRule(BaseModel):
    crop: str
    rating_n: Optional[str] = None
    rating_p: Optional[str] = None
    rating_k: Optional[str] = None
    recommended_n_kg_ha: Optional[float] = None
    recommended_p_kg_ha: Optional[float] = None
    recommended_k_kg_ha: Optional[float] = None
    timing_notes: Optional[str] = None
    citation_url: HttpUrl
    reviewed: bool = False
