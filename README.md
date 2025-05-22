# Document Research & Theme Identification Chatbot

## Introduction

This README provides an overview of the Document Research & Theme Identification Chatbot, a comprehensive solution for analyzing large document sets, identifying common themes, and providing detailed, cited responses to user queries.

## Features

### Core Functionality

- **Document Upload and Processing**: Support for 75+ documents in various formats (PDF, images, Word, text) with OCR for scanned documents
- **Semantic Search**: Advanced vector database integration for accurate document retrieval
- **Theme Identification**: Automatic discovery of common themes across documents
- **Detailed Citations**: Precise citations indicating source locations (page, paragraph, sentence)
- **Cross-Document Synthesis**: Coherent answers synthesized from multiple documents

### Extra Credit Features

- **Enhanced Citation Granularity**: Paragraph and sentence-level citations
- **Visual Citation Mapping**: Interactive visualizations linking citations to documents
- **Advanced Filtering**: Filter by date, author, document type, and relevance
- **Document Selection**: Select/deselect specific documents for targeted querying

## Getting Started

### Prerequisites

- Python 3.11+
- Required packages listed in `backend/requirements.txt`

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd chatbot_theme_identifier
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Running the Application

1. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Access the application:
   - Backend API: http://localhost:8000/docs
   - Frontend interface: http://localhost:8000/

## Usage Guide

### Uploading Documents

1. Navigate to the Documents page
2. Click "Upload Document"
3. Select a file from your computer
4. Add optional metadata (title, description, tags)
5. Click "Upload"

### Querying Documents

1. Navigate to the Query page
2. Enter your natural language query
3. Select documents to include (optional)
4. Click "Search"
5. View individual document responses with citations

### Identifying Themes

1. Navigate to the Themes page
2. Enter a query or select "Analyze All Documents"
3. Adjust theme identification parameters (optional)
4. Click "Identify Themes"
5. Explore identified themes with supporting citations

### Using Advanced Features

- **Citation Visualization**: Click "Visualize" on any citation to see its context
- **Advanced Filtering**: Use the filter panel to narrow down document selection
- **Document Selection**: Create and manage document selections for targeted research
- **Export Results**: Export query results and theme identifications as PDF or JSON

## Project Structure

```
chatbot_theme_identifier/
├── backend/
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core processing logic
│   │   ├── models/         # Data models
│   │   ├── services/       # Enhanced services
│   │   ├── main.py         # Application entry point
│   │   └── config.py       # Configuration settings
│   ├── data/               # Data storage
│   └── requirements.txt    # Dependencies
├── docs/                   # Documentation
├── tests/                  # Unit and integration tests
└── demo/                   # Demo materials
```

## Technical Details

For more detailed technical information, please refer to the [Technical Report](docs/technical_report.md).

## Deployment

The application can be deployed on various platforms:
- Render
- Railway
- Replit
- Hugging Face Spaces
- Vercel

See the [Deployment Guide](docs/deployment_guide.md) for detailed instructions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- Google for Gemini models
- Groq for LLAMA hosting
- ChromaDB for vector database
- Tesseract and PaddleOCR for OCR capabilities
