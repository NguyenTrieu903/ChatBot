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
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")

# LLM Configuration - Using OpenAI GPT-4o for better performance
LLM_PROVIDER = "openai"  # "openai" or "groq"
LLM_MODEL = "gpt-4o"  # OpenAI GPT-4o optimized for accuracy
# Giảm temperature để trả lời chính xác hơn cho domain medical
LLM_TEMPERATURE = 0.2  # Low temperature for factual, consistent responses
LLM_MAX_TOKENS = 2000  # Sufficient for detailed product information

# Embedding Configuration
EMBEDDING_MODEL = "multilingual-e5-large"
EMBEDDING_DIMENSION = 1024  # multilingual-e5-large dimension

# Vector Store Configuration
DEFAULT_USE_CASE = "vietnamese_support"
DEFAULT_INDEX_NAME = f"{DEFAULT_USE_CASE}-index"
# Tăng số lượng documents để có nhiều thông tin hơn
RETRIEVER_K = 8  # Tăng lên 8 để có nhiều context hơn cho semantic search
RETRIEVER_SCORE_THRESHOLD = 0.3  # Giảm xuống 0.3 để lấy nhiều documents liên quan hơn

# Memory Configuration
MEMORY_WINDOW_SIZE = 5  # Number of conversation exchanges to keep

# Chunking Configuration
# Optimized for product information: chunk size 800-900 allows each chunk to contain
# one complete topic (e.g., dosage, price, effects) while maintaining context
CHUNK_SIZE = 900  # Optimal for semantic search of product details
CHUNK_OVERLAP = 200  # Ensure no information loss at chunk boundaries

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
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in .env file or environment."
            )
    elif LLM_PROVIDER == "groq":
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

