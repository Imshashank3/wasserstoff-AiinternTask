"""
Document processor for handling document uploads, OCR, and text extraction.
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import logging
from typing import Dict, List, Optional, Any

from app import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles document processing, including:
    - PDF text extraction using poppler-utils
    - OCR for scanned documents and images
    - Text preprocessing and cleaning
    - Document storage and management
    """
    
    def __init__(self):
        """Initialize the document processor."""
        # Ensure required directories exist
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        os.makedirs(config.PROCESSED_DIR, exist_ok=True)
        
        # Path to document metadata storage
        self.metadata_file = os.path.join(config.DATA_DIR, "document_metadata.json")
        self.documents = self._load_documents()
    
    def _load_documents(self) -> Dict[str, Dict[str, Any]]:
        """Load document metadata from storage."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading document metadata: {str(e)}")
                return {}
        return {}
    
    def _save_documents(self):
        """Save document metadata to storage."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving document metadata: {str(e)}")
    
    def process_document(self, document: Dict[str, Any]):
        """
        Process a document based on its file type.
        
        Args:
            document: Document metadata dictionary
        """
        doc_id = document["id"]
        file_path = document["file_path"]
        file_type = document["file_type"].lower()
        
        try:
            # Create processed directory for this document
            processed_dir = os.path.join(config.PROCESSED_DIR, doc_id)
            os.makedirs(processed_dir, exist_ok=True)
            
            # Extract text based on file type
            if file_type == "pdf":
                text, page_count = self._process_pdf(file_path, processed_dir)
            elif file_type in ["png", "jpg", "jpeg", "tiff", "bmp"]:
                text, page_count = self._process_image(file_path, processed_dir)
            elif file_type in ["doc", "docx"]:
                text, page_count = self._process_word(file_path, processed_dir)
            else:
                # Plain text or other supported formats
                text, page_count = self._process_text(file_path, processed_dir)
            
            # Save extracted text
            text_file = os.path.join(processed_dir, "extracted_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Update document metadata
            document["status"] = "processed"
            document["processed_path"] = processed_dir
            document["page_count"] = page_count
            document["processed_time"] = datetime.now().isoformat()
            document["text_length"] = len(text)
            
            # Save updated metadata
            self.documents[doc_id] = document
            self._save_documents()
            
            logger.info(f"Document {doc_id} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {str(e)}")
            document["status"] = "error"
            document["error_message"] = str(e)
            self.documents[doc_id] = document
            self._save_documents()
            return False
    
    def _process_pdf(self, file_path: str, output_dir: str) -> tuple[str, int]:
        """
        Process PDF document using poppler-utils with OCR fallback.
        
        Args:
            file_path: Path to the PDF file
            output_dir: Directory to store processed files
            
        Returns:
            tuple: (extracted text, page count)
        """
        # First try using pdftotext from poppler-utils
        text = ""
        try:
            # Extract text using pdftotext (poppler-utils)
            text_file = os.path.join(output_dir, "pdftotext_output.txt")
            subprocess.run(
                ["pdftotext", "-layout", file_path, text_file],
                check=True,
                capture_output=True
            )
            
            # Read extracted text
            with open(text_file, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            
            # If text is empty or very short, it might be a scanned PDF
            if len(text.strip()) < 100:
                logger.info(f"PDF appears to be scanned or has little text, falling back to OCR")
                return self._process_pdf_with_ocr(file_path, output_dir)
                
            # Get page count
            info_output = subprocess.run(
                ["pdfinfo", file_path],
                check=True,
                capture_output=True,
                text=True
            ).stdout
            
            # Extract page count from pdfinfo output
            page_count = 0
            for line in info_output.split('\n'):
                if line.startswith('Pages:'):
                    page_count = int(line.split(':')[1].strip())
                    break
            
            return text, page_count
            
        except Exception as e:
            logger.warning(f"Error using poppler-utils: {str(e)}. Falling back to OCR.")
            return self._process_pdf_with_ocr(file_path, output_dir)
    
    def _process_pdf_with_ocr(self, file_path: str, output_dir: str) -> tuple[str, int]:
        """
        Process PDF using OCR when text extraction fails.
        
        Args:
            file_path: Path to the PDF file
            output_dir: Directory to store processed files
            
        Returns:
            tuple: (extracted text, page count)
        """
        # Convert PDF to images
        images = convert_from_path(file_path)
        page_count = len(images)
        
        # Create directory for page images
        images_dir = os.path.join(output_dir, "page_images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Process each page with OCR
        all_text = []
        for i, image in enumerate(images):
            # Save page image
            image_path = os.path.join(images_dir, f"page_{i+1}.png")
            image.save(image_path, "PNG")
            
            # Perform OCR
            if config.OCR_ENGINE == "tesseract":
                page_text = pytesseract.image_to_string(image, lang=config.OCR_LANGUAGE)
            elif config.OCR_ENGINE == "paddleocr":
                # Import PaddleOCR only when needed to avoid unnecessary loading
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang=config.OCR_LANGUAGE)
                result = ocr.ocr(image_path, cls=True)
                page_text = "\n".join([line[1][0] for line in result[0]]) if result[0] else ""
            else:
                raise ValueError(f"Unsupported OCR engine: {config.OCR_ENGINE}")
            
            all_text.append(f"--- Page {i+1} ---\n{page_text}\n")
        
        # Combine text from all pages
        full_text = "\n".join(all_text)
        
        return full_text, page_count
    
    def _process_image(self, file_path: str, output_dir: str) -> tuple[str, int]:
        """
        Process image document using OCR.
        
        Args:
            file_path: Path to the image file
            output_dir: Directory to store processed files
            
        Returns:
            tuple: (extracted text, page count)
        """
        try:
            # Open image
            image = Image.open(file_path)
            
            # Perform OCR
            if config.OCR_ENGINE == "tesseract":
                text = pytesseract.image_to_string(image, lang=config.OCR_LANGUAGE)
            elif config.OCR_ENGINE == "paddleocr":
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang=config.OCR_LANGUAGE)
                result = ocr.ocr(file_path, cls=True)
                text = "\n".join([line[1][0] for line in result[0]]) if result[0] else ""
            else:
                raise ValueError(f"Unsupported OCR engine: {config.OCR_ENGINE}")
            
            return text, 1  # Images are single page
        except Exception as e:
            logger.error(f"Error processing image with OCR: {str(e)}")
            raise
    
    def _process_word(self, file_path: str, output_dir: str) -> tuple[str, int]:
        """
        Process Word document.
        
        Args:
            file_path: Path to the Word file
            output_dir: Directory to store processed files
            
        Returns:
            tuple: (extracted text, page count)
        """
        try:
            # Convert docx to text using docx2txt or antiword
            if file_path.endswith('.docx'):
                # Try using python-docx2txt
                try:
                    import docx2txt
                    text = docx2txt.process(file_path)
                except ImportError:
                    # Fall back to external tool
                    text_file = os.path.join(output_dir, "word_text.txt")
                    subprocess.run(
                        ["docx2txt", file_path, text_file],
                        check=True,
                        capture_output=True
                    )
                    with open(text_file, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
            else:
                # For .doc files, try using antiword
                text = subprocess.run(
                    ["antiword", file_path],
                    check=True,
                    capture_output=True,
                    text=True
                ).stdout
            
            # Estimate page count (rough approximation)
            page_count = max(1, len(text) // 3000)  # ~3000 chars per page
            
            return text, page_count
        except Exception as e:
            logger.error(f"Error processing Word document: {str(e)}")
            # Fall back to converting to PDF and then processing
            try:
                # Convert to PDF using LibreOffice
                pdf_path = os.path.join(output_dir, "converted.pdf")
                subprocess.run(
                    ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, file_path],
                    check=True,
                    capture_output=True
                )
                
                # Process the converted PDF
                return self._process_pdf(pdf_path, output_dir)
            except Exception as e2:
                logger.error(f"Error converting Word to PDF: {str(e2)}")
                raise Exception(f"Failed to process Word document: {str(e)} and conversion failed: {str(e2)}")
    
    def _process_text(self, file_path: str, output_dir: str) -> tuple[str, int]:
        """
        Process plain text document.
        
        Args:
            file_path: Path to the text file
            output_dir: Directory to store processed files
            
        Returns:
            tuple: (extracted text, page count)
        """
        try:
            # Read text file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            
            # Estimate page count (rough approximation)
            page_count = max(1, len(text) // 3000)  # ~3000 chars per page
            
            return text, page_count
        except Exception as e:
            logger.error(f"Error processing text document: {str(e)}")
            raise
    
    def list_documents(self, skip: int = 0, limit: int = 100, 
                      status: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List documents with optional filtering.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Filter by document status
            tag: Filter by document tag
            
        Returns:
            List of document metadata dictionaries
        """
        filtered_docs = []
        
        for doc_id, doc in self.documents.items():
            # Apply filters
            if status and doc.get("status") != status:
                continue
            if tag and tag not in doc.get("tags", []):
                continue
            
            # Add to results
            filtered_docs.append(doc)
        
        # Apply pagination
        return filtered_docs[skip:skip+limit]
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document metadata dictionary or None if not found
        """
        return self.documents.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated files.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        if document_id not in self.documents:
            return False
        
        try:
            # Get document metadata
            document = self.documents[document_id]
            
            # Delete uploaded file
            if "file_path" in document and os.path.exists(document["file_path"]):
                os.remove(document["file_path"])
            
            # Delete processed directory
            if "processed_path" in document and os.path.exists(document["processed_path"]):
                shutil.rmtree(document["processed_path"])
            
            # Remove from metadata
            del self.documents[document_id]
            self._save_documents()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
