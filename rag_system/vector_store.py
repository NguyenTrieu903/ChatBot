"""Production-ready vector store using Pinecone with LangChain best practices.

Uses PineconeEmbeddings and PineconeVectorStore from langchain-pinecone.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Workaround for Pinecone deprecated plugin error
# This must be done BEFORE importing pinecone
os.environ.setdefault("PINECONE_DISABLE_DEPRECATED_PLUGIN_CHECK", "1")

# Monkey patch to bypass deprecated plugin check if needed
try:
    import pinecone.deprecated_plugins as deprecated_plugins
    # Override the check function to do nothing
    deprecated_plugins.check_for_deprecated_plugins = lambda: None
except (ImportError, AttributeError):
    pass

from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone

load_dotenv()


class VectorStore:
    """Pinecone vector store with PineconeEmbeddings.
    
    Production-ready implementation using official langchain-pinecone integration.
    """

    def __init__(self, use_case: str = "vietnamese_support"):
        """Initialize Pinecone vector store.
        
        Args:
            use_case: Use case name (default: vietnamese_support)
        """
        self.use_case = use_case
        self.index_name = f"{use_case}-index".lower().replace("_", "-")
        self.embeddings = self._initialize_embeddings()
        self.pc = self._initialize_pinecone()
        self.index = None
        self.vectorstore: Optional[PineconeVectorStore] = None
        
        # Ensure index exists
        self._ensure_index_exists()

    def _initialize_embeddings(self) -> PineconeEmbeddings:
        """Initialize Pinecone embeddings.
        
        Returns:
            PineconeEmbeddings instance with multilingual-e5-large model
        """
        print("📥 Đang khởi tạo PineconeEmbeddings với model multilingual-e5-large...")
        
        return PineconeEmbeddings(model="multilingual-e5-large")

    def _initialize_pinecone(self) -> Pinecone:
        """Initialize Pinecone client.
        
        Returns:
            Pinecone client instance
            
        Raises:
            ValueError: If PINECONE_API_KEY not found
        """
        api_key = os.getenv("PINECONE_API_KEY")
        
        if not api_key:
            raise ValueError(
                "PINECONE_API_KEY not found in .env file. "
                "Get your API key at: https://app.pinecone.io/"
            )
        
        pc = Pinecone(api_key=api_key)
        print(f"✅ Pinecone client initialized")
        return pc

    def _ensure_index_exists(self) -> None:
        """Create Pinecone index if it doesn't exist.
        
        Creates index with appropriate dimensions for multilingual-e5-large (1024 dimensions).
        """
        dimension = 1024  # multilingual-e5-large dimension
        
        try:
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
                
        except Exception as e:
            print(f"⚠️  Could not check/create index: {e}")
            print(f"   Index '{self.index_name}' will be created on first document upload")
            print(f"   Or create it manually in Pinecone console: https://app.pinecone.io/")

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
            documents: List of Document objects (LangChain) or dictionaries with 'page_content' and 'metadata'
        """
        if not documents:
            raise ValueError("No documents provided")
        
        print(f"📚 Creating Pinecone index with {len(documents)} documents...")
        
        # Convert to LangChain Documents (handle both Document objects and dicts)
        docs = []
        for doc in documents:
            if isinstance(doc, Document):
                # Already a Document object, use it directly
                docs.append(doc)
            elif isinstance(doc, dict):
                # Dictionary, convert to Document
                docs.append(Document(
                    page_content=doc.get("page_content", ""),
                    metadata=doc.get("metadata", {})
                ))
            else:
                raise ValueError(f"Unsupported document type: {type(doc)}")
        
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
        
        # Get vectorstore and add documents
        try:
            vectorstore = self._get_vectorstore()
            
            # Check if index has any vectors
            index = self._get_index()
            stats = index.describe_index_stats()
            existing_vectors = stats.get('total_vector_count', 0)
            
            if existing_vectors > 0:
                print(f"✅ Connecting to existing Pinecone index with {existing_vectors} vectors")
                print(f"📤 Adding {len(docs)} new documents to Pinecone...")
                vectorstore.add_documents(docs)
                print(f"✅ Successfully added {len(docs)} documents to Pinecone")
            else:
                # Create new index with documents
                print(f"📤 Creating new Pinecone index with {len(docs)} documents...")
                vectorstore.add_documents(docs)
                print(f"✅ Successfully created Pinecone index with {len(docs)} documents")
            
        except Exception as e:
            raise ValueError(
                f"Failed to create/connect to Pinecone index '{self.index_name}': {e}\n"
                f"Please create the index manually in Pinecone console: https://app.pinecone.io/"
            )

    def load_index(self) -> None:
        """Load existing Pinecone index.
        
        Connects to existing Pinecone index without re-uploading documents.
        """
        try:
            vectorstore = self._get_vectorstore()
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
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            return self.index_name in existing_indexes
        except:
            # If check fails, assume index doesn't exist (will be created)
            return False

    def delete_index(self) -> None:
        """Delete Pinecone index (use with caution!).
        
        This will permanently delete all vectors in the index.
        """
        try:
            self.pc.delete_index(self.index_name)
            print(f"✅ Deleted index: {self.index_name}")
        except Exception as e:
            raise ValueError(f"Failed to delete index: {e}")

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
                "dimension": 1024  # multilingual-e5-large dimension
            }
        except Exception as e:
            return {
                "index_name": self.index_name,
                "error": str(e),
                "note": "Stats unavailable - index may not exist yet"
            }
    
    def get_retriever(self, k: int = 5, score_threshold: Optional[float] = None):
        """Get LangChain Retriever from Pinecone vector store.
        
        This is the recommended way to use vector store with LangChain RAG.
        
        Args:
            k: Number of documents to retrieve (increased for better coverage)
            score_threshold: Minimum similarity score (0-1). If None, no threshold applied.
            
        Returns:
            LangChain Retriever instance
        """
        vectorstore = self._get_vectorstore()
        
        # Create retriever with similarity search
        # Note: Pinecone uses cosine distance, so lower threshold = more results
        if score_threshold is not None:
            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": k,
                    "score_threshold": score_threshold
                }
            )
        else:
            # No threshold - return top k results
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
        
        return retriever
