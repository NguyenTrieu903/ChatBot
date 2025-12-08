"""Vector-based conversation memory for efficient chat history management."""

import os
from typing import List, Dict, Tuple
from datetime import datetime
import faiss
import numpy as np
import pickle

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    # Fallback to deprecated version
    from langchain_community.embeddings import HuggingFaceEmbeddings


class VectorConversationMemory:
    """Stores conversation history in vector database for semantic retrieval."""
    
    def __init__(self, memory_dir: str = "conversation_memory"):
        """Initialize vector conversation memory.
        
        Args:
            memory_dir: Directory to store conversation memory
        """
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        # Initialize embeddings (same as main system for consistency)
        print("🧠 Initializing conversation memory embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Vector store for history
        self.dimension = 384  # MiniLM embedding dimension
        self.index = None
        self.conversations = []  # List of (question, answer, timestamp) tuples
        
        # Load existing memory if available
        self._load_memory()
    
    def _load_memory(self):
        """Load existing conversation memory from disk."""
        index_path = os.path.join(self.memory_dir, "history_index.faiss")
        data_path = os.path.join(self.memory_dir, "history_data.pkl")
        
        if os.path.exists(index_path) and os.path.exists(data_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(data_path, 'rb') as f:
                    self.conversations = pickle.load(f)
                print(f"✅ Loaded {len(self.conversations)} conversation pairs from memory")
            except Exception as e:
                print(f"⚠️  Could not load memory: {e}")
                self._initialize_empty_index()
        else:
            self._initialize_empty_index()
    
    def _initialize_empty_index(self):
        """Initialize empty FAISS index."""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product for cosine similarity
        self.conversations = []
        print("✅ Initialized empty conversation memory")
    
    def _save_memory(self):
        """Save conversation memory to disk."""
        try:
            index_path = os.path.join(self.memory_dir, "history_index.faiss")
            data_path = os.path.join(self.memory_dir, "history_data.pkl")
            
            faiss.write_index(self.index, index_path)
            with open(data_path, 'wb') as f:
                pickle.dump(self.conversations, f)
        except Exception as e:
            print(f"⚠️  Could not save memory: {e}")
    
    def add_conversation(self, question: str, answer: str):
        """Add a conversation pair to memory.
        
        Args:
            question: User's question
            answer: Bot's answer
        """
        if not question or not answer:
            return
        
        try:
            # Create embedding from question (for semantic retrieval)
            embedding = self.embeddings.embed_query(question)
            embedding_array = np.array([embedding], dtype='float32')
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding_array)
            
            # Add to index
            self.index.add(embedding_array)
            
            # Store conversation data
            timestamp = datetime.now().isoformat()
            self.conversations.append({
                'question': question,
                'answer': answer,
                'timestamp': timestamp
            })
            
            # Save to disk periodically (every 5 conversations)
            if len(self.conversations) % 5 == 0:
                self._save_memory()
                
        except Exception as e:
            print(f"⚠️  Error adding conversation to memory: {e}")
    
    def get_relevant_history(self, current_question: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant conversation history based on current question.
        
        Args:
            current_question: Current user question
            top_k: Number of relevant conversations to retrieve
            
        Returns:
            List of relevant conversation dictionaries
        """
        if not self.conversations or self.index.ntotal == 0:
            return []
        
        try:
            # Embed current question
            query_embedding = self.embeddings.embed_query(current_question)
            query_array = np.array([query_embedding], dtype='float32')
            faiss.normalize_L2(query_array)
            
            # Search for similar questions
            k = min(top_k, len(self.conversations))
            distances, indices = self.index.search(query_array, k)
            
            # Retrieve relevant conversations (filter by similarity threshold)
            relevant = []
            for dist, idx in zip(distances[0], indices[0]):
                if dist > 0.5:  # Similarity threshold
                    relevant.append(self.conversations[idx])
            
            return relevant
            
        except Exception as e:
            print(f"⚠️  Error retrieving history: {e}")
            return []
    
    def get_recent_history(self, n: int = 3) -> List[Dict]:
        """Get N most recent conversations.
        
        Args:
            n: Number of recent conversations to retrieve
            
        Returns:
            List of recent conversation dictionaries
        """
        if not self.conversations:
            return []
        
        return self.conversations[-n:]
    
    def clear_memory(self):
        """Clear all conversation memory."""
        self._initialize_empty_index()
        self._save_memory()
        print("✅ Conversation memory cleared")
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about conversation memory.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            'total_conversations': len(self.conversations),
            'vector_count': self.index.ntotal if self.index else 0,
            'memory_size_mb': self._estimate_memory_size()
        }
    
    def _estimate_memory_size(self) -> float:
        """Estimate memory size in MB."""
        index_path = os.path.join(self.memory_dir, "history_index.faiss")
        data_path = os.path.join(self.memory_dir, "history_data.pkl")
        
        total_size = 0
        if os.path.exists(index_path):
            total_size += os.path.getsize(index_path)
        if os.path.exists(data_path):
            total_size += os.path.getsize(data_path)
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def format_history_for_prompt(self, relevant_history: List[Dict]) -> str:
        """Format relevant history for inclusion in prompt.
        
        Args:
            relevant_history: List of relevant conversation dictionaries
            
        Returns:
            Formatted history string
        """
        if not relevant_history:
            return ""
        
        formatted = []
        for i, conv in enumerate(relevant_history, 1):
            formatted.append(f"[Hỏi trước]: {conv['question']}")
            formatted.append(f"[Đã trả lời]: {conv['answer']}")
        
        return "\n".join(formatted)


# Singleton instance for global access
_memory_instance = None


def get_conversation_memory() -> VectorConversationMemory:
    """Get or create conversation memory singleton.
    
    Returns:
        VectorConversationMemory instance
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = VectorConversationMemory()
    return _memory_instance

