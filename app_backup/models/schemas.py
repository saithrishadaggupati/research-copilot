from pydantic import BaseModel
from typing import Optional, List


class ResearchRequest(BaseModel):
    query: str
    max_results: int = 5
    use_web_search: bool = True


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    relevance_score: float


class ResearchResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float
    sources: List[SearchResult]
    model_used: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None