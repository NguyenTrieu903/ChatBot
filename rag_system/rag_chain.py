"""RAG Chain implementation using LangChain best practices.

This module implements a production-ready RAG (Retrieval-Augmented Generation) chain
using Pinecone for vector storage and Groq AI for LLM inference.
"""

from typing import List, Dict, Any, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables import RunnableLambda
from operator import itemgetter

from .core.config import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    RETRIEVER_K,
    RETRIEVER_SCORE_THRESHOLD,
    MEMORY_WINDOW_SIZE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    JSON_DATA_FILE,
    DEFAULT_USE_CASE,
    validate_config
)
from .core.logger import get_logger
from .core.exceptions import ConfigurationError, RetrievalError, LLMError
from .pinecone.vector_store import VectorStore
from .utils.common import format_docs
from loaders.data_loader import load_and_chunk_json

logger = get_logger(__name__)


class RAGChain:
    """Production-ready RAG chain with memory management.
    
    Implements retrieval-augmented generation with:
    - Pinecone vector store for document retrieval
    - Groq AI for LLM inference
    - ConversationBufferWindowMemory for context management
    - Proper error handling and logging
    """
    
    def __init__(
        self,
        use_case: str = DEFAULT_USE_CASE,
        memory_window_size: int = MEMORY_WINDOW_SIZE
    ):
        """Initialize RAG chain.
        
        Args:
            use_case: Use case identifier for vector store
            memory_window_size: Number of conversation exchanges to keep in memory
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        validate_config()
        
        self.use_case = use_case
        self.memory_window_size = memory_window_size
        
        logger.info(f"Initializing RAG chain for use case: {use_case}")
        
        # Initialize components
        self.vector_store = VectorStore(use_case)
        self.llm = self._initialize_llm()
        self.prompt = self._create_prompt()
        self._initialize_vector_store()
        
        # Initialize retriever
        logger.info("Initializing retriever...")
        self.retriever = self.vector_store.get_retriever(
            k=RETRIEVER_K,
            score_threshold=RETRIEVER_SCORE_THRESHOLD
        )
        
        # Initialize memory
        logger.info(f"Initializing ConversationBufferWindowMemory (k={memory_window_size})...")
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=memory_window_size
        )
        
        # Create RAG chain
        logger.info("Creating RAG chain...")
        self.chain = self._create_rag_chain()
        self._log_index_stats()
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize Groq LLM.
        
        Returns:
            ChatGroq instance
            
        Raises:
            LLMError: If LLM initialization fails
        """
        try:
            from .core.config import GROQ_API_KEY
            return ChatGroq(
                model=LLM_MODEL,
                api_key=GROQ_API_KEY,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize LLM: {e}") from e
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create optimized prompt template.
        
        Returns:
            ChatPromptTemplate instance
        """
        system_message = """Bạn là trợ lý AI thông minh, hỗ trợ người dùng bằng tiếng Việt.

Nhiệm vụ của bạn:
1. Sử dụng thông tin từ cơ sở dữ liệu (context) để trả lời chính xác
2. Cung cấp hướng dẫn chi tiết, rõ ràng và dễ hiểu  
3. Luôn trả lời bằng tiếng Việt
4. Thân thiện và chuyên nghiệp

Thông tin từ cơ sở dữ liệu:
{context}

Lưu ý:
- Nếu có thông tin trong context, hãy dựa vào đó để trả lời
- Khi người dùng hỏi "giá như thế nào", "liều dùng như thế nào" mà KHÔNG đề cập tên sản phẩm 
  → Họ đang hỏi về sản phẩm được đề cập ở CÂU HỎI GẦN NHẤT
- Khi người dùng dùng từ "này", "đó", "thuốc này", "sản phẩm này" 
  → Họ đang nói về sản phẩm được đề cập ở câu hỏi trước
- LUÔN ưu tiên sản phẩm từ câu hỏi GẦN NHẤT, không phải câu hỏi cũ hơn
- Nếu không có thông tin trong context, hãy trả lời dựa trên kiến thức của bạn
- Luôn cố gắng hữu ích nhất có thể"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
    
    def _create_rag_chain(self):
        """Create RAG chain using LCEL.
        
        Returns:
            RAG chain using LangChain Expression Language
            
        Raises:
            RetrievalError: If retriever is not initialized
        """
        if self.retriever is None:
            raise RetrievalError("Retriever not initialized")
        
        rag_chain = (
            {
                "context": itemgetter("question") | self.retriever | RunnableLambda(format_docs),
                "question": itemgetter("question"),
                "chat_history": itemgetter("chat_history")
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def _initialize_vector_store(self) -> None:
        """Initialize vector store with data from JSON file.
        
        Flow: JSON Data → Chunking → PineconeEmbeddings → Pinecone Index
        """
        if self.vector_store.index_exists():
            try:
                self.vector_store.load_index()
                stats = self.vector_store.get_stats()
                vector_count = stats.get('total_vectors', 0)
                
                if vector_count > 0:
                    logger.info(
                        f"Pinecone index '{self.vector_store.index_name}' exists "
                        f"with {vector_count} vectors"
                    )
                    return
                else:
                    logger.warning("Index exists but has no vectors, creating new one...")
            except Exception as e:
                logger.warning(f"Could not load existing index: {e}, creating new one...")
        
        # Create new index
        logger.info(f"Creating Pinecone index for {self.use_case}...")
        
        if not JSON_DATA_FILE.exists():
            raise ConfigurationError(f"Data file not found: {JSON_DATA_FILE}")
        
        chunked_docs = load_and_chunk_json(
            str(JSON_DATA_FILE),
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        if not chunked_docs:
            raise ConfigurationError("No documents loaded from JSON file")
        
        logger.info(f"Loaded {len(chunked_docs)} chunks from JSON")
        logger.info("Uploading chunks to Pinecone...")
        
        self.vector_store.create_index(chunked_docs)
        
        logger.info(f"Successfully uploaded {len(chunked_docs)} chunks to Pinecone")
    
    def _log_index_stats(self) -> None:
        """Log index statistics for monitoring."""
        try:
            stats = self.vector_store.get_stats()
            logger.info(f"Index stats: {stats.get('total_vectors', 0)} vectors")
            if 'error' in stats:
                logger.warning(f"Index stats error: {stats.get('error', '')}")
        except Exception as e:
            logger.warning(f"Could not get index stats: {e}")
    
    def chat(
        self,
        question: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Chat with the bot using RAG.
        
        Args:
            question: User question
            chat_history: Previous messages (optional, uses memory if not provided)
            
        Returns:
            Response dictionary with answer and metadata
        """
        try:
            # Load chat history from memory if not provided
            if chat_history is None:
                memory_variables = self.memory.load_memory_variables({})
                chat_history = memory_variables.get("chat_history", [])
            
            # Prepare chain input
            chain_input = {
                "question": question,
                "chat_history": chat_history
            }
            
            # Generate response
            response = self.chain.invoke(chain_input)
            
            # Save to memory
            self.memory.save_context(
                {"input": question},
                {"output": response}
            )
            
            return {
                "answer": response,
                "method": "rag"
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "answer": f"Xin lỗi, đã xảy ra lỗi: {str(e)}",
                "retrieved_documents": [],
                "sources": [],
                "error": str(e)
            }
    
    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self.memory.clear()
        logger.info("Conversation memory cleared")


# Backward compatibility alias
RetrievalChain = RAGChain
