"""
Unit tests for vector database functionality.
"""
import os
import sys
import unittest
import json
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database import VectorDatabaseService
from backend.app import config

class TestVectorDatabase(unittest.TestCase):
    """Test cases for VectorDatabaseService class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directories
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.test_vector_db_dir = os.path.join(self.test_data_dir, 'vectordb')
        
        os.makedirs(self.test_data_dir, exist_ok=True)
        os.makedirs(self.test_vector_db_dir, exist_ok=True)
        
        # Mock config
        self.original_vector_db_dir = config.VECTOR_DB_DIR
        config.VECTOR_DB_DIR = self.test_vector_db_dir
        
        # Mock embedding model and vector database
        self.mock_embedding_model = MagicMock()
        self.mock_vector_db = MagicMock()
        
        # Create test vector database service with mocks
        with patch('langchain.embeddings.HuggingFaceEmbeddings', return_value=self.mock_embedding_model):
            with patch('langchain.vectorstores.Chroma', return_value=self.mock_vector_db):
                self.vector_db_service = VectorDatabaseService()
                self.vector_db_service.chunk_metadata_file = os.path.join(self.test_data_dir, 'test_chunk_metadata.json')
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original config
        config.VECTOR_DB_DIR = self.original_vector_db_dir
        
        # Remove test directories
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def test_init(self):
        """Test initialization of VectorDatabaseService."""
        self.assertTrue(os.path.exists(self.test_vector_db_dir))
        self.assertEqual(self.vector_db_service.vector_db_path, self.test_vector_db_dir)
        self.assertEqual(self.vector_db_service.chunk_metadata_file, os.path.join(self.test_data_dir, 'test_chunk_metadata.json'))
        self.assertIsInstance(self.vector_db_service.chunk_metadata, dict)
    
    def test_save_load_chunk_metadata(self):
        """Test saving and loading chunk metadata."""
        # Add test chunk metadata
        self.vector_db_service.chunk_metadata = {
            "doc1": ["chunk1", "chunk2", "chunk3"]
        }
        
        # Save metadata
        self.vector_db_service._save_chunk_metadata()
        
        # Create new service to test loading
        with patch('langchain.embeddings.HuggingFaceEmbeddings', return_value=self.mock_embedding_model):
            with patch('langchain.vectorstores.Chroma', return_value=self.mock_vector_db):
                new_service = VectorDatabaseService()
                new_service.chunk_metadata_file = self.vector_db_service.chunk_metadata_file
                new_service._load_chunk_metadata()
        
        # Check if metadata was loaded
        self.assertIn("doc1", new_service.chunk_metadata)
        self.assertEqual(len(new_service.chunk_metadata["doc1"]), 3)
        self.assertEqual(new_service.chunk_metadata["doc1"][0], "chunk1")
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Test document content")
    def test_add_document(self, mock_open):
        """Test adding a document to the vector database."""
        # Mock text splitter
        self.vector_db_service.text_splitter.split_text = MagicMock(return_value=[
            "Chunk 1 content",
            "Chunk 2 content",
            "Chunk 3 content"
        ])
        
        # Create test document
        doc_id = "doc123"
        test_doc = {
            "id": doc_id,
            "title": "Test Document",
            "file_path": "/path/to/test.pdf",
            "file_type": "pdf",
            "status": "processed",
            "processed_path": os.path.join(self.test_data_dir, "processed", doc_id),
            "page_count": 3
        }
        
        # Create processed directory and text file
        os.makedirs(test_doc["processed_path"], exist_ok=True)
        text_file = os.path.join(test_doc["processed_path"], "extracted_text.txt")
        
        # Add document to vector database
        result = self.vector_db_service.add_document(test_doc)
        
        # Check result
        self.assertTrue(result)
        self.assertIn(doc_id, self.vector_db_service.chunk_metadata)
        self.assertEqual(len(self.vector_db_service.chunk_metadata[doc_id]), 3)
        
        # Check if add_documents was called on vector database
        self.vector_db_service.vector_db.add_documents.assert_called_once()
        
        # Check if persist was called on vector database
        self.vector_db_service.vector_db.persist.assert_called_once()
    
    def test_search(self):
        """Test searching for documents in the vector database."""
        # Mock similarity_search_with_score
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Result 1 content"
        mock_doc1.metadata = {
            "document_id": "doc1",
            "document_title": "Document 1",
            "chunk_id": "chunk1",
            "page": 1
        }
        
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Result 2 content"
        mock_doc2.metadata = {
            "document_id": "doc2",
            "document_title": "Document 2",
            "chunk_id": "chunk2",
            "page": 2
        }
        
        self.vector_db_service.vector_db.similarity_search_with_score.return_value = [
            (mock_doc1, 0.2),
            (mock_doc2, 0.5)
        ]
        
        # Search for documents
        results = self.vector_db_service.search("test query", max_results=2)
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["document_id"], "doc1")
        self.assertEqual(results[0]["document_title"], "Document 1")
        self.assertEqual(results[0]["extracted_answer"], "Result 1 content")
        self.assertEqual(results[0]["citation"], "Page 1")
        self.assertAlmostEqual(results[0]["relevance_score"], 0.8, places=1)
        
        # Check if similarity_search_with_score was called correctly
        self.vector_db_service.vector_db.similarity_search_with_score.assert_called_once_with(
            query="test query",
            k=2,
            filter=None
        )
    
    def test_search_with_filter(self):
        """Test searching with document filter."""
        # Mock similarity_search_with_score
        mock_doc = MagicMock()
        mock_doc.page_content = "Result content"
        mock_doc.metadata = {
            "document_id": "doc1",
            "document_title": "Document 1",
            "chunk_id": "chunk1",
            "page": 1
        }
        
        self.vector_db_service.vector_db.similarity_search_with_score.return_value = [
            (mock_doc, 0.2)
        ]
        
        # Search for documents with filter
        results = self.vector_db_service.search("test query", document_ids=["doc1", "doc2"])
        
        # Check if similarity_search_with_score was called with filter
        self.vector_db_service.vector_db.similarity_search_with_score.assert_called_once_with(
            query="test query",
            k=10,
            filter={"document_id": {"$in": ["doc1", "doc2"]}}
        )
    
    def test_delete_document(self):
        """Test deleting a document from the vector database."""
        # Add test chunk metadata
        doc_id = "delete123"
        self.vector_db_service.chunk_metadata = {
            doc_id: ["chunk1", "chunk2", "chunk3"]
        }
        
        # Delete document
        result = self.vector_db_service.delete_document(doc_id)
        
        # Check result
        self.assertTrue(result)
        self.assertNotIn(doc_id, self.vector_db_service.chunk_metadata)
        
        # Check if delete was called on vector database
        self.assertEqual(self.vector_db_service.vector_db.delete.call_count, 3)
        
        # Check if persist was called on vector database
        self.vector_db_service.vector_db.persist.assert_called_once()
        
        # Test deleting non-existent document
        result = self.vector_db_service.delete_document("nonexistent")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
