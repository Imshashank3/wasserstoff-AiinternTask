"""
Unit tests for theme processor functionality.
"""
import os
import sys
import unittest
import json
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.theme_processor import ThemeProcessor
from backend.app import config

class TestThemeProcessor(unittest.TestCase):
    """Test cases for ThemeProcessor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directories
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Mock vector database service
        self.mock_vector_db = MagicMock()
        
        # Create test theme processor with mock
        with patch('backend.app.core.theme_processor.VectorDatabaseService', return_value=self.mock_vector_db):
            self.theme_processor = ThemeProcessor()
            self.theme_processor.themes_file = os.path.join(self.test_data_dir, 'test_themes.json')
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directories
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def test_init(self):
        """Test initialization of ThemeProcessor."""
        self.assertEqual(self.theme_processor.themes_file, os.path.join(self.test_data_dir, 'test_themes.json'))
        self.assertIsInstance(self.theme_processor.themes, dict)
    
    def test_save_load_themes(self):
        """Test saving and loading themes."""
        # Add test theme
        self.theme_processor.themes = {
            "theme1": {
                "id": "theme1",
                "name": "Test Theme",
                "description": "Theme description",
                "document_count": 3,
                "document_ids": ["doc1", "doc2", "doc3"],
                "citations": []
            }
        }
        
        # Save themes
        self.theme_processor._save_themes()
        
        # Create new processor to test loading
        with patch('backend.app.core.theme_processor.VectorDatabaseService', return_value=self.mock_vector_db):
            new_processor = ThemeProcessor()
            new_processor.themes_file = self.theme_processor.themes_file
            new_processor._load_themes()
        
        # Check if theme was loaded
        self.assertIn("theme1", new_processor.themes)
        self.assertEqual(new_processor.themes["theme1"]["name"], "Test Theme")
        self.assertEqual(new_processor.themes["theme1"]["document_count"], 3)
    
    @patch('backend.app.core.theme_processor.DBSCAN')
    @patch('backend.app.core.theme_processor.cosine_similarity')
    def test_identify_themes(self, mock_cosine_similarity, mock_dbscan):
        """Test theme identification."""
        # Mock document embeddings
        doc1_embeddings = [("chunk1", [0.1, 0.2]), ("chunk2", [0.3, 0.4])]
        doc2_embeddings = [("chunk3", [0.1, 0.2]), ("chunk4", [0.5, 0.6])]
        doc3_embeddings = [("chunk5", [0.7, 0.8])]
        
        self.mock_vector_db.get_document_embeddings.side_effect = lambda doc_id: {
            "doc1": doc1_embeddings,
            "doc2": doc2_embeddings,
            "doc3": doc3_embeddings
        }.get(doc_id, [])
        
        # Mock document processor
        with patch('backend.app.core.theme_processor.DocumentProcessor') as mock_doc_processor_class:
            mock_doc_processor = MagicMock()
            mock_doc_processor.get_document.side_effect = lambda doc_id: {
                "doc1": {"id": "doc1", "title": "Document 1"},
                "doc2": {"id": "doc2", "title": "Document 2"},
                "doc3": {"id": "doc3", "title": "Document 3"}
            }.get(doc_id)
            mock_doc_processor_class.return_value = mock_doc_processor
            
            # Mock clustering
            mock_clustering = MagicMock()
            mock_clustering.labels_ = [0, 0, 1, 1, -1]  # Two clusters, one noise point
            mock_dbscan.return_value.fit.return_value = mock_clustering
            
            # Mock cosine similarity
            mock_cosine_similarity.return_value = [
                [1.0, 0.8, 0.3, 0.2, 0.1],
                [0.8, 1.0, 0.2, 0.3, 0.1],
                [0.3, 0.2, 1.0, 0.9, 0.2],
                [0.2, 0.3, 0.9, 1.0, 0.2],
                [0.1, 0.1, 0.2, 0.2, 1.0]
            ]
            
            # Mock vector database get
            self.mock_vector_db.vector_db.get.side_effect = lambda filter: {
                "documents": ["Chunk content about climate"],
                "metadatas": [{"page": 1}]
            } if filter.get("chunk_id") in ["chunk1", "chunk2", "chunk3", "chunk4", "chunk5"] else {"documents": [], "metadatas": []}
            
            # Identify themes
            response = self.theme_processor.identify_themes(
                document_ids=["doc1", "doc2", "doc3"],
                min_documents=2,
                similarity_threshold=0.7
            )
        
        # Check response
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.themes)
        self.assertEqual(len(response.themes), 2)  # Two themes identified
        self.assertIsNotNone(response.synthesized_response)
        
        # Check if get_document_embeddings was called for each document
        self.assertEqual(self.mock_vector_db.get_document_embeddings.call_count, 3)
        
        # Check if themes were saved
        self.assertEqual(len(self.theme_processor.themes), 2)
    
    def test_list_themes(self):
        """Test listing themes."""
        # Add test themes
        self.theme_processor.themes = {
            "theme1": {
                "id": "theme1",
                "name": "Theme 1",
                "description": "Description 1",
                "document_count": 2,
                "citations": [
                    {"document_id": "doc1", "document_title": "Document 1", "citation": "Page 1", "relevance_score": 0.9}
                ]
            },
            "theme2": {
                "id": "theme2",
                "name": "Theme 2",
                "description": "Description 2",
                "document_count": 3,
                "citations": []
            }
        }
        
        # List themes
        themes = self.theme_processor.list_themes()
        
        # Check result
        self.assertEqual(len(themes), 2)
        self.assertEqual(themes[0].themes[0].name, "Theme 1")
        self.assertEqual(themes[0].themes[0].document_count, 2)
        self.assertEqual(len(themes[0].themes[0].citations), 1)
        self.assertEqual(themes[1].themes[0].name, "Theme 2")
    
    def test_get_theme(self):
        """Test getting a theme by ID."""
        # Add test theme
        theme_id = "theme123"
        self.theme_processor.themes = {
            theme_id: {
                "id": theme_id,
                "name": "Test Theme",
                "description": "Theme description",
                "document_count": 2,
                "citations": [
                    {"document_id": "doc1", "document_title": "Document 1", "citation": "Page 1", "relevance_score": 0.9}
                ]
            }
        }
        
        # Get theme
        theme_response = self.theme_processor.get_theme(theme_id)
        
        # Check result
        self.assertIsNotNone(theme_response)
        self.assertEqual(len(theme_response.themes), 1)
        self.assertEqual(theme_response.themes[0].id, theme_id)
        self.assertEqual(theme_response.themes[0].name, "Test Theme")
        self.assertEqual(theme_response.themes[0].document_count, 2)
        self.assertEqual(len(theme_response.themes[0].citations), 1)
        
        # Test getting non-existent theme
        theme_response = self.theme_processor.get_theme("nonexistent")
        self.assertIsNone(theme_response)

if __name__ == '__main__':
    unittest.main()
