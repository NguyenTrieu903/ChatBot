"""RAG chain using Groq AI with Vector Memory.

This module provides backward compatibility.
For new implementations, use rag_chain.RAGChain instead.

The new RAGChain uses:
- Pinecone for vector storage (production-ready)
- LangChain Expression Language (LCEL)
- Best practices from Real Python tutorial
"""

# Import the new RAGChain for backward compatibility
from .rag_chain import RAGChain

# Alias for backward compatibility
RetrievalChain = RAGChain

# Export both names
__all__ = ['RetrievalChain', 'RAGChain']
