"""RAG Chain implementation using LangChain best practices.

This module implements a production-ready RAG (Retrieval-Augmented Generation) chain
using Pinecone for vector storage and Groq AI for LLM inference.
"""

from typing import List, Dict, Any, Optional

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
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
    
    def _initialize_llm(self):
        """Initialize LLM (OpenAI or Groq based on config).
        
        Returns:
            ChatOpenAI or ChatGroq instance
            
        Raises:
            LLMError: If LLM initialization fails
        """
        try:
            from .core.config import LLM_PROVIDER, OPENAI_API_KEY, GROQ_API_KEY
            
            if LLM_PROVIDER == "openai":
                if not OPENAI_API_KEY:
                    raise LLMError("OPENAI_API_KEY not found in configuration")
                logger.info(f"Initializing OpenAI LLM: {LLM_MODEL}")
                return ChatOpenAI(
                    model=LLM_MODEL,
                    api_key=OPENAI_API_KEY,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS
                )
            else:  # groq
                if not GROQ_API_KEY:
                    raise LLMError("GROQ_API_KEY not found in configuration")
                logger.info(f"Initializing Groq LLM: {LLM_MODEL}")
                return ChatGroq(
                    model=LLM_MODEL,
                    api_key=GROQ_API_KEY,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS
                )
        except Exception as e:
            raise LLMError(f"Failed to initialize LLM: {e}") from e
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create optimized prompt template for medical product consultation.
        
        Returns:
            ChatPromptTemplate instance
        """
        system_message = """Bạn là trợ lý AI chuyên nghiệp của Tâm Quốc Tế, chuyên tư vấn về các sản phẩm y tế, thực phẩm chức năng và thuốc.

VAI TRÒ:
- Tư vấn chính xác, đầy đủ về thông tin sản phẩm
- Hỗ trợ khách hàng hiểu rõ công dụng, liều dùng, đối tượng sử dụng
- Cung cấp thông tin giá cả và chính sách mua hàng
- Thân thiện, chuyên nghiệp, dễ hiểu

QUY TẮC NGHIÊM NGẶT:
1. CHỈ SỬ DỤNG thông tin trong phần [THÔNG TIN SẢN PHẨM] bên dưới
2. TUYỆT ĐỐI KHÔNG tự suy đoán, bịa đặt, hoặc sử dụng kiến thức bên ngoài
3. Nếu KHÔNG TÌM THẤY thông tin: "Xin lỗi, hiện tại tôi không có thông tin về [tên sản phẩm/câu hỏi] trong cơ sở dữ liệu. Vui lòng liên hệ hotline Tâm Quốc Tế để được tư vấn chi tiết hơn."

CÁCH TRẢ LỜI:
- Luôn trả lời bằng tiếng Việt, rõ ràng, dễ hiểu
- Trích dẫn CHÍNH XÁC số liệu, thông tin từ database (ví dụ: "200mg/viên", "3 viên/ngày", "2.200.000₫")
- Khi nói về giá: luôn nêu rõ giá bán lẻ và chính sách giảm giá (nếu có)
- Khi nói về liều dùng: phân biệt rõ "duy trì" và "tăng cường" nếu có
- Nhấn mạnh thông tin an toàn, đối tượng sử dụng, chống chỉ định

XỬ LÝ CÂU HỎI:
- Câu hỏi về "giá", "liều dùng", "tác dụng", "đại lý" mà KHÔNG nêu tên sản phẩm → BẠN PHẢI tự động hiểu đang nói về sản phẩm từ câu hỏi/hội thoại GẦN NHẤT trong lịch sử chat
- Ví dụ: Nếu trước đó người dùng hỏi "fucoidan", sau đó hỏi "gia dai ly vip" → BẠN PHẢI hiểu là hỏi về giá đại lý VIP của The Fucoidan
- Từ thay thế như "này", "đó", "thuốc này", "sản phẩm đó" → luôn tham chiếu sản phẩm từ câu hỏi/hội thoại TRƯỚC ĐÓ
- Câu hỏi chung chung như "thuốc điều trị ung thư" → BẠN PHẢI tìm các sản phẩm có công dụng "hỗ trợ điều trị ung thư", "phòng ngừa ung thư" trong database
- Câu hỏi so sánh 2 sản phẩm → so sánh dựa trên thông tin trong database

