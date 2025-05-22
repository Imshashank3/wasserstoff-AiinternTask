"""
Query model definitions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    """Schema for query request."""
    query: str
    document_ids: Optional[List[str]] = None
    max_results: Optional[int] = 10

class DocumentResult(BaseModel):
    """Schema for individual document query result."""
    document_id: str
    document_title: str
    extracted_answer: str
    citation: str
    relevance_score: float

class QueryResponse(BaseModel):
    """Schema for query response."""
    query: str
    results: List[DocumentResult]
    themes: Optional[List[Dict[str, Any]]] = None
    synthesized_response: Optional[str] = None
