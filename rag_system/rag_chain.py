import os
from typing import List, Dict, Any, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from dotenv import load_dotenv

from .vector_store import VectorStore
from langchain_core.runnables import RunnableLambda
from operator import itemgetter
from .utils.common import format_docs
from data_loader import load_and_chunk_json

load_dotenv()


class RAGChain:
    def __init__(self, use_case: str = "vietnamese_support", k: int = 1):
        """Initialize RAG chain.
        
        Args:
            use_case: Use case name
            k: Number of conversation exchanges to keep in memory (default: 5)
        """
        self.use_case = use_case
        print(f"🔧 Initializing RAG chain for use case: {use_case}")
        self.vector_store = VectorStore(use_case)
        self.llm = self._initialize_llm()
        self.prompt = self._create_prompt()
        self._initialize_vector_store()
        print("🔍 Initializing retriever...")
        self.retriever = self.vector_store.get_retriever(k=5, score_threshold=None)
        
        # Initialize ConversationBufferWindowMemory
        # k=5 means keep last 5 conversation exchanges (10 messages: 5 user + 5 assistant)
        print(f"💾 Initializing ConversationBufferWindowMemory (k={k})...")
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=k  # Keep last k conversation exchanges
        )
        
        print("🔗 Creating RAG chain...")
        self.chain = self._create_rag_chain()
        self._log_index_stats()

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

                            Lưu ý:
                            - Nếu có thông tin trong context, hãy dựa vào đó để trả lời
                            - Khi người dùng hỏi "giá như thế nào", "liều dùng như thế nào" mà KHÔNG đề cập tên sản phẩm 
                            → Họ đang hỏi về sản phẩm được đề cập ở CÂU HỎI GẦN NHẤT
                            - Khi người dùng dùng từ "này", "đó", "thuốc này", "sản phẩm này" 
                            → Họ đang nói về sản phẩm được đề cập ở câu hỏi trước
                            - LUÔN ưu tiên sản phẩm từ câu hỏi GẦN NHẤT, không phải câu hỏi cũ hơn
                            - Nếu không có thông tin trong context, hãy trả lời dựa trên kiến thức của bạn
                            - Luôn cố gắng hữu ích nhất có thể"""
        
        # Create prompt with chat history support
        messages = [
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),  # LangChain will handle chat history
            ("human", "{question}")
        ]
        
        return ChatPromptTemplate.from_messages(messages)

    def _create_rag_chain(self):
        """Create RAG chain following LangChain best practices.
        
        Uses LangChain Retriever for better integration.
        
        Returns:
            RAG chain using LCEL (LangChain Expression Language)
        """
        if self.retriever is None:
            raise ValueError("Retriever not initialized. Call _initialize_vector_store() first.")        
        
        # Build RAG chain using LCEL
        # The retriever automatically handles query embedding with PineconeEmbeddings
        # Memory will be loaded and saved in chat() method
        rag_chain = (
            {
                "context": itemgetter("question") | self.retriever | RunnableLambda(format_docs),
                "question": itemgetter("question"),
                "chat_history": itemgetter("chat_history")  # Load from memory
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain

    def _initialize_vector_store(self):
        """Initialize vector store with data from JSON file.
        
        Flow: JSON Data → Chunking → PineconeEmbeddings → Pinecone Index
        
        Uses VectorStore methods:
        - index_exists(): Check if index exists
        - create_index(): Create index with documents (handles embeddings automatically)
        - load_index(): Connect to existing index
        - get_stats(): Get index statistics
        """
        # Check if index exists and has data
        index_exists = self.vector_store.index_exists()
        
        if index_exists:
            # Try to load existing index
            try:
                self.vector_store.load_index()
                
                # Check if index has vectors
                stats = self.vector_store.get_stats()
                vector_count = stats.get('total_vectors', 0)
                
                if vector_count > 0:
                    print(f"✅ Pinecone index '{self.vector_store.index_name}' đã tồn tại với {vector_count} vectors")
                    print("   Sử dụng index hiện có...")
                    return
                else:
                    print(f"⚠️  Index tồn tại nhưng chưa có vectors, đang tạo mới...")
            except Exception as e:
                print(f"⚠️  Không thể load index hiện có: {e}")
                print("   Đang tạo index mới...")
        
        # Index doesn't exist or is empty, create new one
        print(f"📚 Đang tạo Pinecone index cho {self.use_case}...")
        
        # Load from JSON file with chunking  
        chunked_docs = load_and_chunk_json("data/traning.json", 1000, 200)

        print("📤 Đang upload chunks lên Pinecone...")
        print("   (PineconeEmbeddings đang được tạo tự động...)")
        self.vector_store.create_index(chunked_docs)
        
        print(f"✅ Hoàn thành: {len(chunked_docs)} chunks đã được embed và upload lên Pinecone")
    
    def _log_index_stats(self):
        """Log index statistics for debugging."""
        try:
            stats = self.vector_store.get_stats()
            print(f"\n📊 Pinecone Index Statistics: success")
            if 'error' in stats:
                print(f"   ⚠️  Warning: {stats.get('error', '')}")
        except Exception as e:
            print(f"⚠️  Could not get index stats: {e}")


    def chat(
        self,
        question: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Chat with the bot using RAG with ConversationBufferWindowMemory.
        
        Args:
            question: User question
            chat_history: Previous messages (optional, will use memory if not provided)
            
        Returns:
            Response dictionary with answer and metadata
        """
        try:
            # Load chat history from memory if not provided
            if chat_history is None:
                # Get chat history from memory
                memory_variables = self.memory.load_memory_variables({})
                chat_history = memory_variables.get("chat_history", [])
            else:
                # Use provided chat history (for backward compatibility)
                pass
            
            # Prepare input for RAG chain
            chain_input = {
                "question": question,
                "chat_history": chat_history
            }
            
            # Generate response using RAG chain
            # The chain will:
            # 1. Retrieve documents using retriever (with PineconeEmbeddings)
            # 2. Format documents into context
            # 3. Pass to LLM with prompt (including chat history)
            response = self.chain.invoke(chain_input)
            
            # Save conversation to memory
            # Memory will automatically keep only last k exchanges
            self.memory.save_context(
                {"input": question},
                {"output": response}
            )
            
            return {
                "answer": response,
                "method": "rag"
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
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        print("🗑️  Đã xóa lịch sử hội thoại")


# Backward compatibility alias
RetrievalChain = RAGChain

