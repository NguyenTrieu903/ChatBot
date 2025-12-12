"""Configuration settings for RAG system."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JSON_DATA_FILE = DATA_DIR / "traning.json"

# API Keys
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")

# LLM Configuration
LLM_MODEL = "llama-3.3-70b-versatile"
# Giảm temperature để trả lời chính xác hơn cho domain medical
LLM_TEMPERATURE = 0.3  # Giảm từ 0.7 xuống 0.3 để ít "sáng tạo" hơn
LLM_MAX_TOKENS = 2000  # Giảm để tiết kiệm tokens và trả lời tập trung hơn

# Embedding Configuration
EMBEDDING_MODEL = "multilingual-e5-large"
EMBEDDING_DIMENSION = 1024  # multilingual-e5-large dimension

# Vector Store Configuration
DEFAULT_USE_CASE = "vietnamese_support"
DEFAULT_INDEX_NAME = f"{DEFAULT_USE_CASE}-index"
# Tăng số lượng documents để có nhiều thông tin hơn
RETRIEVER_K = 5  # Giảm xuống 5 để tiết kiệm tokens, vẫn đủ thông tin
RETRIEVER_SCORE_THRESHOLD = 0.5  # Chỉ lấy documents có similarity >= 0.5

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

