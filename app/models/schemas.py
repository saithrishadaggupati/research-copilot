from pydantic import BaseModel
from typing import Optional, List


class ResearchRequest(BaseModel):
    query: str
    max_results: int = 5
    use_web_search: bool = True

class ResearchRequest(BaseModel):
    query: str
    max_results: int = 5
    use_web_search: bool = True
    use_documents: bool = False


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
    query_variants: List[str] = []
    cost_usd: float = 0.0
    tokens_used: int = 0

class DocumentInfo(BaseModel):
    doc_id: str
    filename: str


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunks: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class CostRecord(BaseModel):
    timestamp: str
    query: str
    tokens_used: int
    cost_usd: float
