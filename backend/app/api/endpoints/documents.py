"""
API endpoints for document management.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime

from app import config
from app.core.document_processor import DocumentProcessor
from app.models.document import DocumentCreate, DocumentResponse, DocumentList

router = APIRouter()
document_processor = DocumentProcessor()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """
    Upload a document for processing and indexing.
    
    - Accepts PDF, images, and text documents
    - Performs OCR on scanned documents if needed
    - Extracts text and metadata
    - Stores document in the system
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique document ID and create file path
    doc_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{doc_id}.{file_ext}"
    file_path = os.path.join(config.UPLOAD_DIR, safe_filename)
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create document metadata
    doc_title = title or os.path.splitext(file.filename)[0]
    doc_tags = tags.split(",") if tags else []
    
    # Process document in background
    document = {
        "id": doc_id,
        "filename": safe_filename,
        "original_filename": file.filename,
        "title": doc_title,
        "description": description,
        "tags": doc_tags,
        "file_path": file_path,
        "file_type": file_ext,
        "upload_time": datetime.now().isoformat(),
        "status": "processing",
        "page_count": None,
        "processed_path": None
    }
    
    # Schedule background processing
    background_tasks.add_task(
        document_processor.process_document,
        document
    )
    
    return DocumentResponse(
        id=doc_id,
        title=doc_title,
        filename=file.filename,
        file_type=file_ext,
        upload_time=document["upload_time"],
        status="processing",
        message="Document uploaded and queued for processing"
    )

@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    tag: Optional[str] = None
):
    """
    List all uploaded documents with optional filtering.
    """
    documents = document_processor.list_documents(skip, limit, status, tag)
    return DocumentList(
        total=len(documents),
        documents=documents
    )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get details for a specific document.
    """
    document = document_processor.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the system.
    """
    success = document_processor.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}
