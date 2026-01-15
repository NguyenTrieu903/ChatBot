"""Production-ready vector store using ChromaDB with LangChain best practices.

Uses HuggingFace embeddings (multilingual-e5-large) and ChromaDB for local vector storage.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()


class VectorStore:
    """ChromaDB vector store with HuggingFace embeddings.
    
    Production-ready implementation using ChromaDB for local, persistent vector storage.
    No API key required - completely free and local!
    """

    def __init__(self, use_case: str = "vietnamese_support"):
        """Initialize ChromaDB vector store.
        
        Args:
            use_case: Use case name (default: vietnamese_support)
        """
        self.use_case = use_case
        self.collection_name = f"{use_case}_collection".lower().replace("-", "_")
        
        # Set up persistent directory for ChromaDB
        self.persist_directory = os.path.join(
            Path(__file__).parent.parent, 
            "chroma_db", 
            self.collection_name
        )
        
        print(f"💾 ChromaDB persist directory: {self.persist_directory}")
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings()
        
        # Initialize vectorstore (will be created/loaded as needed)
        self.vectorstore: Optional[Chroma] = None

    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        """Initialize HuggingFace embeddings.
        
        Uses multilingual-e5-large model for Vietnamese support.
        Model will be downloaded on first use (~1.5GB).
        
        Returns:
            HuggingFaceEmbeddings instance
        """
        print("📥 Initializing HuggingFace embeddings (multilingual-e5-large)...")
        print("   First time will download model (~1.5GB)...")
        
        # Use multilingual-e5-large for Vietnamese support
        embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        
        print("✅ Embeddings initialized")
        return embeddings

    def _get_vectorstore(self) -> Chroma:
        """Get or create ChromaDB vectorstore instance.
        
        Returns:
            Chroma vectorstore instance
        """
        if self.vectorstore is None:
            # Try to load existing collection
            if self.index_exists():
                print(f"📂 Loading existing ChromaDB collection: {self.collection_name}")
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                print(f"✅ Loaded collection with {self.vectorstore._collection.count()} documents")
            else:
                print(f"📦 Creating new ChromaDB collection: {self.collection_name}")
                # Create new collection
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
        return self.vectorstore

    def create_index(self, documents: List[Any]) -> None:
        """Create ChromaDB collection from documents.
        
        Args:
            documents: List of Document objects (LangChain) or dictionaries with 'page_content' and 'metadata'
        """
        if not documents:
            raise ValueError("No documents provided")
        
        print(f"📚 Creating ChromaDB collection with {len(documents)} documents...")
        
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
        
        # Create or update vectorstore
        try:
            if self.index_exists():
                # Load existing and add new documents
                vectorstore = self._get_vectorstore()
                print(f"📤 Adding {len(docs)} documents to existing collection...")
                vectorstore.add_documents(docs)
                print(f"✅ Successfully added {len(docs)} documents")
            else:
                # Create new collection with documents
                print(f"📤 Creating new collection with {len(docs)} documents...")
                self.vectorstore = Chroma.from_documents(
                    documents=docs,
                    embedding=self.embeddings,
                    collection_name=self.collection_name,
                    persist_directory=self.persist_directory
                )
                print(f"✅ Successfully created collection with {len(docs)} documents")
            
            # Persist to disk
            print("💾 Persisting to disk...")
            if hasattr(self.vectorstore, 'persist'):
                self.vectorstore.persist()
            print("✅ Collection persisted successfully")
            
        except Exception as e:
            raise ValueError(
                f"Failed to create ChromaDB collection '{self.collection_name}': {e}"
            )

    def load_index(self) -> None:
        """Load existing ChromaDB collection.
        
        Connects to existing ChromaDB collection without re-uploading documents.
        """
        try:
            vectorstore = self._get_vectorstore()
            doc_count = vectorstore._collection.count()
            print(f"✅ Connected to ChromaDB collection: {self.collection_name} ({doc_count} documents)")
        except Exception as e:
            raise ValueError(
                f"Failed to load ChromaDB collection '{self.collection_name}': {e}\n"
                f"Try running 'python setup.py' to recreate the collection."
            )

    def index_exists(self) -> bool:
        """Check if ChromaDB collection exists.
        
        Returns:
            True if collection exists, False otherwise
        """
        try:
            # Check if persist directory exists and has data
            persist_path = Path(self.persist_directory)
            if not persist_path.exists():
                return False
            
            # Check if directory has ChromaDB files
            chroma_files = list(persist_path.glob("chroma.sqlite3"))
            return len(chroma_files) > 0
            
        except Exception as e:
            print(f"⚠️  Error checking collection existence: {e}")
            return False

    def delete_index(self) -> None:
        """Delete ChromaDB collection (use with caution!).
        
        This will permanently delete all vectors in the collection.
        """
        try:
            import shutil
            persist_path = Path(self.persist_directory)
            if persist_path.exists():
                shutil.rmtree(persist_path)
                print(f"✅ Deleted collection: {self.collection_name}")
                self.vectorstore = None
            else:
                print(f"⚠️  Collection directory not found: {self.persist_directory}")
        except Exception as e:
            raise ValueError(f"Failed to delete collection: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            vectorstore = self._get_vectorstore()
            doc_count = vectorstore._collection.count()
            
            return {
                "collection_name": self.collection_name,
                "total_documents": doc_count,
                "persist_directory": self.persist_directory,
                "embedding_model": "intfloat/multilingual-e5-large",
                "dimension": 1024  # multilingual-e5-large dimension
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "error": str(e),
                "note": "Stats unavailable - collection may not exist yet"
            }
    
    def get_retriever(self, k: int = 5, score_threshold: Optional[float] = None):
        """Get LangChain Retriever from ChromaDB vector store with score filtering.
        
        This is the recommended way to use vector store with LangChain RAG.
        
        Args:
            k: Number of documents to retrieve (default: 5)
            score_threshold: Minimum similarity score (0-1). 
                           Recommended: 0.7 for strict medical RAG
                           If None, uses default 0.7 for safety
            
        Returns:
            LangChain Retriever instance with score filtering
        """
        vectorstore = self._get_vectorstore()
        
        # For medical/pharma domain, ALWAYS use score threshold for safety
        # Default to 0.7 if not specified (strict filtering)
        if score_threshold is None:
            score_threshold = 0.7  # Strict threshold for medical safety
            print(f"⚠️  Using default score_threshold={score_threshold} for medical safety")
        
        # Create retriever with similarity score threshold
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": k,
                "score_threshold": score_threshold
            }
        )
        
        return retriever
    
    def search_with_scores(self, query: str, k: int = 5, score_threshold: float = 0.7):
        """Search documents with similarity scores for debugging.
        
        Args:
            query: Search query
            k: Number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of (Document, score) tuples that pass threshold
        """
        vectorstore = self._get_vectorstore()
        
        # Get documents with scores
        docs_and_scores = vectorstore.similarity_search_with_relevance_scores(
            query, k=k
        )
        
        # Filter by threshold
        filtered = [(doc, score) for doc, score in docs_and_scores if score >= score_threshold]
        
        print(f"🔍 Retrieved {len(docs_and_scores)} docs, {len(filtered)} passed threshold {score_threshold}")
        for doc, score in filtered:
            product_name = doc.metadata.get('product_name', 'Unknown')
            print(f"   ✓ {product_name}: {score:.3f}")
        
        return filtered
