"""
Unit tests for query processor functionality.
"""
import os
import sys
import unittest
import json
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.query_processor import QueryProcessor
from backend.app import config

class TestQueryProcessor(unittest.TestCase):
    """Test cases for QueryProcessor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directories
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Mock vector database service
        self.mock_vector_db = MagicMock()
        
        # Create test query processor with mock
        with patch('backend.app.core.query_processor.VectorDatabaseService', return_value=self.mock_vector_db):
            self.query_processor = QueryProcessor()
            self.query_processor.query_history_file = os.path.join(self.test_data_dir, 'test_query_history.json')
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directories
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def test_init(self):
        """Test initialization of QueryProcessor."""
        self.assertEqual(self.query_processor.query_history_file, os.path.join(self.test_data_dir, 'test_query_history.json'))
        self.assertIsInstance(self.query_processor.query_history, list)
    
    def test_save_load_query_history(self):
        """Test saving and loading query history."""
        # Add test query history
        self.query_processor.query_history = [
            {
                "id": "query1",
                "query": "Test query",
                "timestamp": "2025-05-16T14:00:00",
                "result_count": 3
            }
        ]
        
        # Save history
        self.query_processor._save_query_history()
        
        # Create new processor to test loading
        with patch('backend.app.core.query_processor.VectorDatabaseService', return_value=self.mock_vector_db):
            new_processor = QueryProcessor()
            new_processor.query_history_file = self.query_processor.query_history_file
            new_processor._load_query_history()
        
        # Check if history was loaded
        self.assertEqual(len(new_processor.query_history), 1)
        self.assertEqual(new_processor.query_history[0]["query"], "Test query")
    
    def test_process_query(self):
        """Test processing a query."""
        # Mock vector database search results
        self.mock_vector_db.search.return_value = [
            {
                "document_id": "doc1",
                "document_title": "Document 1",
                "extracted_answer": "Answer from document 1",
                "citation": "Page 1",
                "relevance_score": 0.9
            },
            {
                "document_id": "doc2",
                "document_title": "Document 2",
                "extracted_answer": "Answer from document 2",
                "citation": "Page 3",
                "relevance_score": 0.7
            }
        ]
        
        # Process query
        response = self.query_processor.process_query("test query", max_results=2)
        
        # Check response
        self.assertEqual(response.query, "test query")
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.results[0].document_id, "doc1")
        self.assertEqual(response.results[0].extracted_answer, "Answer from document 1")
        self.assertEqual(response.results[0].citation, "Page 1")
        self.assertEqual(response.results[0].relevance_score, 0.9)
        
        # Check if search was called correctly
        self.mock_vector_db.search.assert_called_once_with(
            query="test query",
            document_ids=None,
            max_results=2
        )
        
        # Check if query was added to history
        self.assertEqual(len(self.query_processor.query_history), 1)
        self.assertEqual(self.query_processor.query_history[0]["query"], "test query")
        self.assertEqual(self.query_processor.query_history[0]["result_count"], 2)
    
    def test_process_query_with_document_ids(self):
        """Test processing a query with specific document IDs."""
        # Mock vector database search results
        self.mock_vector_db.search.return_value = [
            {
                "document_id": "doc1",
                "document_title": "Document 1",
                "extracted_answer": "Answer from document 1",
                "citation": "Page 1",
                "relevance_score": 0.9
            }
        ]
        
        # Process query with document IDs
        response = self.query_processor.process_query("test query", document_ids=["doc1"])
        
        # Check if search was called with document IDs
        self.mock_vector_db.search.assert_called_once_with(
            query="test query",
            document_ids=["doc1"],
            max_results=10
        )
    
    @patch('backend.app.core.query_processor.DBSCAN')
    @patch('backend.app.core.query_processor.cosine_similarity')
    def test_identify_themes(self, mock_cosine_similarity, mock_dbscan):
        """Test theme identification."""
        # Mock vector database search results
        self.mock_vector_db.search.return_value = [
            {
                "document_id": "doc1",
                "document_title": "Document 1",
                "extracted_answer": "Answer about climate change",
                "citation": "Page 1",
                "relevance_score": 0.9
            },
            {
                "document_id": "doc2",
                "document_title": "Document 2",
                "extracted_answer": "Another answer about climate change",
                "citation": "Page 3",
                "relevance_score": 0.7
            },
            {
                "document_id": "doc3",
                "document_title": "Document 3",
                "extracted_answer": "Answer about renewable energy",
                "citation": "Page 2",
                "relevance_score": 0.8
            }
        ]
        
        # Mock clustering
        mock_clustering = MagicMock()
        mock_clustering.labels_ = [0, 0, 1]  # Two clusters
        mock_dbscan.return_value.fit.return_value = mock_clustering
        
        # Mock cosine similarity
        mock_cosine_similarity.return_value = [[1.0, 0.8, 0.3], [0.8, 1.0, 0.2], [0.3, 0.2, 1.0]]
        
        # Mock embedding model
        with patch('backend.app.core.query_processor.HuggingFaceEmbeddings') as mock_embeddings:
            mock_model = MagicMock()
            mock_model.embed_documents.return_value = [[0.1, 0.2], [0.1, 0.2], [0.3, 0.4]]
            mock_embeddings.return_value = mock_model
            
            # Identify themes
            response = self.query_processor.identify_themes("climate change")
        
        # Check response
        self.assertEqual(response.query, "climate change")
        self.assertEqual(len(response.results), 3)
        self.assertIsNotNone(response.themes)
        self.assertEqual(len(response.themes), 2)  # Two themes identified
        self.assertIsNotNone(response.synthesized_response)
        
        # Check if search was called correctly
        self.mock_vector_db.search.assert_called_once_with(
            query="climate change",
            document_ids=None,
            max_results=20
        )
        
        # Check if query was added to history
        self.assertEqual(len(self.query_processor.query_history), 1)
        self.assertEqual(self.query_processor.query_history[0]["query"], "climate change")
        self.assertEqual(self.query_processor.query_history[0]["result_count"], 3)
        self.assertEqual(self.query_processor.query_history[0]["theme_count"], 2)

if __name__ == '__main__':
    unittest.main()
