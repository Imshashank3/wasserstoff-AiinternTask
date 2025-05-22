"""
Vector database service for document embeddings and semantic search.
"""
import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument

from app import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabaseService:
    """
    Service for managing document embeddings and semantic search using a vector database.
    
    Supports:
    - Document chunking and embedding
    - Semantic search across documents
    - Retrieval of relevant document sections with citations
    """
    
    def __init__(self):
        """Initialize the vector database service."""
        # Create embedding model
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize vector database
        self.vector_db_path = config.VECTOR_DB_DIR
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # Create or load vector database
        self.vector_db = Chroma(
            persist_directory=self.vector_db_path,
            embedding_function=self.embedding_model
        )
        
        # Text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Metadata file for tracking document chunks
        self.chunk_metadata_file = os.path.join(config.DATA_DIR, "chunk_metadata.json")
        self.chunk_metadata = self._load_chunk_metadata()
    
    def _load_chunk_metadata(self) -> Dict[str, List[str]]:
        """Load chunk metadata from storage."""
        if os.path.exists(self.chunk_metadata_file):
            try:
                with open(self.chunk_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading chunk metadata: {str(e)}")
                return {}
        return {}
    
    def _save_chunk_metadata(self):
        """Save chunk metadata to storage."""
        try:
            with open(self.chunk_metadata_file, 'w') as f:
                json.dump(self.chunk_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving chunk metadata: {str(e)}")
    
    def add_document(self, document: Dict[str, Any]) -> bool:
        """
        Add a document to the vector database.
        
        Args:
            document: Document metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_id = document["id"]
            
            # Check if document has been processed
            if document.get("status") != "processed" or "processed_path" not in document:
                logger.error(f"Document {doc_id} has not been processed yet")
                return False
            
            # Get extracted text file
            text_file = os.path.join(document["processed_path"], "extracted_text.txt")
            if not os.path.exists(text_file):
                logger.error(f"Extracted text file not found for document {doc_id}")
                return False
            
            # Read extracted text
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create Langchain documents with metadata
            langchain_docs = []
            chunk_ids = []
            
            for i, chunk_text in enumerate(chunks):
                # Determine page number and paragraph for citation
                # This is a simplified approach; more sophisticated parsing would be needed
                # for accurate page/paragraph tracking
                lines = chunk_text.split('\n')
                page_info = None
                for line in lines:
                    if line.startswith("--- Page "):
                        try:
                            page_info = int(line.replace("--- Page ", "").replace(" ---", ""))
                            break
                        except:
                            pass
                
                # If page info not found in chunk, estimate based on position
                if page_info is None and document.get("page_count"):
                    page_info = min(1 + (i * document["page_count"] // len(chunks)), document["page_count"])
                
                # Generate chunk ID
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                # Create document with metadata
                langchain_docs.append(
                    LangchainDocument(
                        page_content=chunk_text,
                        metadata={
                            "chunk_id": chunk_id,
                            "document_id": doc_id,
                            "document_title": document.get("title", ""),
                            "page": page_info or 1,
                            "chunk_index": i,
                            "source": document.get("original_filename", ""),
                            "file_type": document.get("file_type", ""),
                        }
                    )
                )
            
            # Add documents to vector database
            self.vector_db.add_documents(langchain_docs)
            
            # Persist vector database
            self.vector_db.persist()
            
            # Update chunk metadata
            self.chunk_metadata[doc_id] = chunk_ids
            self._save_chunk_metadata()
            
            logger.info(f"Document {doc_id} added to vector database with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to vector database: {str(e)}")
            return False
    
    def search(self, query: str, document_ids: Optional[List[str]] = None, 
              max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks based on a query.
        
        Args:
            query: Search query
            document_ids: Optional list of document IDs to search within
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with document metadata and citations
        """
        try:
            # Prepare filter based on document IDs
            filter_dict = None
            if document_ids:
                filter_dict = {"document_id": {"$in": document_ids}}
            
            # Perform similarity search
            results = self.vector_db.similarity_search_with_score(
                query=query,
                k=max_results,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                # Convert score to a 0-1 relevance score (lower distance = higher relevance)
                relevance_score = 1.0 - min(score, 1.0)
                
                # Format citation
                citation = f"Page {doc.metadata.get('page', 1)}"
                
                formatted_results.append({
                    "document_id": doc.metadata.get("document_id", ""),
                    "document_title": doc.metadata.get("document_title", ""),
                    "chunk_id": doc.metadata.get("chunk_id", ""),
                    "extracted_answer": doc.page_content,
                    "citation": citation,
                    "relevance_score": relevance_score,
                    "metadata": doc.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector database: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get chunk IDs for this document
            chunk_ids = self.chunk_metadata.get(document_id, [])
            if not chunk_ids:
                logger.warning(f"No chunks found for document {document_id}")
                return False
            
            # Delete chunks from vector database
            for chunk_id in chunk_ids:
                self.vector_db.delete(filter={"chunk_id": chunk_id})
            
            # Persist changes
            self.vector_db.persist()
            
            # Remove from chunk metadata
            if document_id in self.chunk_metadata:
                del self.chunk_metadata[document_id]
                self._save_chunk_metadata()
            
            logger.info(f"Document {document_id} deleted from vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document from vector database: {str(e)}")
            return False
    
    def get_document_embeddings(self, document_id: str) -> List[Tuple[str, List[float]]]:
        """
        Get embeddings for all chunks of a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of (chunk_id, embedding) tuples
        """
        try:
            # Get chunk IDs for this document
            chunk_ids = self.chunk_metadata.get(document_id, [])
            if not chunk_ids:
                logger.warning(f"No chunks found for document {document_id}")
                return []
            
            # Get embeddings for each chunk
            embeddings = []
            for chunk_id in chunk_ids:
                # Get document from vector database
                results = self.vector_db.get(filter={"chunk_id": chunk_id})
                if results and results["documents"]:
                    # Get embedding
                    embedding = results["embeddings"][0] if results["embeddings"] else None
                    if embedding:
                        embeddings.append((chunk_id, embedding))
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error getting document embeddings: {str(e)}")
            return []
