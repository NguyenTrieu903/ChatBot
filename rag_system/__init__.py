"""RAG System for Vietnamese Chatbot.

This package provides a production-ready RAG (Retrieval-Augmented Generation)
system using Pinecone for vector storage and Groq AI for LLM inference.
"""

from .rag_chain import RAGChain, RetrievalChain
from .pinecone.vector_store import VectorStore
from .core.config import validate_config
from .core.logger import get_logger
from .core.exceptions import (
    RAGError,
    ConfigurationError,
    VectorStoreError,
    RetrievalError,
    LLMError
)

__all__ = [
    "RAGChain",
    "RetrievalChain",
    "VectorStore",
    "validate_config",
    "get_logger",
    "RAGError",
    "ConfigurationError",
    "VectorStoreError",
    "RetrievalError",
    "LLMError",
]

__version__ = "1.0.0"
