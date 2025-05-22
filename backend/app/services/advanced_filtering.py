"""
Advanced filtering service for document and query filtering.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedFilteringService:
    """
    Service for advanced filtering options, providing:
    - Date-based filtering
    - Author filtering
    - Document type filtering
    - Relevance score filtering
    """
    
    def __init__(self):
        """Initialize the advanced filtering service."""
        # Path to filter metadata storage
        self.filter_metadata_file = os.path.join(config.DATA_DIR, "filter_metadata.json")
        self.filter_metadata = self._load_filter_metadata()
    
    def _load_filter_metadata(self) -> Dict[str, Any]:
        """Load filter metadata from storage."""
        if os.path.exists(self.filter_metadata_file):
            try:
                with open(self.filter_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading filter metadata: {str(e)}")
                return {"document_filters": {}, "available_filters": {}}
        return {"document_filters": {}, "available_filters": {}}
    
    def _save_filter_metadata(self):
        """Save filter metadata to storage."""
        try:
            with open(self.filter_metadata_file, 'w') as f:
                json.dump(self.filter_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving filter metadata: {str(e)}")
    
    def extract_document_metadata(self, document: Dict[str, Any]) -> bool:
        """
        Extract metadata from a document for filtering.
        
        Args:
            document: Document metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_id = document["id"]
            
            # Extract metadata for filtering
            filter_data = {
                "document_id": doc_id,
                "title": document.get("title", ""),
                "upload_date": document.get("upload_time", ""),
                "file_type": document.get("file_type", ""),
                "tags": document.get("tags", []),
                "page_count": document.get("page_count", 0),
                "text_length": document.get("text_length", 0),
                "status": document.get("status", ""),
                "extracted_metadata": {}
            }
            
            # Extract additional metadata if document has been processed
            if document.get("status") == "processed" and "processed_path" in document:
                # Try to extract author, creation date, etc.
                extracted = self._extract_additional_metadata(document)
                filter_data["extracted_metadata"] = extracted
            
            # Save filter data
            self.filter_metadata["document_filters"][doc_id] = filter_data
            
            # Update available filters
            self._update_available_filters()
            
            # Save metadata
            self._save_filter_metadata()
            
            logger.info(f"Filter metadata extracted for document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting filter metadata: {str(e)}")
            return False
    
    def _extract_additional_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from document content.
        
        Args:
            document: Document metadata dictionary
            
        Returns:
            Dictionary of extracted metadata
        """
        extracted = {}
        
        try:
            # Get file path
            file_path = document.get("file_path")
            file_type = document.get("file_type", "").lower()
            
            # Extract metadata based on file type
            if file_type == "pdf":
                # Use pdfinfo to extract metadata
                try:
                    import subprocess
                    info_output = subprocess.run(
                        ["pdfinfo", file_path],
                        check=True,
                        capture_output=True,
                        text=True
                    ).stdout
                    
                    # Parse pdfinfo output
                    for line in info_output.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().lower().replace(' ', '_')
                            value = value.strip()
                            
                            if key in ['author', 'creator', 'producer', 'creation_date', 'mod_date', 'subject', 'keywords']:
                                extracted[key] = value
                except Exception as e:
                    logger.warning(f"Error extracting PDF metadata: {str(e)}")
            
            elif file_type in ["doc", "docx"]:
                # Try to extract metadata from Word documents
                try:
                    if file_type == "docx":
                        import docx
                        doc = docx.Document(file_path)
                        core_props = doc.core_properties
                        
                        if core_props.author:
                            extracted["author"] = core_props.author
                        if core_props.created:
                            extracted["creation_date"] = core_props.created.isoformat()
                        if core_props.modified:
                            extracted["mod_date"] = core_props.modified.isoformat()
                        if core_props.subject:
                            extracted["subject"] = core_props.subject
                        if core_props.keywords:
                            extracted["keywords"] = core_props.keywords
                except Exception as e:
                    logger.warning(f"Error extracting Word metadata: {str(e)}")
            
            # Try to extract date from filename or content
            if "creation_date" not in extracted:
                # Look for date patterns in filename
                import re
                filename = document.get("original_filename", "")
                date_match = re.search(r'(\d{4}[-_/]\d{1,2}[-_/]\d{1,2})', filename)
                if date_match:
                    extracted["extracted_date"] = date_match.group(1)
            
            return extracted
            
        except Exception as e:
            logger.error(f"Error in additional metadata extraction: {str(e)}")
            return {}
    
    def _update_available_filters(self):
        """Update available filters based on document metadata."""
        available = {
            "file_types": set(),
            "tags": set(),
            "authors": set(),
            "date_ranges": {
                "min": None,
                "max": None
            },
            "page_count_ranges": {
                "min": None,
                "max": None
            }
        }
        
        # Process each document
        for doc_id, filter_data in self.filter_metadata["document_filters"].items():
            # File types
            file_type = filter_data.get("file_type", "")
            if file_type:
                available["file_types"].add(file_type)
            
            # Tags
            for tag in filter_data.get("tags", []):
                if tag:
                    available["tags"].add(tag)
            
            # Authors
            author = filter_data.get("extracted_metadata", {}).get("author")
            if author:
                available["authors"].add(author)
            
            # Upload date
            upload_date = filter_data.get("upload_date")
            if upload_date:
                try:
                    date_obj = datetime.fromisoformat(upload_date)
                    if available["date_ranges"]["min"] is None or date_obj < available["date_ranges"]["min"]:
                        available["date_ranges"]["min"] = date_obj
                    if available["date_ranges"]["max"] is None or date_obj > available["date_ranges"]["max"]:
                        available["date_ranges"]["max"] = date_obj
                except:
                    pass
            
            # Page count
            page_count = filter_data.get("page_count", 0)
            if page_count > 0:
                if available["page_count_ranges"]["min"] is None or page_count < available["page_count_ranges"]["min"]:
                    available["page_count_ranges"]["min"] = page_count
                if available["page_count_ranges"]["max"] is None or page_count > available["page_count_ranges"]["max"]:
                    available["page_count_ranges"]["max"] = page_count
        
        # Convert sets to lists for JSON serialization
        available["file_types"] = sorted(list(available["file_types"]))
        available["tags"] = sorted(list(available["tags"]))
        available["authors"] = sorted(list(available["authors"]))
        
        # Convert datetime objects to strings
        if available["date_ranges"]["min"]:
            available["date_ranges"]["min"] = available["date_ranges"]["min"].isoformat()
        if available["date_ranges"]["max"]:
            available["date_ranges"]["max"] = available["date_ranges"]["max"].isoformat()
        
        # Save available filters
        self.filter_metadata["available_filters"] = available
    
    def filter_documents(self, filters: Dict[str, Any]) -> List[str]:
        """
        Filter documents based on criteria.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            List of document IDs matching filters
        """
        try:
            matching_docs = []
            
            # Process each document
            for doc_id, filter_data in self.filter_metadata["document_filters"].items():
                # Check if document matches all filters
                if self._document_matches_filters(filter_data, filters):
                    matching_docs.append(doc_id)
            
            return matching_docs
            
        except Exception as e:
            logger.error(f"Error filtering documents: {str(e)}")
            return []
    
    def _document_matches_filters(self, doc_filter_data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if a document matches the specified filters.
        
        Args:
            doc_filter_data: Document filter data
            filters: Filter criteria
            
        Returns:
            True if document matches all filters, False otherwise
        """
        # File type filter
        if "file_type" in filters and filters["file_type"]:
            if doc_filter_data.get("file_type") != filters["file_type"]:
                return False
        
        # Tags filter
        if "tags" in filters and filters["tags"]:
            doc_tags = set(doc_filter_data.get("tags", []))
            filter_tags = set(filters["tags"])
            if not filter_tags.issubset(doc_tags):
                return False
        
        # Author filter
        if "author" in filters and filters["author"]:
            doc_author = doc_filter_data.get("extracted_metadata", {}).get("author", "")
            if filters["author"].lower() not in doc_author.lower():
                return False
        
        # Date range filter
        if "date_range" in filters and filters["date_range"]:
            date_min = filters["date_range"].get("min")
            date_max = filters["date_range"].get("max")
            
            # Try upload date first
            doc_date = doc_filter_data.get("upload_date", "")
            
            # If not available, try extracted creation date
            if not doc_date:
                doc_date = doc_filter_data.get("extracted_metadata", {}).get("creation_date", "")
            
            # If still not available, try extracted date
            if not doc_date:
                doc_date = doc_filter_data.get("extracted_metadata", {}).get("extracted_date", "")
            
            if doc_date:
                try:
                    date_obj = datetime.fromisoformat(doc_date)
                    
                    if date_min:
                        min_obj = datetime.fromisoformat(date_min)
                        if date_obj < min_obj:
                            return False
                    
                    if date_max:
                        max_obj = datetime.fromisoformat(date_max)
                        if date_obj > max_obj:
                            return False
                except:
                    # If date parsing fails, skip this filter
                    pass
        
        # Page count range filter
        if "page_count_range" in filters and filters["page_count_range"]:
            page_min = filters["page_count_range"].get("min")
            page_max = filters["page_count_range"].get("max")
            
            doc_pages = doc_filter_data.get("page_count", 0)
            
            if page_min is not None and doc_pages < page_min:
                return False
            
            if page_max is not None and doc_pages > page_max:
                return False
        
        # Text search filter
        if "text_search" in filters and filters["text_search"]:
            search_text = filters["text_search"].lower()
            
            # Check title
            if search_text in doc_filter_data.get("title", "").lower():
                return True
            
            # Check tags
            for tag in doc_filter_data.get("tags", []):
                if search_text in tag.lower():
                    return True
            
            # Check extracted metadata
            for key, value in doc_filter_data.get("extracted_metadata", {}).items():
                if isinstance(value, str) and search_text in value.lower():
                    return True
            
            # If we get here and text_search is specified, it's not a match
            return False
        
        # If we get here, document matches all filters
        return True
    
    def get_available_filters(self) -> Dict[str, Any]:
        """
        Get available filter options.
        
        Returns:
            Dictionary of available filter options
        """
        return self.filter_metadata["available_filters"]
