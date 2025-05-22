"""
Query processor for handling natural language queries and theme identification.
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
from app.models.query import QueryResponse, DocumentResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryProcessor:
    """
    Handles query processing, including:
    - Natural language query processing
    - Document-specific query execution
    - Result formatting with citations
    """
    
    def __init__(self):
        """Initialize the query processor."""
        self.vector_db = VectorDatabaseService()
        
        # Path to query history storage
        self.query_history_file = os.path.join(config.DATA_DIR, "query_history.json")
        self.query_history = self._load_query_history()
    
    def _load_query_history(self) -> List[Dict[str, Any]]:
        """Load query history from storage."""
        if os.path.exists(self.query_history_file):
            try:
                with open(self.query_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading query history: {str(e)}")
                return []
        return []
    
    def _save_query_history(self):
        """Save query history to storage."""
        try:
            with open(self.query_history_file, 'w') as f:
                json.dump(self.query_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving query history: {str(e)}")
    
    def process_query(self, query: str, document_ids: Optional[List[str]] = None, 
                     max_results: int = 10) -> QueryResponse:
        """
        Process a natural language query against the document collection.
        
        Args:
            query: Natural language query
            document_ids: Optional list of document IDs to search within
            max_results: Maximum number of results to return
            
        Returns:
            QueryResponse object with results
        """
        try:
            # Search vector database
            search_results = self.vector_db.search(
                query=query,
                document_ids=document_ids,
                max_results=max_results
            )
            
            # Format results
            document_results = []
            for result in search_results:
                document_results.append(
                    DocumentResult(
                        document_id=result["document_id"],
                        document_title=result["document_title"],
                        extracted_answer=result["extracted_answer"],
                        citation=result["citation"],
                        relevance_score=result["relevance_score"]
                    )
                )
            
            # Create response
            response = QueryResponse(
                query=query,
                results=document_results
            )
            
            # Save to query history
            query_record = {
                "id": str(uuid.uuid4()),
                "query": query,
                "document_ids": document_ids,
                "timestamp": datetime.now().isoformat(),
                "result_count": len(document_results)
            }
            self.query_history.append(query_record)
            self._save_query_history()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            # Return empty response on error
            return QueryResponse(
                query=query,
                results=[]
            )
    
    def identify_themes(self, query: str, document_ids: Optional[List[str]] = None, 
                       max_results: int = 20) -> QueryResponse:
        """
        Process a query and identify themes across document responses.
        
        Args:
            query: Natural language query
            document_ids: Optional list of document IDs to search within
            max_results: Maximum number of results to consider for theme identification
            
        Returns:
            QueryResponse object with results and identified themes
        """
        try:
            # First, get document results
            search_results = self.vector_db.search(
                query=query,
                document_ids=document_ids,
                max_results=max_results
            )
            
            # Format document results
            document_results = []
            for result in search_results:
                document_results.append(
                    DocumentResult(
                        document_id=result["document_id"],
                        document_title=result["document_title"],
                        extracted_answer=result["extracted_answer"],
                        citation=result["citation"],
                        relevance_score=result["relevance_score"]
                    )
                )
            
            # Identify themes if we have enough results
            themes = []
            synthesized_response = ""
            
            if len(search_results) >= config.MIN_THEME_DOCUMENTS:
                # Get embeddings for all results
                from langchain.embeddings import HuggingFaceEmbeddings
                embedding_model = HuggingFaceEmbeddings(
                    model_name=config.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                
                # Extract text content and embed
                texts = [result["extracted_answer"] for result in search_results]
                embeddings = embedding_model.embed_documents(texts)
                
                # Cluster embeddings to identify themes
                # Calculate similarity matrix
                similarity_matrix = cosine_similarity(embeddings)
                
                # Use DBSCAN for clustering
                clustering = DBSCAN(
                    eps=1.0 - config.THEME_SIMILARITY_THRESHOLD,
                    min_samples=config.MIN_THEME_DOCUMENTS,
                    metric='precomputed'
                ).fit(1.0 - similarity_matrix)  # Convert similarity to distance
                
                # Get cluster labels
                labels = clustering.labels_
                
                # Group results by cluster
                clusters = {}
                for i, label in enumerate(labels):
                    if label != -1:  # Skip noise points
                        if label not in clusters:
                            clusters[label] = []
                        clusters[label].append(i)
                
                # Create themes from clusters
                for cluster_id, result_indices in clusters.items():
                    # Get documents in this cluster
                    cluster_results = [search_results[i] for i in result_indices]
                    
                    # Extract document IDs and titles
                    doc_ids = list(set([r["document_id"] for r in cluster_results]))
                    doc_titles = list(set([r["document_title"] for r in cluster_results]))
                    
                    # Create theme name and description
                    # This is a simplified approach; more sophisticated NLP could be used
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
                    
                    # Combine all text in the cluster
                    all_text = " ".join([r["extracted_answer"] for r in cluster_results])
                    
                    # Tokenize and remove stopwords
                    stop_words = set(stopwords.words('english'))
                    word_tokens = word_tokenize(all_text.lower())
                    filtered_words = [w for w in word_tokens if w.isalnum() and w not in stop_words and len(w) > 3]
                    
                    # Get most common words
                    word_counts = Counter(filtered_words)
                    common_words = [word for word, count in word_counts.most_common(5)]
                    
                    # Create theme description
                    theme_description = f"Common topics: {', '.join(common_words)}"
                    
                    # Create citations
                    citations = []
                    for result in cluster_results:
                        citations.append({
                            "document_id": result["document_id"],
                            "document_title": result["document_title"],
                            "citation": result["citation"],
                            "relevance_score": result["relevance_score"]
                        })
                    
                    # Add theme
                    themes.append({
                        "id": f"theme_{cluster_id}",
                        "name": theme_name,
                        "description": theme_description,
                        "document_count": len(doc_ids),
                        "citations": citations
                    })
                
                # Create synthesized response
                if themes:
                    synthesized_response = "# Synthesized Response\n\n"
                    
                    for theme in themes:
                        synthesized_response += f"## {theme['name']} - {theme['description']}\n\n"
                        
                        # Group citations by document
                        doc_citations = {}
                        for citation in theme["citations"]:
                            doc_id = citation["document_id"]
                            if doc_id not in doc_citations:
                                doc_citations[doc_id] = []
                            doc_citations[doc_id].append(citation["citation"])
                        
                        # Add document citations
                        doc_list = []
                        for doc_id, citations in doc_citations.items():
                            doc_title = next((c["document_title"] for c in theme["citations"] if c["document_id"] == doc_id), "Unknown")
                            citation_str = ", ".join(sorted(set(citations)))
                            doc_list.append(f"{doc_title} ({doc_id}): {citation_str}")
                        
                        synthesized_response += "Documents: " + "; ".join(doc_list) + "\n\n"
            
            # Create response
            response = QueryResponse(
                query=query,
                results=document_results,
                themes=themes,
                synthesized_response=synthesized_response
            )
            
            # Save to query history
            query_record = {
                "id": str(uuid.uuid4()),
                "query": query,
                "document_ids": document_ids,
                "timestamp": datetime.now().isoformat(),
                "result_count": len(document_results),
                "theme_count": len(themes)
            }
            self.query_history.append(query_record)
            self._save_query_history()
            
            return response
            
        except Exception as e:
            logger.error(f"Error identifying themes: {str(e)}")
            # Return basic response on error
            return QueryResponse(
                query=query,
                results=[]
            )
