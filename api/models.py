from pydantic import BaseModel
from typing import List, Optional

class VaultIngest(BaseModel):
    source: str
    chunk: str
    summary: str
    links: List[str] = []

class VaultQuery(BaseModel):
    query: str
    top_k: int = 5

class DecisionOption(BaseModel):
    option: str
    pros: List[str] = []
    cons: List[str] = []

class DecisionCreate(BaseModel):
    topic: str
    options: List[DecisionOption]

class DecisionRecommend(BaseModel):
    rationale: Optional[str] = None

class DecisionStatusUpdate(BaseModel):
    status: str   # 'approved' or 'declined'