"""
Configuration settings for the Document Research & Theme Identification Chatbot.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Data directory for storing uploaded documents and processed files
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vectordb")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# API settings
API_PREFIX = "/api/v1"
PROJECT_NAME = "Document Research & Theme Identification Chatbot"
DEBUG = True

# OCR settings
OCR_ENGINE = "tesseract"  # Options: "tesseract", "paddleocr"
OCR_LANGUAGE = "eng"  # Default language for OCR

# Vector database settings
VECTOR_DB_TYPE = "chroma"  # Options: "chroma", "qdrant", "faiss"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Default embedding model

# LLM settings
LLM_PROVIDER = "openai"  # Options: "openai", "gemini", "groq"
LLM_MODEL = "gpt-3.5-turbo"  # Default model
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Document processing settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "tiff", "bmp", 
    "doc", "docx", "txt", "rtf", "odt"
}

# Theme identification settings
MIN_THEME_DOCUMENTS = 2  # Minimum number of documents to form a theme
THEME_SIMILARITY_THRESHOLD = 0.75  # Similarity threshold for theme grouping
