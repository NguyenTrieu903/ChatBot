"""Configuration settings for RAG system."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JSON_DATA_FILE = DATA_DIR / "traning.json"  # [AGENT: OLD CODE] - Giữ lại để tương thích ngược
# Excel data files
EXCEL_DATA_FILES = [
    DATA_DIR / "traning.xlsx",
    DATA_DIR / "traning_new.xlsx"
]

# API Keys
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")

# LLM Configuration
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 8000

# Embedding Configuration
EMBEDDING_MODEL = "multilingual-e5-large"
EMBEDDING_DIMENSION = 1024  # multilingual-e5-large dimension

# Vector Store Configuration
DEFAULT_USE_CASE = "vietnamese_support"
DEFAULT_INDEX_NAME = f"{DEFAULT_USE_CASE}-index"
RETRIEVER_K = 5
RETRIEVER_SCORE_THRESHOLD = None

# Memory Configuration
MEMORY_WINDOW_SIZE = 5  # Number of conversation exchanges to keep

# Chunking Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Pinecone Configuration
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
PINECONE_METRIC = "cosine"

# Workaround for Pinecone deprecated plugin error
os.environ.setdefault("PINECONE_DISABLE_DEPRECATED_PLUGIN_CHECK", "1")


def validate_config() -> None:
    """Validate that all required configuration is present.
    
    Raises:
        ValueError: If required configuration is missing
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )
    
    if not PINECONE_API_KEY:
        raise ValueError(
            "PINECONE_API_KEY not found in environment variables. "
            "Please set it in .env file or environment."
        )

