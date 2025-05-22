"""
Visual citation mapping service for creating interactive visualizations.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

from app import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualCitationService:
    """
    Service for visual citation mapping, providing:
    - Interactive visualization of document citations
    - Visual mapping between themes and source documents
    - Citation network visualization
    """
    
    def __init__(self):
        """Initialize the visual citation service."""
        # Path to visualization data storage
        self.visualization_dir = os.path.join(config.DATA_DIR, "visualizations")
        os.makedirs(self.visualization_dir, exist_ok=True)
    
    def create_document_citation_map(self, document_id: str) -> Dict[str, Any]:
        """
        Create visual citation map for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Visualization data dictionary
        """
        try:
            # Get enhanced citation service
            from app.services.enhanced_citation import EnhancedCitationService
            citation_service = EnhancedCitationService()
            
            # Get document structure
            document_structure = citation_service.get_document_structure(document_id)
            
            # Create visualization data
            visualization = {
                "type": "document_citation_map",
                "document_id": document_id,
                "document_title": document_structure.get("document_title", "Unknown"),
                "created_at": self._get_timestamp(),
                "structure": document_structure.get("structure", []),
                "visualization_data": {
                    "nodes": [],
                    "links": []
                }
            }
            
            # Create nodes for document structure
            node_id = 0
            node_map = {}  # Map structure IDs to node IDs
            
            # Document node
            visualization["visualization_data"]["nodes"].append({
                "id": node_id,
                "name": document_structure.get("document_title", "Unknown"),
                "type": "document",
                "level": 0
            })
            node_map["document"] = node_id
            node_id += 1
            
            # Page nodes
            for page in document_structure.get("structure", []):
                visualization["visualization_data"]["nodes"].append({
                    "id": node_id,
                    "name": f"Page {page.get('number', 0)}",
                    "type": "page",
                    "level": 1
                })
                node_map[page.get("id")] = node_id
                
                # Link to document
                visualization["visualization_data"]["links"].append({
                    "source": node_map["document"],
                    "target": node_id,
                    "value": 1
                })
                
                node_id += 1
                
                # Paragraph nodes
                for paragraph in page.get("paragraphs", []):
                    # Truncate paragraph text for visualization
                    p_text = paragraph.get("text", "")
                    if len(p_text) > 50:
                        p_text = p_text[:47] + "..."
                    
                    visualization["visualization_data"]["nodes"].append({
                        "id": node_id,
                        "name": f"Para {paragraph.get('index', 0) + 1}",
                        "type": "paragraph",
                        "level": 2,
                        "text": p_text
                    })
                    node_map[paragraph.get("id")] = node_id
                    
                    # Link to page
                    visualization["visualization_data"]["links"].append({
                        "source": node_map[page.get("id")],
                        "target": node_id,
                        "value": 1
                    })
                    
                    node_id += 1
            
            # Save visualization data
            vis_file = os.path.join(self.visualization_dir, f"doc_citation_map_{document_id}.json")
            with open(vis_file, 'w') as f:
                json.dump(visualization, f, indent=2)
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error creating document citation map: {str(e)}")
            return {
                "type": "document_citation_map",
                "document_id": document_id,
                "error": str(e)
            }
    
    def create_theme_citation_map(self, theme_id: str) -> Dict[str, Any]:
        """
        Create visual citation map for a theme.
        
        Args:
            theme_id: Theme ID
            
        Returns:
            Visualization data dictionary
        """
        try:
            # Get theme processor
            from app.core.theme_processor import ThemeProcessor
            theme_processor = ThemeProcessor()
            
            # Get theme data
            theme_response = theme_processor.get_theme(theme_id)
            if not theme_response or not theme_response.themes:
                raise ValueError(f"Theme {theme_id} not found")
            
            theme = theme_response.themes[0]
            
            # Create visualization data
            visualization = {
                "type": "theme_citation_map",
                "theme_id": theme_id,
                "theme_name": theme.name,
                "theme_description": theme.description,
                "created_at": self._get_timestamp(),
                "visualization_data": {
                    "nodes": [],
                    "links": []
                }
            }
            
            # Create nodes for theme and documents
            node_id = 0
            node_map = {}  # Map IDs to node IDs
            
            # Theme node
            visualization["visualization_data"]["nodes"].append({
                "id": node_id,
                "name": theme.name,
                "type": "theme",
                "level": 0,
                "description": theme.description
            })
            node_map["theme"] = node_id
            node_id += 1
            
            # Document nodes
            doc_nodes = {}
            for citation in theme.citations:
                doc_id = citation.document_id
                
                # Skip if document already added
                if doc_id in doc_nodes:
                    continue
                
                # Add document node
                visualization["visualization_data"]["nodes"].append({
                    "id": node_id,
                    "name": citation.document_title,
                    "type": "document",
                    "level": 1,
                    "document_id": doc_id
                })
                doc_nodes[doc_id] = node_id
                
                # Link to theme
                visualization["visualization_data"]["links"].append({
                    "source": node_map["theme"],
                    "target": node_id,
                    "value": 2
                })
                
                node_id += 1
            
            # Citation nodes
            for citation in theme.citations:
                doc_id = citation.document_id
                
                # Add citation node
                visualization["visualization_data"]["nodes"].append({
                    "id": node_id,
                    "name": citation.citation,
                    "type": "citation",
                    "level": 2,
                    "document_id": doc_id,
                    "relevance": citation.relevance_score
                })
                
                # Link to document
                visualization["visualization_data"]["links"].append({
                    "source": doc_nodes[doc_id],
                    "target": node_id,
                    "value": 1
                })
                
                node_id += 1
            
            # Save visualization data
            vis_file = os.path.join(self.visualization_dir, f"theme_citation_map_{theme_id}.json")
            with open(vis_file, 'w') as f:
                json.dump(visualization, f, indent=2)
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error creating theme citation map: {str(e)}")
            return {
                "type": "theme_citation_map",
                "theme_id": theme_id,
                "error": str(e)
            }
    
    def create_cross_document_map(self, document_ids: List[str], query: Optional[str] = None) -> Dict[str, Any]:
        """
        Create visual map of relationships between documents.
        
        Args:
            document_ids: List of document IDs
            query: Optional query to focus the map
            
        Returns:
            Visualization data dictionary
        """
        try:
            # Get document processor
            from app.core.document_processor import DocumentProcessor
            doc_processor = DocumentProcessor()
            
            # Get vector database service
            from app.core.vector_database import VectorDatabaseService
            vector_db = VectorDatabaseService()
            
            # Create visualization data
            visualization = {
                "type": "cross_document_map",
                "document_count": len(document_ids),
                "query": query,
                "created_at": self._get_timestamp(),
                "visualization_data": {
                    "nodes": [],
                    "links": []
                }
            }
            
            # Create nodes for documents
            node_id = 0
            node_map = {}  # Map document IDs to node IDs
            
            for doc_id in document_ids:
                # Get document metadata
                doc_metadata = doc_processor.get_document(doc_id)
                if not doc_metadata:
                    continue
                
                # Add document node
                visualization["visualization_data"]["nodes"].append({
                    "id": node_id,
                    "name": doc_metadata.get("title", f"Document {doc_id}"),
                    "type": "document",
                    "document_id": doc_id
                })
                node_map[doc_id] = node_id
                node_id += 1
            
            # If query provided, add connections based on query results
            if query:
                # Search for query
                search_results = vector_db.search(
                    query=query,
                    document_ids=document_ids,
                    max_results=50
                )
                
                # Group results by document
                doc_results = {}
                for result in search_results:
                    doc_id = result["document_id"]
                    if doc_id not in doc_results:
                        doc_results[doc_id] = []
                    doc_results[doc_id].append(result)
                
                # Add query node
                visualization["visualization_data"]["nodes"].append({
                    "id": node_id,
                    "name": query,
                    "type": "query"
                })
                query_node_id = node_id
                node_id += 1
                
                # Link documents to query
                for doc_id, results in doc_results.items():
                    if doc_id in node_map:
                        # Calculate strength based on relevance scores
                        strength = sum(r["relevance_score"] for r in results) / len(results)
                        
                        visualization["visualization_data"]["links"].append({
                            "source": query_node_id,
                            "target": node_map[doc_id],
                            "value": int(strength * 5) + 1  # Scale to 1-6
                        })
            
            # Add connections between documents based on similarity
            # This is a simplified approach; more sophisticated methods could be used
            for i, doc_id1 in enumerate(document_ids):
                for doc_id2 in document_ids[i+1:]:
                    # Skip if either document not in node map
                    if doc_id1 not in node_map or doc_id2 not in node_map:
                        continue
                    
                    # Calculate similarity between documents
                    # This is a placeholder; actual implementation would depend on available data
                    similarity = 0.5  # Default medium similarity
                    
                    # Add link if similarity above threshold
                    if similarity > 0.2:
                        visualization["visualization_data"]["links"].append({
                            "source": node_map[doc_id1],
                            "target": node_map[doc_id2],
                            "value": int(similarity * 5) + 1  # Scale to 1-6
                        })
            
            # Save visualization data
            map_id = "_".join(document_ids[:3])
            if len(document_ids) > 3:
                map_id += f"_plus_{len(document_ids) - 3}"
            
            vis_file = os.path.join(self.visualization_dir, f"cross_doc_map_{map_id}.json")
            with open(vis_file, 'w') as f:
                json.dump(visualization, f, indent=2)
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error creating cross-document map: {str(e)}")
            return {
                "type": "cross_document_map",
                "document_ids": document_ids,
                "error": str(e)
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
