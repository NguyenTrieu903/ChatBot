"""Custom exceptions for RAG system."""


class RAGError(Exception):
    """Base exception for RAG system errors."""
    pass


class ConfigurationError(RAGError):
    """Raised when configuration is invalid or missing."""
    pass


class VectorStoreError(RAGError):
    """Raised when vector store operations fail."""
    pass


class RetrievalError(RAGError):
    """Raised when document retrieval fails."""
    pass


class LLMError(RAGError):
    """Raised when LLM operations fail."""
    pass

