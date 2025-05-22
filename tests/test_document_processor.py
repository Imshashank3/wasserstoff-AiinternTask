"""
Unit tests for document processor functionality.
"""
import os
import sys
import unittest
import json
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.document_processor import DocumentProcessor
from backend.app import config

class TestDocumentProcessor(unittest.TestCase):
    """Test cases for DocumentProcessor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directories
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        self.test_upload_dir = os.path.join(self.test_data_dir, 'uploads')
        self.test_processed_dir = os.path.join(self.test_data_dir, 'processed')
        
        os.makedirs(self.test_data_dir, exist_ok=True)
        os.makedirs(self.test_upload_dir, exist_ok=True)
        os.makedirs(self.test_processed_dir, exist_ok=True)
        
        # Mock config
        self.original_upload_dir = config.UPLOAD_DIR
        self.original_processed_dir = config.PROCESSED_DIR
        config.UPLOAD_DIR = self.test_upload_dir
        config.PROCESSED_DIR = self.test_processed_dir
        
        # Create test document processor
        self.doc_processor = DocumentProcessor()
        self.doc_processor.metadata_file = os.path.join(self.test_data_dir, 'test_metadata.json')
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original config
        config.UPLOAD_DIR = self.original_upload_dir
        config.PROCESSED_DIR = self.original_processed_dir
        
        # Remove test directories
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def test_init(self):
        """Test initialization of DocumentProcessor."""
        self.assertTrue(os.path.exists(self.test_upload_dir))
        self.assertTrue(os.path.exists(self.test_processed_dir))
        self.assertEqual(self.doc_processor.metadata_file, os.path.join(self.test_data_dir, 'test_metadata.json'))
        self.assertIsInstance(self.doc_processor.documents, dict)
    
    def test_save_load_documents(self):
        """Test saving and loading document metadata."""
        # Add test document
        test_doc = {
            "id": "test123",
            "title": "Test Document",
            "file_path": "/path/to/test.pdf",
            "status": "uploaded"
        }
        self.doc_processor.documents["test123"] = test_doc
        
        # Save documents
        self.doc_processor._save_documents()
        
        # Create new processor to test loading
        new_processor = DocumentProcessor()
        new_processor.metadata_file = self.doc_processor.metadata_file
        new_processor._load_documents()
        
        # Check if document was loaded
        self.assertIn("test123", new_processor.documents)
        self.assertEqual(new_processor.documents["test123"]["title"], "Test Document")
    
    @patch('subprocess.run')
    def test_process_pdf(self, mock_run):
        """Test PDF processing."""
        # Mock subprocess calls
        mock_run.return_value.stdout = "Title: Test\nPages: 5\nAuthor: Test Author"
        
        # Create test document
        doc_id = "pdf123"
        test_doc = {
            "id": doc_id,
            "title": "Test PDF",
            "file_path": os.path.join(self.test_upload_dir, "test.pdf"),
            "file_type": "pdf",
            "status": "uploaded"
        }
        
        # Create test PDF file
        with open(test_doc["file_path"], 'w') as f:
            f.write("Test PDF content")
        
        # Create processed directory
        processed_dir = os.path.join(self.test_processed_dir, doc_id)
        os.makedirs(processed_dir, exist_ok=True)
        
        # Mock _process_pdf method
        with patch.object(self.doc_processor, '_process_pdf') as mock_process_pdf:
            mock_process_pdf.return_value = ("Test PDF content extracted", 5)
            
            # Process document
            result = self.doc_processor.process_document(test_doc)
            
            # Check result
            self.assertTrue(result)
            self.assertEqual(test_doc["status"], "processed")
            self.assertEqual(test_doc["page_count"], 5)
            self.assertIn("processed_time", test_doc)
            
            # Check if text file was created
            text_file = os.path.join(processed_dir, "extracted_text.txt")
            self.assertTrue(os.path.exists(text_file))
            
            # Check if document was saved
            self.assertIn(doc_id, self.doc_processor.documents)
    
    @patch('pytesseract.image_to_string')
    def test_process_image(self, mock_ocr):
        """Test image processing with OCR."""
        # Mock OCR
        mock_ocr.return_value = "Test OCR result"
        
        # Create test document
        doc_id = "img123"
        test_doc = {
            "id": doc_id,
            "title": "Test Image",
            "file_path": os.path.join(self.test_upload_dir, "test.jpg"),
            "file_type": "jpg",
            "status": "uploaded"
        }
        
        # Create test image file
        with open(test_doc["file_path"], 'w') as f:
            f.write("Test image content")
        
        # Create processed directory
        processed_dir = os.path.join(self.test_processed_dir, doc_id)
        os.makedirs(processed_dir, exist_ok=True)
        
        # Mock _process_image method
        with patch.object(self.doc_processor, '_process_image') as mock_process_image:
            mock_process_image.return_value = ("Test OCR result", 1)
            
            # Process document
            result = self.doc_processor.process_document(test_doc)
            
            # Check result
            self.assertTrue(result)
            self.assertEqual(test_doc["status"], "processed")
            self.assertEqual(test_doc["page_count"], 1)
            
            # Check if text file was created
            text_file = os.path.join(processed_dir, "extracted_text.txt")
            self.assertTrue(os.path.exists(text_file))
    
    def test_list_documents(self):
        """Test listing documents with filtering."""
        # Add test documents
        self.doc_processor.documents = {
            "doc1": {"id": "doc1", "status": "processed", "tags": ["test", "pdf"]},
            "doc2": {"id": "doc2", "status": "processing", "tags": ["test"]},
            "doc3": {"id": "doc3", "status": "error", "tags": ["image"]}
        }
        
        # Test without filters
        docs = self.doc_processor.list_documents()
        self.assertEqual(len(docs), 3)
        
        # Test with status filter
        docs = self.doc_processor.list_documents(status="processed")
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["id"], "doc1")
        
        # Test with tag filter
        docs = self.doc_processor.list_documents(tag="test")
        self.assertEqual(len(docs), 2)
        
        # Test with pagination
        docs = self.doc_processor.list_documents(skip=1, limit=1)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["id"], "doc2")
    
    def test_get_document(self):
        """Test getting a document by ID."""
        # Add test document
        self.doc_processor.documents = {
            "doc1": {"id": "doc1", "title": "Test Document"}
        }
        
        # Test getting existing document
        doc = self.doc_processor.get_document("doc1")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["title"], "Test Document")
        
        # Test getting non-existent document
        doc = self.doc_processor.get_document("nonexistent")
        self.assertIsNone(doc)
    
    def test_delete_document(self):
        """Test deleting a document."""
        # Add test document
        doc_id = "delete123"
        test_doc = {
            "id": doc_id,
            "title": "Delete Test",
            "file_path": os.path.join(self.test_upload_dir, "delete_test.pdf"),
            "processed_path": os.path.join(self.test_processed_dir, doc_id)
        }
        self.doc_processor.documents[doc_id] = test_doc
        
        # Create test files
        os.makedirs(test_doc["processed_path"], exist_ok=True)
        with open(test_doc["file_path"], 'w') as f:
            f.write("Test content")
        
        # Delete document
        result = self.doc_processor.delete_document(doc_id)
        
        # Check result
        self.assertTrue(result)
        self.assertNotIn(doc_id, self.doc_processor.documents)
        self.assertFalse(os.path.exists(test_doc["file_path"]))
        self.assertFalse(os.path.exists(test_doc["processed_path"]))
        
        # Test deleting non-existent document
        result = self.doc_processor.delete_document("nonexistent")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
