# Document Research & Theme Identification Chatbot

## Project Overview

This project implements an interactive chatbot capable of performing research across a large set of documents (75+ documents), identifying common themes, and providing detailed, cited responses to user queries. The system supports various document formats, including PDF and scanned images, and provides comprehensive citation mapping to support identified themes.

## Features

### Core Functionality

1. **Document Upload and Knowledge Base Creation**
   - Support for 75+ documents in various formats (PDF, images, Word, text)
   - OCR processing for scanned documents using Tesseract and PaddleOCR
   - High-fidelity text extraction with poppler-utils for PDFs
   - Integrated document storage and management system

2. **Document Management & Query Processing**
   - Intuitive interface for viewing uploaded documents
   - Natural language query processing
   - Document-specific query execution
   - Precise citations with page, paragraph, and sentence-level granularity

3. **Theme Identification & Cross-Document Synthesis**
   - Collective analysis of responses from all documents
   - Identification of common themes across documents
   - Synthesized answers with clear theme identification
   - Comprehensive citation mapping to support each theme

### Extra Credit Features

1. **Enhanced Citation Granularity**
   - Paragraph-level citations
   - Sentence-level citations
   - Citation mapping to original documents

2. **Visual Citation Mapping**
   - Interactive visualization of document citations
   - Visual mapping between themes and source documents
   - Citation network visualization

3. **Advanced Filtering Options**
   - Date-based filtering
   - Author filtering
   - Document type filtering
   - Relevance score filtering

4. **Document Selection/Deselection**
   - Selection of specific documents for targeted queries
   - Selection persistence across sessions
   - Selection sharing and export

## Technical Architecture

### Backend Components

1. **Document Processor**
   - Handles document uploads and storage
   - Extracts text using appropriate methods based on document type
   - Processes scanned documents with OCR
   - Manages document metadata

2. **Vector Database Service**
   - Embeds document text using HuggingFace embeddings
   - Stores document chunks in ChromaDB for semantic search
   - Provides efficient retrieval of relevant document sections

3. **Query Processor**
   - Processes natural language queries
   - Executes queries against the vector database
   - Formats results with proper citations

4. **Theme Processor**
   - Analyzes document responses to identify common themes
   - Uses clustering algorithms to group related content
   - Generates synthesized responses with theme identification

5. **Enhanced Services**
   - Enhanced citation service for granular citations
   - Visual citation service for interactive visualizations
   - Advanced filtering service for document filtering
   - Document selection service for targeted queries

### Technologies Used

- **AI Language Models**: OpenAI GPT, Gemini, Groq
- **Vector Databases**: ChromaDB
- **OCR Libraries**: Tesseract, PaddleOCR
- **Backend Framework**: FastAPI
- **Embedding Models**: HuggingFace Sentence Transformers
- **Clustering Algorithms**: DBSCAN for theme identification
- **PDF Processing**: poppler-utils for high-quality text extraction

## Implementation Details

### Document Processing Pipeline

1. **Upload Phase**
   - Document is uploaded and stored in the system
   - Metadata is extracted and saved
   - Document is queued for processing

2. **Processing Phase**
   - Text extraction based on document type
   - For PDFs: poppler-utils with OCR fallback
   - For images: OCR processing
   - For Word documents: text extraction with conversion fallback

3. **Indexing Phase**
   - Text is split into chunks
   - Chunks are embedded using sentence transformers
   - Embeddings are stored in ChromaDB
   - Citation metadata is generated

### Query Processing Pipeline

1. **Query Phase**
   - User submits natural language query
   - Query is processed and embedded

2. **Search Phase**
   - Query embedding is compared to document embeddings
   - Relevant document chunks are retrieved
   - Results are ranked by relevance

3. **Response Phase**
   - Results are formatted with citations
   - Citations are generated at appropriate granularity
   - Response is returned to user

### Theme Identification Pipeline

1. **Analysis Phase**
   - Document responses are collected
   - Embeddings are clustered using DBSCAN
   - Common themes are identified

2. **Synthesis Phase**
   - Themes are named and described
   - Supporting citations are collected
   - Synthesized response is generated

3. **Visualization Phase**
   - Theme-document relationships are visualized
   - Citation networks are generated
   - Interactive visualizations are created

## Deployment Instructions

1. **Prerequisites**
   - Python 3.11+
   - Required packages listed in requirements.txt

2. **Installation**
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd chatbot_theme_identifier

   # Install dependencies
   pip install -r backend/requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Running the Application**
   ```bash
   # Start the backend server
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Deployment Options**
   - Render
   - Railway
   - Replit
   - Hugging Face Spaces
   - Vercel

## Future Enhancements

1. **Scalability Improvements**
   - Distributed document processing
   - Caching for frequent queries
   - Batch processing for large document sets

2. **User Experience Enhancements**
   - Real-time processing status updates
   - Interactive theme exploration
   - Customizable citation formats

3. **Advanced Features**
   - Multi-language support
   - Domain-specific models for specialized documents
   - Collaborative document analysis

## Conclusion

The Document Research & Theme Identification Chatbot provides a powerful tool for analyzing large document sets, identifying common themes, and generating detailed, cited responses. With its comprehensive feature set and robust architecture, it offers an effective solution for document research and theme identification tasks.
