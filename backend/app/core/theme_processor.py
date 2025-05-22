"""
Theme processor for identifying common themes across documents.
"""
import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from app import config
from app.core.vector_database import VectorDatabaseService
from app.models.theme import ThemeResponse, Theme, ThemeCitation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThemeProcessor:
    """
    Handles theme identification, including:
    - Cross-document analysis
    - Theme clustering and identification
    - Citation mapping for themes
    """
    
    def __init__(self):
        """Initialize the theme processor."""
        self.vector_db = VectorDatabaseService()
        
        # Path to theme storage
        self.themes_file = os.path.join(config.DATA_DIR, "themes.json")
        self.themes = self._load_themes()
    
    def _load_themes(self) -> Dict[str, Dict[str, Any]]:
        """Load themes from storage."""
        if os.path.exists(self.themes_file):
            try:
                with open(self.themes_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading themes: {str(e)}")
                return {}
        return {}
    
    def _save_themes(self):
        """Save themes to storage."""
        try:
            with open(self.themes_file, 'w') as f:
                json.dump(self.themes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving themes: {str(e)}")
    
    def identify_themes(self, document_ids: Optional[List[str]] = None,
                       min_documents: int = 2,
                       similarity_threshold: float = 0.75) -> ThemeResponse:
        """
        Identify common themes across a set of documents.
        
        Args:
            document_ids: Optional list of document IDs to analyze
            min_documents: Minimum number of documents to form a theme
            similarity_threshold: Similarity threshold for theme grouping
            
        Returns:
            ThemeResponse object with identified themes
        """
        try:
            # Get document embeddings
            document_chunks = {}
            
            # If document_ids is provided, use only those documents
            if document_ids:
                for doc_id in document_ids:
                    embeddings = self.vector_db.get_document_embeddings(doc_id)
                    if embeddings:
                        document_chunks[doc_id] = embeddings
            else:
                # Otherwise, use all documents in the vector database
                # This is a simplified approach; in a real system, you might
                # need to handle pagination for large document collections
                from app.core.document_processor import DocumentProcessor
                doc_processor = DocumentProcessor()
                all_docs = doc_processor.list_documents()
                
                for doc in all_docs:
                    doc_id = doc["id"]
                    embeddings = self.vector_db.get_document_embeddings(doc_id)
                    if embeddings:
                        document_chunks[doc_id] = embeddings
            
            # Check if we have enough documents
            if len(document_chunks) < min_documents:
                logger.warning(f"Not enough documents for theme identification: {len(document_chunks)} < {min_documents}")
                return ThemeResponse(themes=[])
            
            # Prepare data for clustering
            all_chunks = []
            chunk_map = {}  # Map chunk index to (doc_id, chunk_id)
            
            for doc_id, chunks in document_chunks.items():
                for chunk_id, embedding in chunks:
                    chunk_index = len(all_chunks)
                    all_chunks.append(embedding)
                    chunk_map[chunk_index] = (doc_id, chunk_id)
            
            # Convert to numpy array
            embeddings_array = np.array(all_chunks)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings_array)
            
            # Use DBSCAN for clustering
            clustering = DBSCAN(
                eps=1.0 - similarity_threshold,
                min_samples=min_documents,
                metric='precomputed'
            ).fit(1.0 - similarity_matrix)  # Convert similarity to distance
            
            # Get cluster labels
            labels = clustering.labels_
            
            # Group chunks by cluster
            clusters = {}
            for i, label in enumerate(labels):
                if label != -1:  # Skip noise points
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(i)
            
            # Create themes from clusters
            theme_list = []
            
            for cluster_id, chunk_indices in clusters.items():
                # Get document IDs in this cluster
                doc_ids = set()
                chunk_ids = []
                
                for idx in chunk_indices:
                    doc_id, chunk_id = chunk_map[idx]
                    doc_ids.add(doc_id)
                    chunk_ids.append(chunk_id)
                
                # Only create theme if it spans multiple documents
                if len(doc_ids) >= min_documents:
                    # Get document metadata
                    from app.core.document_processor import DocumentProcessor
                    doc_processor = DocumentProcessor()
                    
                    # Get chunk content and create citations
                    citations = []
                    
                    for idx in chunk_indices:
                        doc_id, chunk_id = chunk_map[idx]
                        
                        # Get document metadata
                        doc_metadata = doc_processor.get_document(doc_id)
                        if not doc_metadata:
                            continue
                        
                        # Get chunk content
                        search_results = self.vector_db.vector_db.get(filter={"chunk_id": chunk_id})
                        if not search_results or not search_results["documents"]:
                            continue
                        
                        chunk_text = search_results["documents"][0]
                        chunk_metadata = search_results["metadatas"][0] if search_results["metadatas"] else {}
                        
                        # Create citation
                        citation = ThemeCitation(
                            document_id=doc_id,
                            document_title=doc_metadata.get("title", "Unknown"),
                            citation=f"Page {chunk_metadata.get('page', 1)}",
                            relevance_score=0.9  # Placeholder; could be calculated based on centrality
                        )
                        
                        # Add to citations if not already present
                        if not any(c.document_id == citation.document_id and 
                                  c.citation == citation.citation for c in citations):
                            citations.append(citation)
                    
                    # Create theme name and description
                    # This is a simplified approach; more sophisticated NLP could be used
                    theme_id = str(uuid.uuid4())
                    theme_name = f"Theme {cluster_id + 1}"
                    
                    # Get most common words/phrases for theme description
                    import re
                    from collections import Counter
                    import nltk
                    try:
                        nltk.data.find('tokenizers/punkt')
                    except LookupError:
                        nltk.download('punkt', quiet=True)
                        nltk.download('stopwords', quiet=True)
                    
                    from nltk.corpus import stopwords
                    from nltk.tokenize import word_tokenize
                    
                    # Get chunk text for all chunks in this cluster
                    chunk_texts = []
                    for idx in chunk_indices:
                        _, chunk_id = chunk_map[idx]
                        search_results = self.vector_db.vector_db.get(filter={"chunk_id": chunk_id})
                        if search_results and search_results["documents"]:
                            chunk_texts.append(search_results["documents"][0])
                    
                    # Combine all text in the cluster
                    all_text = " ".join(chunk_texts)
                    
                    # Tokenize and remove stopwords
                    stop_words = set(stopwords.words('english'))
                    word_tokens = word_tokenize(all_text.lower())
                    filtered_words = [w for w in word_tokens if w.isalnum() and w not in stop_words and len(w) > 3]
                    
                    # Get most common words
                    word_counts = Counter(filtered_words)
                    common_words = [word for word, count in word_counts.most_common(5)]
                    
                    # Create theme description
                    theme_description = f"Common topics: {', '.join(common_words)}"
                    
                    # Create theme
                    theme = Theme(
                        id=theme_id,
                        name=theme_name,
                        description=theme_description,
                        document_count=len(doc_ids),
                        citations=citations
                    )
                    
                    # Add to theme list
                    theme_list.append(theme)
                    
                    # Save theme
                    self.themes[theme_id] = {
                        "id": theme_id,
                        "name": theme_name,
                        "description": theme_description,
                        "document_count": len(doc_ids),
                        "document_ids": list(doc_ids),
                        "chunk_ids": chunk_ids,
                        "created_at": datetime.now().isoformat(),
                        "citations": [c.dict() for c in citations]
                    }
            
            # Save themes
            self._save_themes()
            
            # Create synthesized response
            synthesized_response = None
            if theme_list:
                synthesized_response = "# Identified Themes\n\n"
                
                for theme in theme_list:
                    synthesized_response += f"## {theme.name} - {theme.description}\n\n"
                    
                    # Group citations by document
                    doc_citations = {}
                    for citation in theme.citations:
                        doc_id = citation.document_id
                        if doc_id not in doc_citations:
                            doc_citations[doc_id] = []
                        doc_citations[doc_id].append(citation.citation)
                    
                    # Add document citations
                    doc_list = []
                    for doc_id, citations in doc_citations.items():
                        doc_title = next((c.document_title for c in theme.citations if c.document_id == doc_id), "Unknown")
                        citation_str = ", ".join(sorted(set(citations)))
                        doc_list.append(f"{doc_title} ({doc_id}): {citation_str}")
                    
                    synthesized_response += "Documents: " + "; ".join(doc_list) + "\n\n"
            
            # Create response
            response = ThemeResponse(
                themes=theme_list,
                synthesized_response=synthesized_response
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error identifying themes: {str(e)}")
            # Return empty response on error
            return ThemeResponse(themes=[])
    
    def list_themes(self) -> List[ThemeResponse]:
        """
        List all identified themes.
        
        Returns:
            List of ThemeResponse objects
        """
        try:
            theme_responses = []
            
            for theme_id, theme_data in self.themes.items():
                # Convert citations
                citations = []
                for citation_data in theme_data.get("citations", []):
                    citations.append(ThemeCitation(**citation_data))
                
                # Create theme
                theme = Theme(
                    id=theme_data["id"],
                    name=theme_data["name"],
                    description=theme_data["description"],
                    document_count=theme_data["document_count"],
                    citations=citations
                )
                
                # Create response
                response = ThemeResponse(
                    themes=[theme]
                )
                
                theme_responses.append(response)
            
            return theme_responses
            
        except Exception as e:
            logger.error(f"Error listing themes: {str(e)}")
            return []
    
    def get_theme(self, theme_id: str) -> Optional[ThemeResponse]:
        """
        Get details for a specific theme.
        
        Args:
            theme_id: Theme ID
            
        Returns:
            ThemeResponse object or None if not found
        """
        try:
            theme_data = self.themes.get(theme_id)
            if not theme_data:
                return None
            
            # Convert citations
            citations = []
            for citation_data in theme_data.get("citations", []):
                citations.append(ThemeCitation(**citation_data))
            
            # Create theme
            theme = Theme(
                id=theme_data["id"],
                name=theme_data["name"],
                description=theme_data["description"],
                document_count=theme_data["document_count"],
                citations=citations
            )
            
            # Create response
            response = ThemeResponse(
                themes=[theme]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting theme: {str(e)}")
            return None
