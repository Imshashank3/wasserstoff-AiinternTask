"""
Document selection service for targeted querying.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Set

from app import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentSelectionService:
    """
    Service for document selection/deselection, providing:
    - Document selection for targeted queries
    - Selection persistence across sessions
    - Selection sharing and export
    """
    
    def __init__(self):
        """Initialize the document selection service."""
        # Path to selection storage
        self.selections_dir = os.path.join(config.DATA_DIR, "selections")
        os.makedirs(self.selections_dir, exist_ok=True)
        
        # Default selection (all documents)
        self.default_selection_file = os.path.join(self.selections_dir, "default_selection.json")
        self.default_selection = self._load_default_selection()
    
    def _load_default_selection(self) -> Dict[str, Any]:
        """Load default selection from storage."""
        if os.path.exists(self.default_selection_file):
            try:
                with open(self.default_selection_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading default selection: {str(e)}")
                return {"name": "All Documents", "document_ids": []}
        return {"name": "All Documents", "document_ids": []}
    
    def _save_default_selection(self):
        """Save default selection to storage."""
        try:
            with open(self.default_selection_file, 'w') as f:
                json.dump(self.default_selection, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving default selection: {str(e)}")
    
    def update_default_selection(self):
        """Update default selection with all available documents."""
        try:
            # Get document processor
            from app.core.document_processor import DocumentProcessor
            doc_processor = DocumentProcessor()
            
            # Get all documents
            all_docs = doc_processor.list_documents()
            
            # Update default selection
            self.default_selection["document_ids"] = [doc["id"] for doc in all_docs]
            self._save_default_selection()
            
            logger.info(f"Default selection updated with {len(all_docs)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error updating default selection: {str(e)}")
            return False
    
    def create_selection(self, name: str, document_ids: List[str], description: Optional[str] = None) -> Optional[str]:
        """
        Create a new document selection.
        
        Args:
            name: Selection name
            document_ids: List of document IDs
            description: Optional description
            
        Returns:
            Selection ID if successful, None otherwise
        """
        try:
            # Generate selection ID
            import uuid
            selection_id = str(uuid.uuid4())
            
            # Create selection data
            selection = {
                "id": selection_id,
                "name": name,
                "description": description or "",
                "document_ids": document_ids,
                "created_at": self._get_timestamp(),
                "updated_at": self._get_timestamp()
            }
            
            # Save selection
            selection_file = os.path.join(self.selections_dir, f"selection_{selection_id}.json")
            with open(selection_file, 'w') as f:
                json.dump(selection, f, indent=2)
            
            logger.info(f"Selection '{name}' created with {len(document_ids)} documents")
            return selection_id
            
        except Exception as e:
            logger.error(f"Error creating selection: {str(e)}")
            return None
    
    def get_selection(self, selection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document selection by ID.
        
        Args:
            selection_id: Selection ID
            
        Returns:
            Selection data if found, None otherwise
        """
        try:
            # Check if default selection
            if selection_id == "default":
                return self.default_selection
            
            # Load selection file
            selection_file = os.path.join(self.selections_dir, f"selection_{selection_id}.json")
            if not os.path.exists(selection_file):
                logger.warning(f"Selection {selection_id} not found")
                return None
            
            with open(selection_file, 'r') as f:
                selection = json.load(f)
            
            return selection
            
        except Exception as e:
            logger.error(f"Error getting selection: {str(e)}")
            return None
    
    def update_selection(self, selection_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing document selection.
        
        Args:
            selection_id: Selection ID
            updates: Dictionary of updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if default selection
            if selection_id == "default":
                # Only allow updating document_ids for default selection
                if "document_ids" in updates:
                    self.default_selection["document_ids"] = updates["document_ids"]
                    self._save_default_selection()
                return True
            
            # Load selection file
            selection_file = os.path.join(self.selections_dir, f"selection_{selection_id}.json")
            if not os.path.exists(selection_file):
                logger.warning(f"Selection {selection_id} not found")
                return False
            
            with open(selection_file, 'r') as f:
                selection = json.load(f)
            
            # Apply updates
            for key, value in updates.items():
                if key in ["name", "description", "document_ids"]:
                    selection[key] = value
            
            # Update timestamp
            selection["updated_at"] = self._get_timestamp()
            
            # Save updated selection
            with open(selection_file, 'w') as f:
                json.dump(selection, f, indent=2)
            
            logger.info(f"Selection {selection_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating selection: {str(e)}")
            return False
    
    def delete_selection(self, selection_id: str) -> bool:
        """
        Delete a document selection.
        
        Args:
            selection_id: Selection ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if default selection
            if selection_id == "default":
                logger.warning("Cannot delete default selection")
                return False
            
            # Check if selection exists
            selection_file = os.path.join(self.selections_dir, f"selection_{selection_id}.json")
            if not os.path.exists(selection_file):
                logger.warning(f"Selection {selection_id} not found")
                return False
            
            # Delete selection file
            os.remove(selection_file)
            
            logger.info(f"Selection {selection_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting selection: {str(e)}")
            return False
    
    def list_selections(self) -> List[Dict[str, Any]]:
        """
        List all available document selections.
        
        Returns:
            List of selection data dictionaries
        """
        try:
            selections = []
            
            # Add default selection
            default = self.default_selection.copy()
            default["id"] = "default"
            default["is_default"] = True
            selections.append(default)
            
            # Get all selection files
            for filename in os.listdir(self.selections_dir):
                if filename.startswith("selection_") and filename.endswith(".json"):
                    try:
                        with open(os.path.join(self.selections_dir, filename), 'r') as f:
                            selection = json.load(f)
                            selection["is_default"] = False
                            selections.append(selection)
                    except Exception as e:
                        logger.warning(f"Error loading selection file {filename}: {str(e)}")
            
            return selections
            
        except Exception as e:
            logger.error(f"Error listing selections: {str(e)}")
            return []
    
    def add_documents_to_selection(self, selection_id: str, document_ids: List[str]) -> bool:
        """
        Add documents to an existing selection.
        
        Args:
            selection_id: Selection ID
            document_ids: List of document IDs to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get selection
            selection = self.get_selection(selection_id)
            if not selection:
                return False
            
            # Add documents
            current_ids = set(selection.get("document_ids", []))
            current_ids.update(document_ids)
            
            # Update selection
            return self.update_selection(selection_id, {"document_ids": list(current_ids)})
            
        except Exception as e:
            logger.error(f"Error adding documents to selection: {str(e)}")
            return False
    
    def remove_documents_from_selection(self, selection_id: str, document_ids: List[str]) -> bool:
        """
        Remove documents from an existing selection.
        
        Args:
            selection_id: Selection ID
            document_ids: List of document IDs to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get selection
            selection = self.get_selection(selection_id)
            if not selection:
                return False
            
            # Remove documents
            current_ids = set(selection.get("document_ids", []))
            current_ids.difference_update(document_ids)
            
            # Update selection
            return self.update_selection(selection_id, {"document_ids": list(current_ids)})
            
        except Exception as e:
            logger.error(f"Error removing documents from selection: {str(e)}")
            return False
    
    def export_selection(self, selection_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a document selection for sharing.
        
        Args:
            selection_id: Selection ID
            
        Returns:
            Exportable selection data if successful, None otherwise
        """
        try:
            # Get selection
            selection = self.get_selection(selection_id)
            if not selection:
                return None
            
            # Get document processor
            from app.core.document_processor import DocumentProcessor
            doc_processor = DocumentProcessor()
            
            # Get document metadata
            document_metadata = []
            for doc_id in selection.get("document_ids", []):
                doc = doc_processor.get_document(doc_id)
                if doc:
                    document_metadata.append({
                        "id": doc_id,
                        "title": doc.get("title", ""),
                        "file_type": doc.get("file_type", ""),
                        "upload_time": doc.get("upload_time", ""),
                        "page_count": doc.get("page_count", 0)
                    })
            
            # Create export data
            export_data = {
                "selection_id": selection.get("id", selection_id),
                "name": selection.get("name", "Unnamed Selection"),
                "description": selection.get("description", ""),
                "document_count": len(selection.get("document_ids", [])),
                "documents": document_metadata,
                "exported_at": self._get_timestamp()
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting selection: {str(e)}")
            return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
