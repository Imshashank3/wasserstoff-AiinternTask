"""
API endpoints for theme identification.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel

from app.core.theme_processor import ThemeProcessor
from app.models.theme import ThemeRequest, ThemeResponse

router = APIRouter()
theme_processor = ThemeProcessor()

@router.post("/", response_model=ThemeResponse)
async def identify_themes(theme_request: ThemeRequest):
    """
    Identify common themes across a set of documents.
    
    - Analyzes document content
    - Identifies coherent common themes
    - Returns themes with supporting citations
    """
    try:
        result = theme_processor.identify_themes(
            document_ids=theme_request.document_ids,
            min_documents=theme_request.min_documents,
            similarity_threshold=theme_request.similarity_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme identification failed: {str(e)}")

@router.get("/", response_model=List[ThemeResponse])
async def list_themes():
    """
    List all identified themes in the document collection.
    """
    try:
        themes = theme_processor.list_themes()
        return themes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list themes: {str(e)}")

@router.get("/{theme_id}", response_model=ThemeResponse)
async def get_theme(theme_id: str):
    """
    Get details for a specific theme.
    """
    theme = theme_processor.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme
