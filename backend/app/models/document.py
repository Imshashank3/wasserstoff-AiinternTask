"""
Document model definitions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentCreate(BaseModel):
    """Schema for document creation."""
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []

class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    title: str
    filename: str
    file_type: str
    upload_time: str
    status: str
    page_count: Optional[int] = None
    message: Optional[str] = None
    error_message: Optional[str] = None

class DocumentList(BaseModel):
    """Schema for document list response."""
    total: int
    documents: List[Dict[str, Any]]
