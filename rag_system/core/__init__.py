"""Core utilities for RAG system.

This module contains configuration, logging, and exception handling.
"""

from .config import (
    PROJECT_ROOT,
    DATA_DIR,
    JSON_DATA_FILE,
    GROQ_API_KEY,
    PINECONE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    DEFAULT_USE_CASE,
    DEFAULT_INDEX_NAME,
    RETRIEVER_K,
    RETRIEVER_SCORE_THRESHOLD,
    MEMORY_WINDOW_SIZE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    PINECONE_CLOUD,
    PINECONE_REGION,
    PINECONE_METRIC,
    validate_config
)
from .logger import get_logger
from .exceptions import (
    RAGError,
    ConfigurationError,
    VectorStoreError,
    RetrievalError,
    LLMError
)

__all__ = [
    # Config
    "PROJECT_ROOT",
    "DATA_DIR",
    "JSON_DATA_FILE",
    "GROQ_API_KEY",
    "PINECONE_API_KEY",
    "LLM_MODEL",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSION",
    "DEFAULT_USE_CASE",
    "DEFAULT_INDEX_NAME",
    "RETRIEVER_K",
    "RETRIEVER_SCORE_THRESHOLD",
    "MEMORY_WINDOW_SIZE",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "PINECONE_CLOUD",
    "PINECONE_REGION",
    "PINECONE_METRIC",
    "validate_config",
    # Logger
    "get_logger",
    # Exceptions
    "RAGError",
    "ConfigurationError",
    "VectorStoreError",
    "RetrievalError",
    "LLMError",
]

