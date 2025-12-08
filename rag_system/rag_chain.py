"""Production-ready RAG chain using LangChain best practices.

Based on:
- https://realpython.com/build-llm-rag-chatbot-with-langchain/
- LangChain RAG documentation

Implements proper RAG patterns with:
- Retrieval chain with context compression
- Proper prompt engineering
- Error handling
- Logging and monitoring
"""

import os
from typing import List, Dict, Any, Optional, Sequence
from operator import itemgetter

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from dotenv import load_dotenv

from .vector_store import VectorStore
from .conversation_memory import get_conversation_memory
from langchain_core.retrievers import BaseRetriever

load_dotenv()


class RAGChain:
    """Production-ready RAG chain following LangChain best practices.
    
    Implements retrieval-augmented generation with:
    - Context compression
    - Proper prompt engineering
    - Error handling
    - Conversation memory
    """

    def __init__(self, use_case: str = "vietnamese_support"):
        """Initialize RAG chain.
        
        Args:
            use_case: Use case name
        """
        self.use_case = use_case
        self.vector_store = VectorStore(use_case)
        self.llm = self._initialize_llm()
        self.prompt = self._create_prompt()
        self.retriever = None  # Will be initialized after vector store is ready
        self.chain = None  # Will be created after retriever is ready
        self._initialize_vector_store()
        # Initialize retriever and chain after vector store is ready
        self.retriever = self.vector_store.get_retriever(k=3, score_threshold=0.3)
        self.chain = self._create_rag_chain()

    def _initialize_llm(self) -> ChatGroq:
        """Initialize Groq LLM.
        
        Returns:
            ChatGroq instance
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.7,
            max_tokens=8000
        )

    def _create_prompt(self) -> ChatPromptTemplate:
        """Create optimized prompt template following best practices.
        
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

