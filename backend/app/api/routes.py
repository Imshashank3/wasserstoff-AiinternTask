"""
API routes for the Document Research & Theme Identification Chatbot.
"""
from fastapi import APIRouter

from app.api.endpoints import documents, queries, themes

# Create API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
api_router.include_router(themes.router, prefix="/themes", tags=["themes"])
