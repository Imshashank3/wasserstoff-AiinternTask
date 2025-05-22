"""
Enhanced citation service for paragraph and sentence level citations.
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

from app import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCitationService:
    """
    Service for enhanced citation granularity, providing:
    - Paragraph-level citations
    - Sentence-level citations
    - Citation mapping to original documents
    """
    
    def __init__(self):
        """Initialize the enhanced citation service."""
        # Path to citation metadata storage
        self.citation_metadata_file = os.path.join(config.DATA_DIR, "citation_metadata.json")
        self.citation_metadata = self._load_citation_metadata()
    
    def _load_citation_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load citation metadata from storage."""
        if os.path.exists(self.citation_metadata_file):
            try:
                with open(self.citation_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading citation metadata: {str(e)}")
                return {}
        return {}
    
    def _save_citation_metadata(self):
        """Save citation metadata to storage."""
        try:
            with open(self.citation_metadata_file, 'w') as f:
                json.dump(self.citation_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving citation metadata: {str(e)}")
    
    def process_document(self, document: Dict[str, Any]) -> bool:
        """
        Process a document for enhanced citation granularity.
        
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
            
            # Process text for enhanced citations
            paragraphs = self._split_into_paragraphs(text)
            
            # Create citation metadata
            citation_data = {
                "document_id": doc_id,
                "document_title": document.get("title", ""),
                "paragraph_count": len(paragraphs),
                "paragraphs": {}
            }
            
            # Process each paragraph
            for i, paragraph in enumerate(paragraphs):
                # Skip empty paragraphs
                if not paragraph.strip():
                    continue
                
                # Get page number if available
                page_num = self._extract_page_number(paragraph) or self._estimate_page_number(i, len(paragraphs), document.get("page_count", 1))
                
                # Split into sentences
                sentences = self._split_into_sentences(paragraph)
                
                # Create paragraph metadata
                paragraph_data = {
                    "index": i,
                    "page": page_num,
                    "text": paragraph,
                    "sentence_count": len(sentences),
                    "sentences": {}
                }
                
                # Process each sentence
                for j, sentence in enumerate(sentences):
                    # Skip empty sentences
                    if not sentence.strip():
                        continue
                    
                    # Create sentence metadata
                    paragraph_data["sentences"][str(j)] = {
                        "index": j,
                        "text": sentence
                    }
                
                # Add paragraph to citation data
                citation_data["paragraphs"][str(i)] = paragraph_data
            
            # Save citation metadata
            self.citation_metadata[doc_id] = citation_data
            self._save_citation_metadata()
            
            logger.info(f"Enhanced citations processed for document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document for enhanced citations: {str(e)}")
            return False
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Document text
            
        Returns:
            List of paragraphs
        """
        # Handle page markers
        text = re.sub(r'--- Page \d+ ---', lambda m: f"\n{m.group(0)}\n", text)
        
        # Split by double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_into_sentences(self, paragraph: str) -> List[str]:
        """
        Split paragraph into sentences.
        
        Args:
            paragraph: Paragraph text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting
        # This is a simplified approach; more sophisticated NLP could be used
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        # Filter out empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_page_number(self, text: str) -> Optional[int]:
        """
        Extract page number from text if present.
        
        Args:
            text: Text to extract from
            
        Returns:
            Page number or None if not found
        """
        # Look for page markers
        match = re.search(r'--- Page (\d+) ---', text)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        return None
    
    def _estimate_page_number(self, paragraph_index: int, total_paragraphs: int, total_pages: int) -> int:
        """
        Estimate page number based on paragraph position.
        
        Args:
            paragraph_index: Index of paragraph
            total_paragraphs: Total number of paragraphs
            total_pages: Total number of pages
            
        Returns:
            Estimated page number
        """
        # Simple estimation based on position
        if total_paragraphs <= 1:
            return 1
        
        page = 1 + (paragraph_index * total_pages // total_paragraphs)
        return min(page, total_pages)
    
    def get_citation(self, document_id: str, chunk_text: str, granularity: str = "paragraph") -> str:
        """
        Get citation for a text chunk at specified granularity.
        
        Args:
            document_id: Document ID
            chunk_text: Text chunk to find citation for
            granularity: Citation granularity ("document", "page", "paragraph", "sentence")
            
        Returns:
            Citation string
        """
        try:
            # Get citation metadata
            citation_data = self.citation_metadata.get(document_id)
            if not citation_data:
                # Fall back to document-level citation
                return f"Document {document_id}"
            
            # Document-level citation
            if granularity == "document":
                return f"Document: {citation_data.get('document_title', document_id)}"
            
            # Find matching paragraph and sentence
            best_match = None
            best_score = 0
            best_paragraph_idx = None
            best_sentence_idx = None
            
            # Check each paragraph
            for p_idx, p_data in citation_data.get("paragraphs", {}).items():
                paragraph_text = p_data.get("text", "")
                
                # Calculate similarity score with paragraph
                p_score = self._similarity_score(chunk_text, paragraph_text)
                
                if p_score > best_score:
                    best_score = p_score
                    best_match = p_data
                    best_paragraph_idx = p_idx
                    best_sentence_idx = None
                
                # Check each sentence if needed
                if granularity == "sentence":
                    for s_idx, s_data in p_data.get("sentences", {}).items():
                        sentence_text = s_data.get("text", "")
                        
                        # Calculate similarity score with sentence
                        s_score = self._similarity_score(chunk_text, sentence_text)
                        
                        if s_score > best_score:
                            best_score = s_score
                            best_match = p_data
                            best_paragraph_idx = p_idx
                            best_sentence_idx = s_idx
            
            # Create citation based on granularity
            if not best_match:
                # Fall back to document-level citation
                return f"Document: {citation_data.get('document_title', document_id)}"
            
            page_num = best_match.get("page", 1)
            
            if granularity == "page":
                return f"Page {page_num}"
            
            if granularity == "paragraph":
                return f"Page {page_num}, Paragraph {int(best_paragraph_idx) + 1}"
            
            if granularity == "sentence" and best_sentence_idx is not None:
                return f"Page {page_num}, Paragraph {int(best_paragraph_idx) + 1}, Sentence {int(best_sentence_idx) + 1}"
            
            # Fall back to paragraph-level citation
            return f"Page {page_num}, Paragraph {int(best_paragraph_idx) + 1}"
            
        except Exception as e:
            logger.error(f"Error getting citation: {str(e)}")
            # Fall back to document-level citation
            return f"Document {document_id}"
    
    def _similarity_score(self, text1: str, text2: str) -> float:
        """
        Calculate similarity score between two text strings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Simple overlap-based similarity
        # This is a simplified approach; more sophisticated NLP could be used
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_document_structure(self, document_id: str) -> Dict[str, Any]:
        """
        Get document structure for citation mapping visualization.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document structure dictionary
        """
        try:
            # Get citation metadata
            citation_data = self.citation_metadata.get(document_id)
            if not citation_data:
                return {
                    "document_id": document_id,
                    "document_title": "Unknown",
                    "structure": []
                }
            
            # Create document structure
            structure = []
            
            # Group paragraphs by page
            pages = {}
            for p_idx, p_data in citation_data.get("paragraphs", {}).items():
                page_num = p_data.get("page", 1)
                if page_num not in pages:
                    pages[page_num] = []
                
                # Add paragraph
                pages[page_num].append({
                    "type": "paragraph",
                    "id": f"p{p_idx}",
                    "index": int(p_idx),
                    "text": p_data.get("text", "")[:100] + "..." if len(p_data.get("text", "")) > 100 else p_data.get("text", ""),
                    "sentences": [
                        {
                            "type": "sentence",
                            "id": f"p{p_idx}s{s_idx}",
                            "index": int(s_idx),
                            "text": s_data.get("text", "")
                        }
                        for s_idx, s_data in p_data.get("sentences", {}).items()
                    ]
                })
            
            # Create page structure
            for page_num in sorted(pages.keys()):
                structure.append({
                    "type": "page",
                    "id": f"page{page_num}",
                    "number": page_num,
                    "paragraphs": pages[page_num]
                })
            
            return {
                "document_id": document_id,
                "document_title": citation_data.get("document_title", "Unknown"),
                "structure": structure
            }
            
        except Exception as e:
            logger.error(f"Error getting document structure: {str(e)}")
            return {
                "document_id": document_id,
                "document_title": "Unknown",
                "structure": []
            }
