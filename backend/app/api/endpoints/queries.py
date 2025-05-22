"""
API endpoints for query processing.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel

from app.core.query_processor import QueryProcessor
from app.models.query import QueryRequest, QueryResponse

router = APIRouter()
query_processor = QueryProcessor()

@router.post("/", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """
    Process a natural language query against the document collection.
    
    - Executes query against each document
    - Extracts relevant responses with citations
    - Returns individual document responses
    """
    try:
        result = query_processor.process_query(
            query=query_request.query,
            document_ids=query_request.document_ids,
            max_results=query_request.max_results
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.post("/themes", response_model=QueryResponse)
async def identify_themes(query_request: QueryRequest):
    """
    Process a query and identify themes across document responses.
    
    - Executes query against documents
    - Identifies common themes across responses
    - Returns synthesized answer with theme identification
    """
    try:
        result = query_processor.identify_themes(
            query=query_request.query,
            document_ids=query_request.document_ids,
            max_results=query_request.max_results
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme identification failed: {str(e)}")
