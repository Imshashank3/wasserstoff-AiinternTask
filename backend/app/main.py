"""
Main application entry point for the Document Research & Theme Identification Chatbot.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import uvicorn
import os
from pathlib import Path

from app.api.routes import api_router
from app import config

# Create FastAPI application
app = FastAPI(
    title=config.PROJECT_NAME,
    description="An interactive chatbot that performs research across documents, identifies themes, and provides cited responses.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=config.API_PREFIX)

# Mount static files for frontend
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