{product_context}

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
        """Create RAG chain following LangChain best practices.
        
        Uses LangChain Retriever for better integration.
        
        Returns:
            RAG chain using LCEL (LangChain Expression Language)
        """
        if self.retriever is None:
            raise ValueError("Retriever not initialized. Call _initialize_vector_store() first.")
        
        # Step 1: Retrieve documents using LangChain Retriever
        def retrieve_docs(input_dict: Dict[str, Any]) -> str:
            """Retrieve relevant documents using LangChain Retriever.
            
            Args:
                input_dict: Dictionary with 'question' key
                
            Returns:
                Formatted context string
            """
            question = input_dict.get("question", "")
            if not question:
                return "Không có câu hỏi."
            
            # Use LangChain Retriever (better integration)
            docs = self.retriever.invoke(question)
            
            if not docs:
                return "Không có thông tin liên quan trong cơ sở dữ liệu."
            
            # Format context
            context_parts = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content
                metadata = doc.metadata
                source = metadata.get('source', 'Unknown')
                product_name = metadata.get('product_name', 'Unknown')
                
                # Truncate long documents
                if len(content) > 1500:
                    content = content[:1500] + "\n... (nội dung đã rút gọn)"
                
                context_parts.append(f"Tài liệu {i} (Sản phẩm: {product_name}, Nguồn: {source}):\n{content}")
            
            return "\n\n".join(context_parts)
        
        # Step 2: Format conversation summary
        def format_conversation_summary(input_dict: Dict[str, Any]) -> str:
            """Format conversation summary if exists.
            
            Args:
                input_dict: Dictionary with optional 'conversation_summary'
                
            Returns:
                Formatted summary string
            """
            summary = input_dict.get("conversation_summary", "")
            if summary:
                return f"\n\nTóm tắt hội thoại trước:\n{summary}\n"
            return ""
        
        # Step 3: Format product context
        def format_product_context(input_dict: Dict[str, Any]) -> str:
            """Format product context if available.
            
            Args:
                input_dict: Dictionary with optional 'product_context'
                
            Returns:
                Formatted product context string
            """
            product_context = input_dict.get("product_context", "")
            if product_context:
                return f"\n⚠️ QUAN TRỌNG: {product_context}"
            return ""
        
        # Build RAG chain using LCEL
        rag_chain = (
            {
                "context": retrieve_docs,
                "conversation_summary": format_conversation_summary,
                "product_context": format_product_context,
                "question": itemgetter("question"),
                "chat_history": itemgetter("chat_history")
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain

    def _initialize_vector_store(self):
        """Initialize vector store with data from JSON file.
        
        Flow: JSON Data → Chunking → Embeddings → Pinecone Index
        """
        if not self.vector_store.index_exists():
            print(f"📚 Đang tạo Pinecone index cho {self.use_case}...")
            
            # Load from JSON file with chunking
            from data_loader import load_and_chunk_json
            from langchain_core.documents import Document
            
            json_file = "data/traning.json"
            
            print("📄 Đang đọc dữ liệu từ JSON...")
            print("   Flow: JSON → Chunking → Embeddings → Pinecone")
            
            # Step 1: Load JSON and chunk
            chunked_docs = load_and_chunk_json(
                json_file,
                chunk_size=1000,
                chunk_overlap=200
            )
            
            if not chunked_docs:
                raise ValueError("❌ Không thể đọc dữ liệu từ file JSON")
            
            print(f"✅ Đã tạo {len(chunked_docs)} chunks từ JSON")
            
            # Step 2: Create Pinecone index with chunked documents
            # Embeddings and upload to Pinecone happen inside create_index
            print("📤 Đang upload chunks lên Pinecone (với embeddings)...")
            self.vector_store.create_index(chunked_docs)
            
            print(f"✅ Hoàn thành: {len(chunked_docs)} chunks đã được embed và upload lên Pinecone")
        else:
            print(f"✅ Pinecone index '{self.vector_store.index_name}' đã tồn tại")
            self.vector_store.load_index()

    def _format_prompt_for_logging(
        self, 
        chain_input: Dict[str, Any],
        context: str
    ) -> str:
        """Format prompt for console logging.
        
        Args:
            chain_input: Input dictionary for RAG chain
            context: Actual context retrieved from vector store
            
        Returns:
            Formatted prompt string
        """
        # Format system message
        system_msg = """Bạn là trợ lý AI thông minh, hỗ trợ người dùng bằng tiếng Việt.

Nhiệm vụ của bạn:
1. Sử dụng thông tin từ cơ sở dữ liệu (context) để trả lời chính xác
2. Cung cấp hướng dẫn chi tiết, rõ ràng và dễ hiểu  
3. Luôn trả lời bằng tiếng Việt
4. Thân thiện và chuyên nghiệp

Thông tin từ cơ sở dữ liệu:
{context}

{product_context}

Lưu ý:
- Nếu có thông tin trong context, hãy dựa vào đó để trả lời
- Khi người dùng hỏi "giá như thế nào", "liều dùng như thế nào" mà KHÔNG đề cập tên sản phẩm 
  → Họ đang hỏi về sản phẩm được đề cập ở CÂU HỎI GẦN NHẤT
- Khi người dùng dùng từ "này", "đó", "thuốc này", "sản phẩm này" 
  → Họ đang nói về sản phẩm được đề cập ở câu hỏi trước
- LUÔN ưu tiên sản phẩm từ câu hỏi GẦN NHẤT, không phải câu hỏi cũ hơn
- Nếu không có thông tin trong context, hãy trả lời dựa trên kiến thức của bạn
- Luôn cố gắng hữu ích nhất có thể"""
        
        # Get values from chain_input
        question = chain_input.get("question", "")
        chat_history = chain_input.get("chat_history", [])
        conversation_summary = chain_input.get("conversation_summary", "")
        product_context = chain_input.get("product_context", "")
        
        # Replace placeholders in system message with actual context
        system_formatted = system_msg.replace("{context}", context)
        if product_context:
            system_formatted = system_formatted.replace("{product_context}", product_context)
        else:
            system_formatted = system_formatted.replace("{product_context}", "")
        
        # Build full prompt
        lines = []
        lines.append("=" * 80)
        lines.append("SYSTEM MESSAGE:")
        lines.append("=" * 80)
        lines.append(system_formatted)
        lines.append("")
        
        # Add conversation summary if exists
        if conversation_summary:
            lines.append("=" * 80)
            lines.append("CONVERSATION SUMMARY:")
            lines.append("=" * 80)
            lines.append(conversation_summary)
            lines.append("")
        
        # Add chat history
        if chat_history:
            lines.append("=" * 80)
            lines.append("CHAT HISTORY:")
            lines.append("=" * 80)
            for i, msg in enumerate(chat_history, 1):
                if hasattr(msg, 'content'):
                    # Check message type
                    msg_type = type(msg).__name__
                    if "Human" in msg_type:
                        role = "Human"
                    elif "AI" in msg_type or "Assistant" in msg_type:
                        role = "Assistant"
                    else:
                        role = msg_type
                    lines.append(f"[{i}] {role}: {msg.content}")
                else:
                    lines.append(f"[{i}] {msg}")
            lines.append("")
        
        # Add current question
        lines.append("=" * 80)
        lines.append("CURRENT QUESTION:")
        lines.append("=" * 80)
        lines.append(question)
        lines.append("")
        
        return "\n".join(lines)

    def chat(
        self,
        question: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Chat with the bot using RAG.
        
        Args:
            question: User question
            chat_history: Previous messages (for backward compatibility)
            
        Returns:
            Response dictionary with answer, sources, and metadata
        """
        try:
            # Get conversation memory
            memory = get_conversation_memory()
            recent_history = memory.get_recent_history(n=1)

            last_conv = None
            if recent_history:
                last_conv = recent_history[-1]

            # Get context for logging using retriever
            docs_for_logging = []
            context_for_logging = ""
            try:
                # Use retriever to get documents for logging
                docs_for_logging = self.retriever.invoke(question) if self.retriever else []
                
                if docs_for_logging:
                    context_parts = []
                    for i, doc in enumerate(docs_for_logging, 1):
                        content = doc.page_content
                        metadata = doc.metadata
                        source = metadata.get('source', 'Unknown')
                        product_name = metadata.get('product_name', 'Unknown')
                        
                        if len(content) > 1500:
                            content = content[:1500] + "\n... (nội dung đã rút gọn)"
                        context_parts.append(f"Tài liệu {i} (Sản phẩm: {product_name}, Nguồn: {source}):\n{content}")
                    context_for_logging = "\n\n".join(context_parts)
                else:
                    context_for_logging = "Không có thông tin liên quan trong cơ sở dữ liệu."
            except Exception as e:
                print(f"⚠️  Lỗi khi retrieve docs cho logging: {e}")
                context_for_logging = "Không thể retrieve documents."
            
            # Prepare input for RAG chain
            # LangChain Retriever will handle retrieval automatically
            chain_input = {
                "question": question,
                "chat_history": chat_history or [],
                "conversation_summary": "",  # Không dùng nữa, LangChain tự quản lý
                "product_context": ""  # Không dùng nữa, LangChain tự quản lý
            }
            
            # Format and log prompt before sending to LLM
            formatted_prompt = self._format_prompt_for_logging(
                chain_input, 
                context_for_logging
            )
            print("\n" + "="*80)
            print("📤 PROMPT GỬI ĐẾN GROQ AI:")
            print("="*80)
            print(formatted_prompt)
            print("="*80 + "\n")
            
            # Generate response using RAG chain
            response = self.chain.invoke(chain_input)
            
            # Log response from GROQ AI
            print("\n" + "="*80)
            print("📥 RESPONSE TỪ GROQ AI:")
            print("="*80)
            print(response)
            print("="*80 + "\n")
            
            # Save conversation to vector memory
            memory.add_conversation(question, response)
            
            # Get memory stats
            stats = memory.get_memory_stats()
            print(f"\n💾 Memory: {stats['total_conversations']} conversations, {stats['memory_size_mb']:.2f} MB")
            
            # Format retrieved documents for response
            retrieved_docs = []
            sources = []
            if docs_for_logging:
                for doc in docs_for_logging:
                    retrieved_docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    })
                    sources.append(doc.metadata.get('source', 'Unknown'))
            
            return {
                "answer": response,
                "retrieved_documents": retrieved_docs,
                "sources": sources,
                "method": "rag" if docs_for_logging else "direct",
                "memory_stats": stats
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "answer": f"Xin lỗi, đã xảy ra lỗi: {str(e)}",
                "retrieved_documents": [],
                "sources": [],
                "error": str(e)
            }


# Backward compatibility alias
RetrievalChain = RAGChain

