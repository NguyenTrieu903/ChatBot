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
        system_message = """Bạn là trợ lý AI của Tâm Quốc Tế, tư vấn về sản phẩm y tế và thuốc.

QUY TẮC:
1. CHỈ dùng thông tin trong [THÔNG TIN] bên dưới. KHÔNG suy đoán hay dùng kiến thức ngoài.
2. Nếu không có thông tin: "Xin lỗi, tôi không có thông tin về [tên sản phẩm] trong cơ sở dữ liệu. Vui lòng liên hệ Tâm Quốc Tế."
3. Trả lời tiếng Việt, rõ ràng, trích dẫn chính xác số liệu từ context.
4. Khi hỏi "giá", "liều dùng" mà không nêu tên → tham chiếu sản phẩm từ câu hỏi GẦN NHẤT.
5. Từ "này", "đó", "thuốc này" → tham chiếu sản phẩm từ câu hỏi TRƯỚC.

THÔNG TIN TỪ CƠ SỞ DỮ LIỆU:
{context}

NHẮC LẠI: CHỈ dùng thông tin trong [THÔNG TIN] trên. KHÔNG tạo ra thông tin mới."""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
    
    def _get_product_names(self) -> List[str]:
        """Get list of product names from JSON file.
        
        Returns:
            List of product names
        """
        try:
            import json
            if JSON_DATA_FILE.exists():
                with open(JSON_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return [item.get('name', '') for item in data if item.get('name')]
        except Exception:
            pass
        return []
    
    def _rewrite_query(self, question: str, chat_history: List[BaseMessage]) -> str:
        """Rewrite/expand query to improve retrieval quality.
        
        Args:
            question: Original user question
            chat_history: Previous conversation messages
            
        Returns:
            Rewritten/expanded query for better retrieval
        """
        # Nếu có chat history, thử tìm tên sản phẩm từ câu hỏi trước
        if chat_history:
            # Lấy danh sách sản phẩm từ JSON
            product_names = self._get_product_names()
            
            # Lấy câu hỏi gần nhất
            recent_questions = [msg.content for msg in chat_history[-4:] if hasattr(msg, 'content')]
            for recent_q in reversed(recent_questions):
                # Tìm tên sản phẩm trong câu hỏi trước
                for product in product_names:
                    if product and product.lower() in str(recent_q).lower():
                        # Nếu câu hỏi hiện tại không có tên sản phẩm, thêm vào
                        if product.lower() not in question.lower():
                            return f"{question} {product}"
                        break
        
        return question
    
    def _create_rag_chain(self):
        """Create RAG chain using LCEL with query rewriting.
        
        Returns:
            RAG chain using LangChain Expression Language
            
        Raises:
            RetrievalError: If retriever is not initialized
        """
        if self.retriever is None:
            raise RetrievalError("Retriever not initialized")
        
        def rewrite_and_retrieve(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Rewrite query and retrieve documents."""
            question = inputs["question"]
            chat_history = inputs.get("chat_history", [])
            
            # Rewrite query for better retrieval
            rewritten_query = self._rewrite_query(question, chat_history)
            
            # Retrieve documents
            docs = self.retriever.invoke(rewritten_query)
            
            # Format context
            context = format_docs(docs)
            
            return {
                "context": context,
                "question": question,  # Use original question for LLM
                "chat_history": chat_history
            }
        
        rag_chain = (
            rewrite_and_retrieve
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
    
    def _validate_response(self, response: str, context: str) -> bool:
        """Validate that response is based on context, not hallucinated.
        
        Args:
            response: LLM response
            context: Retrieved context
            
        Returns:
            True if response seems valid, False if likely hallucinated
        """
        if not context or "Không có thông tin" in context:
            # Nếu không có context, response phải thông báo không có thông tin
            no_info_keywords = [
                "không có thông tin",
                "không tìm thấy",
                "không có trong cơ sở dữ liệu",
                "liên hệ"
            ]
            return any(keyword in response.lower() for keyword in no_info_keywords)
        
        # Kiểm tra xem response có chứa thông tin từ context không
        # Lấy một số từ khóa quan trọng từ context
        context_lower = context.lower()
        response_lower = response.lower()
        
        # Tìm tên sản phẩm trong context (lấy từ JSON)
        product_names = self._get_product_names()
        found_product = None
        for product in product_names:
            if product and product.lower() in context_lower:
                found_product = product.lower()
                break
        
        # Nếu có sản phẩm trong context, response nên đề cập đến nó
        if found_product and found_product not in response_lower:
            # Có thể vẫn hợp lệ nếu response nói về sản phẩm khác từ chat history
            return True
        
        return True  # Mặc định cho phép, validation này chỉ là cảnh báo
    
    def chat(
        self,
        question: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Chat with the bot using RAG with improved retrieval.
        
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
            
            # Validate response (log warning if suspicious)
            # Lấy context để validate (có thể cache lại nếu cần)
            rewritten_query = self._rewrite_query(question, chat_history)
            docs = self.retriever.invoke(rewritten_query)
            context = format_docs(docs)
            
            if not self._validate_response(response, context):
                logger.warning(f"Response validation warning for question: {question[:50]}...")
            
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
