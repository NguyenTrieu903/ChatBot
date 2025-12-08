"""Production-ready vector store using Pinecone with LangChain best practices.

Based on:
- https://realpython.com/build-llm-rag-chatbot-with-langchain/
- https://docs.langchain.com/oss/python/langchain/rag#pinecone
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Try to use langchain-pinecone (newer, better compatibility with Pinecone serverless)
try:
    from langchain_pinecone import PineconeVectorStore
    USE_LANGCHAIN_PINECONE = True
except ImportError:
    # Fallback to langchain-community
    from langchain_community.vectorstores import Pinecone as PineconeVectorStore
    USE_LANGCHAIN_PINECONE = False
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    # Fallback to deprecated version
    from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
import pinecone

load_dotenv()


class VectorStore:
    """Pinecone vector store with local embeddings (sentence-transformers).
    
    Production-ready implementation following LangChain best practices.
    Uses Pinecone for scalable, cloud-based vector storage.
    """

    def __init__(self, use_case: str = "vietnamese_support"):
        """Initialize Pinecone vector store.
        
        Args:
            use_case: Use case name (default: vietnamese_support)
        """
        self.use_case = use_case
        self.embeddings = self._initialize_embeddings()
        self.vectorstore: Optional[Pinecone] = None
        self.index_name = f"{use_case}-index".lower().replace("_", "-")
        
        # Initialize Pinecone
        self._initialize_pinecone()
        
        # Create or connect to index
        self._ensure_index_exists()

    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        """Initialize local embeddings (no API needed!).
        
        Returns:
            HuggingFaceEmbeddings instance
        """
        print("📥 Đang tải mô hình embedding local (lần đầu có thể mất vài phút)...")
        
        # Use multilingual model that supports Vietnamese
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def _initialize_pinecone(self) -> None:
        """Initialize Pinecone client.
        
        Raises:
            ValueError: If PINECONE_API_KEY not found
        """
        api_key = os.getenv("PINECONE_API_KEY")
        
        if not api_key:
            raise ValueError(
                "PINECONE_API_KEY not found in .env file. "
                "Get your API key at: https://app.pinecone.io/"
            )
        
        # Try newer Pinecone API first (serverless)
        try:
            from pinecone import Pinecone as PineconeClient
            self.pc = PineconeClient(api_key=api_key)
            self.use_new_api = True
            print(f"✅ Pinecone initialized (serverless API)")
        except ImportError:
            # Fall back to older API
            try:
                environment = os.getenv("PINECONE_ENVIRONMENT") or os.getenv("PINECONE_ENV")
                if environment:
                    pinecone.init(api_key=api_key, environment=environment)
                else:
                    pinecone.init(api_key=api_key)
                self.use_new_api = False
                print(f"✅ Pinecone initialized (legacy API)")
            except Exception as e:
                raise ValueError(f"Failed to initialize Pinecone: {e}")

    def _ensure_index_exists(self) -> None:
        """Create Pinecone index if it doesn't exist.
        
        Creates index with appropriate dimensions for the embedding model.
        """
        dimension = 384  # MiniLM-L12-v2 dimension
        
        try:
            if hasattr(self, 'use_new_api') and self.use_new_api:
                # New Pinecone API (serverless)
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                
                if self.index_name not in existing_indexes:
                    print(f"📦 Creating Pinecone index: {self.index_name}")
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=dimension,
                        metric="cosine",
                        spec={
                            "serverless": {
                                "cloud": "aws",
                                "region": "us-east-1"
                            }
                        }
                    )
                    print(f"✅ Index '{self.index_name}' created")
                    print(f"⏳ Waiting for index to be ready (this may take 1-2 minutes)...")
                    import time
                    # Wait for index to be ready
                    while True:
                        try:
                            index_description = self.pc.describe_index(self.index_name)
                            if hasattr(index_description, 'status') and index_description.status.get('ready'):
                                print(f"✅ Index '{self.index_name}' is ready!")
                                break
                            time.sleep(2)
                        except:
                            time.sleep(2)
                else:
                    print(f"✅ Index '{self.index_name}' already exists")
            else:
                # Legacy Pinecone API
                existing_indexes = pinecone.list_indexes()
                
                if self.index_name not in existing_indexes:
                    print(f"📦 Creating Pinecone index: {self.index_name}")
                    pinecone.create_index(
                        name=self.index_name,
                        dimension=dimension,
                        metric="cosine"
                    )
                    print(f"✅ Index '{self.index_name}' created")
                else:
                    print(f"✅ Index '{self.index_name}' already exists")
                    
        except Exception as e:
            print(f"⚠️  Could not check/create index: {e}")
            print(f"   Index '{self.index_name}' will be created on first document upload")
            print(f"   Or create it manually in Pinecone console: https://app.pinecone.io/")

    def create_index(self, documents: List[Dict[str, Any]]) -> None:
        """Create Pinecone index from documents.
        
        Args:
            documents: List of document dictionaries with 'page_content' and 'metadata'
        """
        if not documents:
            raise ValueError("No documents provided")
        
        print(f"📚 Creating Pinecone index with {len(documents)} documents...")
        
        # Convert to LangChain Documents
        docs = [
            Document(
                page_content=doc["page_content"],
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
        
        # Add metadata to ensure proper filtering
        for i, doc in enumerate(docs):
            if not doc.metadata:
                doc.metadata = {}
            doc.metadata["use_case"] = self.use_case
            doc.metadata["doc_id"] = i
        
        # Ensure index exists before trying to use it
        if not self.index_exists():
            print(f"⚠️  Index '{self.index_name}' does not exist. Creating it now...")
            self._ensure_index_exists()
            # Wait a bit for index to be ready
            import time
            time.sleep(3)
        
        # Create or connect to Pinecone vector store
        try:
            # Check if index has any vectors
            if hasattr(self, 'use_new_api') and self.use_new_api:
                index = self.pc.Index(self.index_name)
                stats = index.describe_index_stats()
                existing_vectors = stats.get('total_vector_count', 0)
            else:
                existing_vectors = 0  # Assume empty for legacy API
            
            if existing_vectors > 0:
                # Connect to existing index and add new documents
                print(f"✅ Connecting to existing Pinecone index with {existing_vectors} vectors")
                # Use from_documents workaround for new API compatibility
                # Document is already imported at top of file
                dummy_doc = Document(page_content="__init__", metadata={"__init__": True})
                
                if USE_LANGCHAIN_PINECONE:
                    # New langchain-pinecone API
                    self.vectorstore = PineconeVectorStore.from_documents(
                        documents=[dummy_doc],
                        embedding=self.embeddings,
                        index_name=self.index_name
                    )
                else:
                    # Legacy langchain-community API
                    self.vectorstore = PineconeVectorStore.from_documents(
                        documents=[dummy_doc],
                        embedding=self.embeddings,
                        index_name=self.index_name
                    )
                print(f"📤 Adding {len(docs)} new documents to Pinecone...")
                self.vectorstore.add_documents(docs)
                print(f"✅ Successfully added {len(docs)} documents to Pinecone")
            else:
                # Create new index with documents
                print(f"📤 Creating new Pinecone index with {len(docs)} documents...")
                # Both APIs use from_documents
                self.vectorstore = PineconeVectorStore.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    index_name=self.index_name
                )
                print(f"✅ Successfully created Pinecone index with {len(docs)} documents")
            
        except Exception as e:
            # If from_existing_index fails, try from_documents (will create if needed)
            print(f"⚠️  Could not connect to existing index, creating new one...")
            try:
                # Both APIs use from_documents
                self.vectorstore = PineconeVectorStore.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    index_name=self.index_name
                )
                print(f"✅ Successfully created Pinecone index with {len(docs)} documents")
            except Exception as e2:
                raise ValueError(
                    f"Failed to create/connect to Pinecone index '{self.index_name}': {e2}\n"
                    f"Please create the index manually in Pinecone console: https://app.pinecone.io/"
                )

    def search(self, query: str, k: int = 3, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using Pinecone.
        
        Args:
            query: Search query string
            k: Number of results to return
            filter_dict: Optional metadata filter (e.g., {"use_case": "vietnamese_support"})
            
        Returns:
            List of similar documents with scores
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_index() or load_index() first.")
        
        try:
            # Perform similarity search with optional filtering
            if filter_dict:
                results = self.vectorstore.similarity_search_with_score(
                    query, 
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                # Pinecone returns cosine distance (0 = identical, 2 = opposite)
                # Convert to similarity score (0-1 scale)
                similarity = 1 - (score / 2)  # Normalize to 0-1
                
                # Only include if similarity > 0.3 (adjust threshold as needed)
                if similarity > 0.3:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"⚠️  Error during search: {e}")
            return []

    def load_index(self) -> None:
        """Load existing Pinecone index.
        
        Connects to existing Pinecone index without re-uploading documents.
        Uses a workaround for LangChain compatibility with new Pinecone API.
        """
        try:
            # For new Pinecone API, LangChain has compatibility issues
            # Workaround: Use from_documents with a single dummy doc, then it connects to existing
            if hasattr(self, 'use_new_api') and self.use_new_api:
                # Create minimal document just to initialize connection
                # Document is already imported at top of file
                dummy_doc = Document(
                    page_content="__init__",
                    metadata={"__init__": True}
                )
                
                # This will connect to existing index
                self.vectorstore = PineconeVectorStore.from_documents(
                    documents=[dummy_doc],
                    embedding=self.embeddings,
                    index_name=self.index_name
                )
                
                # The dummy document will be added, but it's minimal
                # In production, you might want to filter it out in search
                print(f"✅ Connected to Pinecone index: {self.index_name}")
            else:
                # Legacy API - try from_existing_index first, fallback to from_documents
                try:
                    if not USE_LANGCHAIN_PINECONE:
                        # Old API has from_existing_index
                        self.vectorstore = PineconeVectorStore.from_existing_index(
                            index_name=self.index_name,
                            embedding=self.embeddings
                        )
                    else:
                        raise AttributeError("New API doesn't have from_existing_index")
                except (AttributeError, Exception):
                    # Fallback: use from_documents (works for both)
                    dummy_doc = Document(page_content="__init__", metadata={"__init__": True})
                    self.vectorstore = PineconeVectorStore.from_documents(
                        documents=[dummy_doc],
                        embedding=self.embeddings,
                        index_name=self.index_name
                    )
                print(f"✅ Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            raise ValueError(
                f"Failed to load Pinecone index '{self.index_name}': {e}\n"
                f"Try running 'python setup.py' to recreate the index, or check PINECONE_API_KEY."
            )

    def index_exists(self) -> bool:
        """Check if Pinecone index exists.
        
        Returns:
            True if index exists, False otherwise
        """
        try:
            if hasattr(self, 'use_new_api') and self.use_new_api:
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                return self.index_name in existing_indexes
            else:
                existing_indexes = pinecone.list_indexes()
                return self.index_name in existing_indexes
        except:
            # If check fails, assume index doesn't exist (will be created)
            return False

    def delete_index(self) -> None:
        """Delete Pinecone index (use with caution!).
        
        This will permanently delete all vectors in the index.
        """
        try:
            pinecone.delete_index(self.index_name)
            print(f"✅ Deleted index: {self.index_name}")
        except Exception as e:
            try:
                if hasattr(self, 'pc'):
                    self.pc.delete_index(self.index_name)
                    print(f"✅ Deleted index: {self.index_name}")
            except Exception as e2:
                raise ValueError(f"Failed to delete index: {e2}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            if hasattr(self, 'use_new_api') and self.use_new_api:
                # New API
                index = self.pc.Index(self.index_name)
                stats = index.describe_index_stats()
                return {
                    "index_name": self.index_name,
                    "total_vectors": stats.get('total_vector_count', 0),
                    "dimension": stats.get('dimension', 384)
                }
            else:
                # Legacy API
                index_stats = pinecone.describe_index(self.index_name)
                return {
                    "index_name": self.index_name,
                    "dimension": index_stats.dimension,
                    "metric": index_stats.metric,
                    "status": index_stats.status.get('ready', 'unknown') if hasattr(index_stats, 'status') else 'unknown'
                }
        except Exception as e:
            return {
                "index_name": self.index_name,
                "error": str(e),
                "note": "Stats unavailable - index may not exist yet"
            }
    
    def get_retriever(self, k: int = 3, score_threshold: float = 0.3):
        """Get LangChain Retriever from Pinecone vector store.
        
        This is the recommended way to use vector store with LangChain RAG.
        
        Args:
            k: Number of documents to retrieve
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            LangChain Retriever instance
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_index() or load_index() first.")
        
        # Create retriever with similarity search
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": k,
                "score_threshold": score_threshold
            }
        )
        
        return retriever
