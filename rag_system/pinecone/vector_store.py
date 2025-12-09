"""Production-ready vector store using Pinecone with LangChain best practices.

Uses PineconeEmbeddings and PineconeVectorStore from langchain-pinecone.
"""

import time
from typing import List, Dict, Any, Optional

# Workaround for Pinecone deprecated plugin error
# This must be done BEFORE importing pinecone
import os
os.environ.setdefault("PINECONE_DISABLE_DEPRECATED_PLUGIN_CHECK", "1")

# Monkey patch to bypass deprecated plugin check if needed
try:
    import pinecone.deprecated_plugins as deprecated_plugins
    deprecated_plugins.check_for_deprecated_plugins = lambda: None
except (ImportError, AttributeError):
    pass

from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone

from ..core.config import (
    PINECONE_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    PINECONE_CLOUD,
    PINECONE_REGION,
    PINECONE_METRIC,
    DEFAULT_INDEX_NAME
)
from ..core.logger import get_logger
from ..core.exceptions import VectorStoreError, ConfigurationError

logger = get_logger(__name__)


class VectorStore:
    """Pinecone vector store with PineconeEmbeddings.
    
    Production-ready implementation using official langchain-pinecone integration.
    """
    
    def __init__(self, use_case: str = "vietnamese_support"):
        """Initialize Pinecone vector store.
        
        Args:
            use_case: Use case name (default: vietnamese_support)
            
        Raises:
            ConfigurationError: If PINECONE_API_KEY is missing
            VectorStoreError: If initialization fails
        """
        self.use_case = use_case
        self.index_name = f"{use_case}-index".lower().replace("_", "-")
        
        try:
            self.embeddings = self._initialize_embeddings()
            self.pc = self._initialize_pinecone()
            self.index = None
            self.vectorstore: Optional[PineconeVectorStore] = None
            
            # Ensure index exists
            self._ensure_index_exists()
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise VectorStoreError(f"Vector store initialization failed: {e}") from e
    
    def _initialize_embeddings(self) -> PineconeEmbeddings:
        """Initialize Pinecone embeddings.
        
        Returns:
            PineconeEmbeddings instance
        """
        logger.info(f"Initializing PineconeEmbeddings with model {EMBEDDING_MODEL}...")
        return PineconeEmbeddings(model=EMBEDDING_MODEL)
    
    def _initialize_pinecone(self) -> Pinecone:
        """Initialize Pinecone client.
        
        Returns:
            Pinecone client instance
            
        Raises:
            ConfigurationError: If PINECONE_API_KEY not found
        """
        if not PINECONE_API_KEY:
            raise ConfigurationError(
                "PINECONE_API_KEY not found. "
                "Get your API key at: https://app.pinecone.io/"
            )
        
        pc = Pinecone(api_key=PINECONE_API_KEY)
        logger.info("Pinecone client initialized")
        return pc
    
    def _ensure_index_exists(self) -> None:
        """Create Pinecone index if it doesn't exist."""
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=EMBEDDING_DIMENSION,
                    metric=PINECONE_METRIC,
                    spec={
                        "serverless": {
                            "cloud": PINECONE_CLOUD,
                            "region": PINECONE_REGION
                        }
                    }
                )
                logger.info(f"Index '{self.index_name}' created, waiting for readiness...")
                
                # Wait for index to be ready
                while True:
                    try:
                        index_description = self.pc.describe_index(self.index_name)
                        if hasattr(index_description, 'status') and index_description.status.get('ready'):
                            logger.info(f"Index '{self.index_name}' is ready")
                            break
                        time.sleep(2)
                    except Exception:
                        time.sleep(2)
            else:
                logger.info(f"Index '{self.index_name}' already exists")
                
        except Exception as e:
            logger.warning(f"Could not check/create index: {e}")
            logger.info("Index will be created on first document upload")
    
    def _get_index(self):
        """Get Pinecone index object.
        
        Returns:
            Pinecone Index object
        """
        if self.index is None:
            self.index = self.pc.Index(self.index_name)
        return self.index
    
    def _get_vectorstore(self) -> PineconeVectorStore:
        """Get or create PineconeVectorStore instance.
        
        Returns:
            PineconeVectorStore instance
        """
        if self.vectorstore is None:
            index = self._get_index()
            self.vectorstore = PineconeVectorStore(
                index=index,
                embedding=self.embeddings
            )
        return self.vectorstore
    
    def create_index(self, documents: List[Any]) -> None:
        """Create Pinecone index from documents.
        
        Args:
            documents: List of Document objects or dictionaries
            
        Raises:
            VectorStoreError: If document creation fails
        """
        if not documents:
            raise VectorStoreError("No documents provided")
        
        logger.info(f"Creating Pinecone index with {len(documents)} documents...")
        
        # Convert to LangChain Documents
        docs = []
        for doc in documents:
            if isinstance(doc, Document):
                docs.append(doc)
            elif isinstance(doc, dict):
                docs.append(Document(
                    page_content=doc.get("page_content", ""),
                    metadata=doc.get("metadata", {})
                ))
            else:
                raise VectorStoreError(f"Unsupported document type: {type(doc)}")
        
        # Add metadata
        for i, doc in enumerate(docs):
            if not doc.metadata:
                doc.metadata = {}
            doc.metadata["use_case"] = self.use_case
            doc.metadata["doc_id"] = i
        
        # Ensure index exists
        if not self.index_exists():
            logger.warning(f"Index '{self.index_name}' does not exist, creating now...")
            self._ensure_index_exists()
            time.sleep(3)
        
        # Add documents
        try:
            vectorstore = self._get_vectorstore()
            index = self._get_index()
            stats = index.describe_index_stats()
            existing_vectors = stats.get('total_vector_count', 0)
            
            if existing_vectors > 0:
                logger.info(f"Connecting to existing index with {existing_vectors} vectors")
                logger.info(f"Adding {len(docs)} new documents...")
                vectorstore.add_documents(docs)
                logger.info(f"Successfully added {len(docs)} documents")
            else:
                logger.info(f"Creating new index with {len(docs)} documents...")
                vectorstore.add_documents(docs)
                logger.info(f"Successfully created index with {len(docs)} documents")
            
        except Exception as e:
            error_msg = (
                f"Failed to create/connect to Pinecone index '{self.index_name}': {e}\n"
                f"Please create the index manually in Pinecone console: https://app.pinecone.io/"
            )
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e
    
    def load_index(self) -> None:
        """Load existing Pinecone index.
        
        Raises:
            VectorStoreError: If index loading fails
        """
        try:
            self._get_vectorstore()
            logger.info(f"Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            error_msg = (
                f"Failed to load Pinecone index '{self.index_name}': {e}\n"
                f"Try running 'python setup.py' to recreate the index."
            )
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e
    
    def index_exists(self) -> bool:
        """Check if Pinecone index exists.
        
        Returns:
            True if index exists, False otherwise
        """
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            return self.index_name in existing_indexes
        except Exception:
            return False
    
    def delete_index(self) -> None:
        """Delete Pinecone index (use with caution!).
        
        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            self.pc.delete_index(self.index_name)
            logger.info(f"Deleted index: {self.index_name}")
        except Exception as e:
            raise VectorStoreError(f"Failed to delete index: {e}") from e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            index = self._get_index()
            stats = index.describe_index_stats()
            return {
                "index_name": self.index_name,
                "total_vectors": stats.get('total_vector_count', 0),
                "dimension": EMBEDDING_DIMENSION
            }
        except Exception as e:
            return {
                "index_name": self.index_name,
                "error": str(e),
                "note": "Stats unavailable - index may not exist yet"
            }
    
    def get_retriever(self, k: int = 5, score_threshold: Optional[float] = None):
        """Get LangChain Retriever from Pinecone vector store.
        
        Args:
            k: Number of documents to retrieve
            score_threshold: Minimum similarity score (0-1). If None, no threshold applied.
            
        Returns:
            LangChain Retriever instance
            
        Raises:
            VectorStoreError: If retriever creation fails
        """
        try:
            vectorstore = self._get_vectorstore()
            
            if score_threshold is not None:
                retriever = vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "k": k,
                        "score_threshold": score_threshold
                    }
                )
            else:
                retriever = vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": k}
                )
            
            return retriever
        except Exception as e:
            raise VectorStoreError(f"Failed to create retriever: {e}") from e

