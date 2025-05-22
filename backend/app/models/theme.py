"""
Theme model definitions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ThemeRequest(BaseModel):
    """Schema for theme identification request."""
    document_ids: Optional[List[str]] = None
    min_documents: Optional[int] = 2
    similarity_threshold: Optional[float] = 0.75

class ThemeCitation(BaseModel):
    """Schema for theme citation."""
    document_id: str
    document_title: str
    citation: str
    relevance_score: float

class Theme(BaseModel):
    """Schema for identified theme."""
    id: str
    name: str
    description: str
    document_count: int
    citations: List[ThemeCitation]

class ThemeResponse(BaseModel):
    """Schema for theme identification response."""
    themes: List[Theme]
    synthesized_response: Optional[str] = None