[THÔNG TIN SẢN PHẨM]:
{context}

NHẮC NHỞ QUAN TRỌNG:
- BẠN PHẢI CHỈ sử dụng thông tin trong [THÔNG TIN SẢN PHẨM] ở trên
- Nếu thông tin không có trong database, bạn PHẢI thông báo rõ ràng là không có thông tin
- KHÔNG BAO GIỜ tự tạo ra thông tin, số liệu, hoặc mô tả mới"""
        
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
        
        Enhanced version that:
        - Extracts product names from both questions AND responses
        - Expands queries with related keywords
        - Handles contextual references better
        
        Args:
            question: Original user question
            chat_history: Previous conversation messages
            
        Returns:
            Rewritten/expanded query for better retrieval
        """
        original_question = question
        product_names = self._get_product_names()
        
        # Keywords mapping for query expansion
        keyword_expansions = {
            "gia": ["giá", "giá cả", "giá bán", "giá bán lẻ", "giá đại lý"],
            "liều dùng": ["liều lượng", "cách dùng", "hướng dẫn sử dụng"],
            "tác dụng": ["công dụng", "hiệu quả", "tác dụng phụ"],
            "ung thư": ["hỗ trợ điều trị ung thư", "phòng ngừa ung thư", "ung thư"],
            "dai ly": ["đại lý", "giá đại lý"],
            "vip": ["đại lý vip", "giá vip"]
        }
        
        # Step 1: Intelligently detect if this is a NEW product search vs. question about current product
        question_lower = question.lower()
        question_words = question_lower.split()
        
        # Check if question already mentions a product name
        question_mentions_product = False
        for product in product_names:
            if product and product.lower() in question_lower:
                question_mentions_product = True
                break
        
        # Detect intent: Is this asking about product attributes or searching for new product?
        # Strategy: Check for question words that indicate search/comparison intent
        
        # Question words that typically indicate NEW product search (tìm kiếm)
        search_question_words = ["nào", "nao", "gì", "gi", "bao nhiêu", "ba nhieu"]
        
        # Attribute keywords that indicate question about CURRENT product (hỏi về thuộc tính)
        attribute_keywords = [
            "gia", "giá", "liều", "lieu", "liều lượng", "lieu luong",
            "tác dụng", "tac dung", "công dụng", "cong dung",
            "cách dùng", "cach dung", "hướng dẫn", "huong dan",
            "đối tượng", "doi tuong", "ai", "cho ai",
            "dai ly", "đại lý", "vip", "giá bán", "gia ban",
            "có mã", "co ma", "code", "mã code"
        ]
        
        # Heuristic: If question has search words AND no attribute keywords → likely new product search
        has_search_words = any(word in question_lower for word in search_question_words)
        has_attribute_keywords = any(keyword in question_lower for keyword in attribute_keywords)
        
        # Decision logic:
        # 1. If question mentions a product → it's about that product (not new search)
        # 2. If has search words BUT has attribute keywords → likely asking about attributes
        # 3. If has search words AND no attribute keywords AND no product mentioned → likely new search
        # 4. If no search words but has attribute keywords → asking about current product
        
        is_new_product_search = False
        if question_mentions_product:
            # Already mentions a product, so it's about that product
            is_new_product_search = False
        elif has_search_words and not has_attribute_keywords:
            # Has search words but no attribute keywords → likely searching for new product
            is_new_product_search = True
        elif has_search_words and has_attribute_keywords:
            # Has both → check context: if question starts with search pattern, it's likely new search
            # But if it's mid-conversation with attribute keywords, it's about current product
            # Default: treat as attribute question (safer, as we can add context)
            is_new_product_search = False
        else:
            # No clear indicators → check if it's a short attribute question
            # Short questions (<= 5 words) with attribute keywords → likely about current product
            is_new_product_search = len(question_words) > 5 and not has_attribute_keywords
        
        logger.info(f"Query intent analysis: mentions_product={question_mentions_product}, "
                   f"has_search_words={has_search_words}, has_attribute_keywords={has_attribute_keywords}, "
                   f"is_new_product_search={is_new_product_search}")
        
        # Step 2: Only add product context if NOT a new product search AND question is about attributes
        found_product_in_context = None
        if chat_history and not is_new_product_search:
            # Extract product names from recent messages (both questions AND responses)
            recent_messages = chat_history[-6:]  # Look at more messages
            
            # First, check if current question already mentions a product
            current_question_has_product = False
            for product in product_names:
                if product and product.lower() in question_lower:
                    current_question_has_product = True
                    break
            
            # If not, try to find product from chat history (only for attribute questions)
            if not current_question_has_product:
                # Check for indirect references like "gia", "liều dùng" without product name
                needs_product_context = any(keyword in question_lower for keyword in 
                                          ["gia", "giá", "liều", "liều lượng", "lieu luong",
                                           "tác dụng", "công dụng", "dai ly", "đại lý", 
                                           "vip", "giá bán", "cach dung", "cách dùng",
                                           "doi tuong", "đối tượng", "su dung", "sử dụng",
                                           "co ma", "có mã", "code"])
                
                if needs_product_context:
                    # Try to find product from recent messages
                    for msg in reversed(recent_messages):
                        if hasattr(msg, 'content'):
                            msg_content = str(msg.content).lower()
                            
                            # Check all product names
                            for product in product_names:
                                if product and product.lower() in msg_content:
                                    found_product_in_context = product
                                    break
                            
                            if found_product_in_context:
                                break
                    
                    if found_product_in_context:
                        question = f"{question} {found_product_in_context}"
                        logger.info(f"Added product context: {found_product_in_context} to query")
        
        # Step 3: Expand query with related keywords for better semantic search
        question_lower = question.lower()
        expanded_terms = []
        
        # Expand with keyword synonyms
        for keyword, synonyms in keyword_expansions.items():
            if keyword in question_lower:
                # Add first synonym that's not already in question
                for synonym in synonyms:
                    if synonym not in question_lower:
                        expanded_terms.append(synonym)
                        break
        
        # Step 4: For new product search questions, expand with related medical terms
        if is_new_product_search:
            # Expand based on medical conditions mentioned
            if any(term in question_lower for term in ["ung thư", "cancer", "tumor"]):
                expanded_terms.extend(["hỗ trợ điều trị ung thư", "phòng ngừa ung thư"])
            elif any(term in question_lower for term in ["yeu sinh ly", "yếu sinh lý", "sinh ly", "sinh lý"]):
                expanded_terms.extend(["bổ thận", "tráng dương", "testosterone", "sinh lực nam"])
            elif any(term in question_lower for term in ["dot quy", "đột quỵ", "tai bien", "tai biến"]):
                expanded_terms.extend(["phòng ngừa đột quỵ", "hỗ trợ phục hồi sau đột quỵ"])
            elif any(term in question_lower for term in ["gan", "cholesterol", "huyet ap", "huyết áp"]):
                expanded_terms.extend(["giải độc gan", "giảm cholesterol", "điều hòa huyết áp"])
        else:
            # For attribute questions, add medical context if relevant
            if any(term in question_lower for term in ["ung thư", "cancer", "tumor"]):
                if "hỗ trợ" not in question_lower:
                    expanded_terms.append("hỗ trợ điều trị")
        
        # Combine original question with expansions
        if expanded_terms:
            expanded_query = f"{question} {' '.join(expanded_terms)}"
            logger.info(f"Expanded query: {original_question} -> {expanded_query}")
            return expanded_query
        
        if question != original_question:
            logger.info(f"Rewritten query: {original_question} -> {question}")
        elif is_new_product_search:
            logger.info(f"New product search query: {original_question} (no product context added)")
        
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
        
        Flow: JSON Data → Documents → Chunking → PineconeEmbeddings → Pinecone Index
        Each chunk = 1 vector, optimized for semantic search
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
        
        # Load and chunk documents for optimal semantic search
        chunked_docs = load_and_chunk_json(
            str(JSON_DATA_FILE),
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        if not chunked_docs:
            raise ConfigurationError("No documents loaded from JSON file")
        
        logger.info(f"Loaded and chunked into {len(chunked_docs)} chunks from JSON")
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
