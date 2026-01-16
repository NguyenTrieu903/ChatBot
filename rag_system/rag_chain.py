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
from .medical_taxonomy_auto import (
    detect_condition_and_products
)
from .vietnamese_normalizer import normalize_vietnamese

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
        print("🔍 Initializing retriever with strict score threshold...")
        # For medical safety: strict threshold 0.7 to prevent irrelevant context
        self.retriever = self.vector_store.get_retriever(k=5, score_threshold=0.7)
        
        # Initialize ConversationBufferWindowMemory
        # k=5 means keep last 5 conversation exchanges (10 messages: 5 user + 5 assistant)
        print(f"💾 Initializing ConversationBufferWindowMemory (k={k})...")
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=k  # Keep last k conversation exchanges
        )
        
        # Track the current product being discussed (for accurate follow-up questions)
        self.current_product = None
        
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
        """Create strict medical prompt to prevent hallucination.
        
        Returns:
            ChatPromptTemplate instance
        """
        system_message = """Bạn là trợ lý tư vấn sản phẩm y tế TẬN TÂM và HỮU ÍCH.

🎯 NHIỆM VỤ: Trả lời câu hỏi dựa trên THÔNG TIN ĐƯỢC CUNG CẤP bên dưới.

📚 THÔNG TIN ĐƯỢC CUNG CẤP:
{context}

✅ CÁCH TRẢ LỜI:
1. ĐỌC kỹ thông tin được cung cấp
2. TRẢ LỜI trực tiếp, rõ ràng, tự nhiên
3. TRÍCH XUẤT thông tin cụ thể: giá, liều dùng, thành phần, công dụng
4. KHÔNG nói "không có thông tin" khi thông tin ĐÃ CÓ TRONG CONTEXT
5. KHÔNG sử dụng kiến thức ngoài CONTEXT

💡 LƯU Ý:
- Nếu có ghi chú "💡 LƯU Ý: Người dùng hỏi về..." → Thông tin phía dưới ĐÃ LIÊN QUAN, hãy dùng!
- User hỏi "giá?" → Tìm số tiền trong thông tin
- User hỏi "thành phần?" → Tìm danh sách thành phần
- User hỏi "liều dùng?" → Tìm số viên/ngày
- User hỏi về bệnh lý → Giới thiệu sản phẩm phù hợp

⚠️ CHỈ từ chối khi user yêu cầu CHẨN ĐOÁN hoặc KÊ ĐƠN

TRÍCH XUẤT và TRẢ LỜI dựa trên thông tin có sẵn!"""
        
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
                
                # Check if collection has documents
                stats = self.vector_store.get_stats()
                vector_count = stats.get('total_documents', 0)
                
                if vector_count > 0:
                    print(f"✅ ChromaDB collection '{self.vector_store.collection_name}' đã tồn tại với {vector_count} documents")
                    print("   Sử dụng collection hiện có...")
                    return
                else:
                    print(f"⚠️  Collection tồn tại nhưng chưa có documents, đang tạo mới...")
            except Exception as e:
                print(f"⚠️  Không thể load collection hiện có: {e}")
                print("   Đang tạo collection mới...")
        
        # Collection doesn't exist or is empty, create new one
        print(f"📚 Đang tạo ChromaDB collection cho {self.use_case}...")
        
        # Load from JSON file with chunking  
        chunked_docs = load_and_chunk_json("data/traning.json", 1000, 200)

        print("📤 Đang lưu chunks vào ChromaDB...")
        print("   (HuggingFace embeddings đang được tạo tự động...)")
        self.vector_store.create_index(chunked_docs)
        
        print(f"✅ Hoàn thành: {len(chunked_docs)} chunks đã được embed và lưu vào ChromaDB")
    
    def _log_index_stats(self):
        """Log collection statistics for debugging."""
        try:
            stats = self.vector_store.get_stats()
            print(f"\n📊 ChromaDB Collection Statistics: success")
            if 'error' in stats:
                print(f"   ⚠️  Warning: {stats.get('error', '')}")
        except Exception as e:
            print(f"⚠️  Could not get collection stats: {e}")


    def chat(
        self,
        question: str,
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Chat with the bot using RAG with strict safety controls and context-aware retrieval.
        
        Args:
            question: User question
            chat_history: Previous messages (optional, will use memory if not provided)
            
        Returns:
            Response dictionary with answer, sources, and safety flags
        """
        try:
            # ✨ VIETNAMESE TEXT NORMALIZATION (NEW!)
            # Convert text without diacritics to proper Vietnamese with diacritics
            # Example: "gia bao nhieu" → "giá bao nhiêu"
            original_question = question
            question = normalize_vietnamese(question)
            
            # 🚨 SAFETY LAYER 1: Question Classification
            safety_check = self._classify_question_safety(question)
            if not safety_check["is_safe"]:
                # Don't call LLM - return safety message immediately
                # Save to memory even for blocked questions
                self.memory.save_context(
                    {"input": question},
                    {"output": safety_check["message"]}
                )
                return {
                    "answer": safety_check["message"],
                    "method": "safety_blocked",
                    "sources": [],
                    "warning": safety_check["reason"]
                }
            
            # Load chat history from memory if not provided
            if chat_history is None:
                memory_variables = self.memory.load_memory_variables({})
                chat_history = memory_variables.get("chat_history", [])
            
            # 🩺 MEDICAL CONDITION DETECTION (NEW - INTELLIGENT!)
            # Check if user is asking about a medical condition
            # Example: "thuốc nào bổ thận" → detect "bổ thận" → find "Kidney & Men's"
            condition_result = detect_condition_and_products(question)
            
            if condition_result:
                # User is asking about a product or condition! Use intelligent search
                if condition_result['query_type'] == 'product_search':
                    print(f"🏷️  Product search: {condition_result['products'][0]}")
                else:
                    print(f"🩺 Condition detected: {condition_result['condition_name']}")
                
                print(f"📦 Matching products: {condition_result['products']}")
                
                # 🎯 Track the PRIMARY product (first one in list - most relevant)
                self.current_product = condition_result['products'][0]
                print(f"🎯 Setting current product: {self.current_product}")
                
                # Use product names as query for precise retrieval
                enhanced_query = " ".join(condition_result['products'])
            else:
                # No condition detected - use context-aware enhancement
                # 🔍 CONTEXT-AWARE QUERY ENHANCEMENT
                # If question is vague (e.g., "giá bao nhiêu?"), enhance with context
                enhanced_query = self._enhance_query_with_context(question, chat_history)
            
            # 🚨 SAFETY LAYER 2: Retrieve documents with score threshold
            # Use ENHANCED query for better context-aware retrieval
            retrieved_docs = self.retriever.get_relevant_documents(enhanced_query)
            
            print(f"🔍 Original query: {question}")
            print(f"🔍 Enhanced query: {enhanced_query}")
            print(f"📄 Retrieved {len(retrieved_docs)} documents")
            
            # HARD FALLBACK: If no documents retrieved (all below threshold)
            if not retrieved_docs or len(retrieved_docs) == 0:
                fallback_message = (
                    "❌ Tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu để trả lời câu hỏi này.\n\n"
                    "💡 Vui lòng:\n"
                    "- Thử diễn đạt câu hỏi khác đi\n"
                    "- Liên hệ dược sĩ hoặc tra cứu tài liệu chính thức"
                )
                # Save to memory even for fallback
                self.memory.save_context(
                    {"input": question},
                    {"output": fallback_message}
                )
                return {
                    "answer": fallback_message,
                    "method": "no_relevant_context",
                    "sources": [],
                    "warning": "No documents passed similarity threshold"
                }
            
            # Format context from retrieved documents
            from .utils.common import format_docs
            context = format_docs(retrieved_docs)
            
            # 🚨 SAFETY LAYER 3: Double-check context is not empty
            if not context or context.strip() == "":
                empty_message = "❌ Không có đủ thông tin để trả lời câu hỏi này. Vui lòng liên hệ dược sĩ."
                # Save to memory
                self.memory.save_context(
                    {"input": question},
                    {"output": empty_message}
                )
                return {
                    "answer": empty_message,
                    "method": "empty_context",
                    "sources": [],
                    "warning": "Context is empty after formatting"
                }
            
            # 🩺 ADD CONTEXT NOTE if product/condition was detected
            # This tells LLM that we already matched the query to products
            if condition_result:
                if condition_result['query_type'] == 'product_search':
                    # User asked about a specific product
                    product_name = condition_result['products'][0]
                    context_note = f"\n\n💡 LƯU Ý: Người dùng hỏi về sản phẩm '{product_name}'. Thông tin bên dưới là về sản phẩm này. HÃY TRẢ LỜI dựa trên thông tin được cung cấp!\n\n"
                else:
                    # User asked about a medical condition
                    context_note = f"\n\n💡 LƯU Ý: Người dùng hỏi về '{condition_result['condition_name']}'. Thông tin bên dưới là về các sản phẩm điều trị/hỗ trợ tình trạng này: {', '.join(condition_result['products'])}. Hãy trả lời dựa trên thông tin này.\n\n"
                
                context = context_note + context
            
            # 📊 DEBUG: Log context being sent to LLM
            print(f"\n{'='*60}")
            print(f"📋 CONTEXT SENT TO LLM:")
            print(f"{'='*60}")
            context_preview = context[:500] + "..." if len(context) > 500 else context
            print(context_preview)
            print(f"{'='*60}\n")
            
            # 🔧 FIX: Create a custom prompt chain that uses our pre-retrieved context
            # Instead of letting the RAG chain retrieve again, we pass the context directly
            # Create a simple chain that uses our prepared context
            custom_chain = (
                {
                    "context": lambda x: context,  # Use our pre-retrieved context with condition note
                    "question": lambda x: x["question"],
                    "chat_history": lambda x: x["chat_history"]
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Prepare input for custom chain
            chain_input = {
                "question": question,
                "chat_history": chat_history
            }
            
            # Generate response using custom chain with our pre-retrieved context
            response = custom_chain.invoke(chain_input)
            
            # 📊 DEBUG: Log LLM response
            print(f"\n🤖 LLM RESPONSE: {response[:200]}...\n")
            
            # Extract sources for logging (not displayed)
            sources = self._extract_sources(retrieved_docs)
            
            # NO citation in response (cleaner UX per user request)
            # Just return the clean answer
            
            # If condition was detected, add product names to response for context
            # This helps follow-up questions work better
            if condition_result:
                # Save with product mention so context knows what we're talking about
                context_response = f"{response} (Sản phẩm: {', '.join(condition_result['products'])})"
                self.memory.save_context(
                    {"input": question},
                    {"output": context_response}
                )
            else:
                # Regular save
                self.memory.save_context(
                    {"input": question},
                    {"output": response}
                )
            
            return {
                "answer": response,
                "method": "rag_with_safety",
                "sources": sources,  # Keep for backend logging
                "num_sources": len(sources),
                "warning": None
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "answer": "❌ Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại.",
                "method": "error",
                "sources": [],
                "error": str(e)
            }
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        print("🗑️  Đã xóa lịch sử hội thoại")
    
    def _enhance_query_with_context(self, question: str, chat_history: List) -> str:
        """Enhance query with context from chat history for better retrieval.
        
        This solves the problem where "giá bao nhiêu?" doesn't work because
        retriever doesn't know we're asking about a product from previous conversation.
        
        Args:
            question: Current user question
            chat_history: Previous conversation messages
            
        Returns:
            Enhanced query string for retrieval
        """
        # If question is complete (mentions product name), use as-is
        product_names = [
            "fucoidan", "glucan", "kidney", "men's", "power hlp", 
            "reishi", "paracetamol", "agaricus", "mozuku"
        ]
        
        question_lower = question.lower()
        
        # Check if question already has product context
        has_product = any(name in question_lower for name in product_names)
        
        if has_product:
            # Question is complete, no enhancement needed
            return question
        
        # Check if question is vague (asking about price, dosage, etc. without product)
        vague_patterns = [
            "giá", "bao nhiêu", "liều", "dùng", "uống", "viên", "lần",
            "ngày", "hộp", "tác dụng", "công dụng", "nào", "này", "đó", 
            "sản phẩm", "thuốc", "có tốt không", "hiệu quả"
        ]
        
        is_vague = any(pattern in question_lower for pattern in vague_patterns)
        
        if not is_vague:
            # Not a follow-up question, use as-is
            return question
        
        # Question is vague - need to add context from history
        # 🎯 PRIORITY 1: Use tracked current product (most accurate!)
        if self.current_product:
            enhanced = f"{self.current_product} {question}"
            print(f"🔍 Query enhancement (tracked product): '{question}' → '{enhanced}'")
            return enhanced
        
        # 🎯 PRIORITY 2: Search chat history if no tracked product
        if not chat_history or len(chat_history) == 0:
            # No history, can't enhance
            return question
        
        # Extract product mentioned in recent history (last 2 exchanges = 4 messages)
        recent_history = chat_history[-4:] if len(chat_history) >= 4 else chat_history
        
        mentioned_product = None
        for msg in reversed(recent_history):
            msg_content = msg.content if hasattr(msg, 'content') else str(msg)
            msg_lower = msg_content.lower()
            
            # Find product name in message (look for most specific first)
            if "kidney" in msg_lower and "men" in msg_lower:
                mentioned_product = "Kidney & Men's"
            elif "the fucoidan xk" in msg_lower or "fucoidan xk" in msg_lower:
                mentioned_product = "The Fucoidan xK"
            elif "the fucoidan" in msg_lower or ("fucoidan" in msg_lower and "the" in msg_lower):
                mentioned_product = "The Fucoidan"
            elif "glucan" in msg_lower:
                mentioned_product = "β-Glucan Ball"
            elif "power hlp" in msg_lower or "power" in msg_lower:
                mentioned_product = "Power HLP"
            elif "reishi" in msg_lower:
                mentioned_product = "The Reishi"
            elif "paracetamol" in msg_lower:
                mentioned_product = "Paracetamol"
            
            if mentioned_product:
                break
        
        if mentioned_product:
            # Enhance query with product context
            enhanced = f"{mentioned_product} {question}"
            print(f"🔍 Query enhancement (from history): '{question}' → '{enhanced}'")
            return enhanced
        else:
            # No product found in history
            return question
    
    def _classify_question_safety(self, question: str) -> Dict[str, Any]:
        """Classify question safety - block medical diagnosis/prescription questions.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with is_safe, message, reason
        """
        question_lower = question.lower()
        
        # 🚨 BLOCK 1: Medical diagnosis questions
        diagnosis_keywords = [
            "bị", "mắc", "triệu chứng", "dấu hiệu", "đau", "sốt", "ho", "khó thở",
            "chảy máu", "sưng", "ngứa", "phát ban", "viêm", "nhiễm trùng",
            "chẩn đoán", "bệnh gì", "có phải", "tôi có", "con tôi", "mẹ tôi"
        ]
        
        diagnosis_patterns = [
            "nên uống thuốc gì", "uống thuốc nào", "dùng thuốc nào", 
            "có nên dùng", "có nên uống", "tôi có thể",
            "được phép", "khỏi bệnh", "chữa được không"
        ]
        
        # Check diagnosis keywords
        for keyword in diagnosis_keywords:
            if keyword in question_lower:
                for pattern in diagnosis_patterns:
                    if pattern in question_lower:
                        return {
                            "is_safe": False,
                            "message": (
                                "⚠️ TÔI KHÔNG THỂ ĐƯA RA CHỈ ĐỊNH Y TẾ\n\n"
                                "Câu hỏi của bạn liên quan đến chẩn đoán hoặc chỉ định điều trị. "
                                "Đây là việc chỉ bác sĩ hoặc dược sĩ mới có thể làm.\n\n"
                                "🏥 Vui lòng:\n"
                                "- Tham khảo ý kiến bác sĩ\n"
                                "- Đến nhà thuốc gặp dược sĩ\n"
                                "- Gọi đường dây tư vấn y tế\n\n"
                                "💡 Tôi chỉ có thể cung cấp THÔNG TIN về các sản phẩm có sẵn, "
                                "không thay thế tư vấn y tế chuyên môn."
                            ),
                            "reason": "medical_diagnosis_blocked"
                        }
        
        # 🚨 BLOCK 2: Prescription/dosage questions without context
        prescription_alone = [
            "cho tôi", "bán cho", "mua được không", "liều lượng bao nhiêu",
            "uống mấy viên", "ngày mấy lần", "khi nào uống"
        ]
        
        # These are OK if asking about specific product, but dangerous if general
        has_product_context = any([
            "fucoidan" in question_lower,
            "glucan" in question_lower,
            "kidney" in question_lower,
            "power hlp" in question_lower,
            "reishi" in question_lower,
            "paracetamol" in question_lower
        ])
        
        for pattern in prescription_alone:
            if pattern in question_lower and not has_product_context:
                # If asking about dosage but no specific product mentioned
                if any(word in pattern for word in ["liều", "viên", "lần", "uống"]):
                    return {
                        "is_safe": False,
                        "message": (
                            "⚠️ CẢNH BÁO AN TOÀN\n\n"
                            "Tôi cần biết BẠN ĐANG HỎI VỀ SẢN PHẨM NÀO để cung cấp thông tin liều dùng.\n\n"
                            "Vui lòng nêu rõ tên sản phẩm, ví dụ:\n"
                            "- 'Liều dùng của The Fucoidan là gì?'\n"
                            "- 'Paracetamol uống như thế nào?'\n\n"
                            "⚠️ QUAN TRỌNG: Mọi thông tin về liều dùng chỉ mang tính tham khảo. "
                            "Vui lòng đọc kỹ hướng dẫn sử dụng hoặc tham khảo dược sĩ."
                        ),
                        "reason": "dosage_without_product_context"
                    }
        
        # ✅ Question is safe - can proceed with RAG
        return {
            "is_safe": True,
            "message": None,
            "reason": None
        }
    
    def _extract_sources(self, documents: List) -> List[Dict[str, str]]:
        """Extract source information from retrieved documents.
        
        Args:
            documents: List of retrieved Document objects
            
        Returns:
            List of source dictionaries
        """
        sources = []
        seen_products = set()
        
        for doc in documents:
            product_name = doc.metadata.get('product_name', 'Unknown')
            source_file = doc.metadata.get('source', 'traning.json')
            
            # Avoid duplicate sources
            if product_name not in seen_products:
                sources.append({
                    'product_name': product_name,
                    'source_file': source_file,
                    'doc_type': doc.metadata.get('type', 'product_info')
                })
                seen_products.add(product_name)
        
        return sources
    
    def _format_citation(self, sources: List[Dict[str, str]]) -> str:
        """Format sources as citation text.
        
        Args:
            sources: List of source dictionaries
            
        Returns:
            Formatted citation string
        """
        if not sources:
            return "\n📚 Nguồn: Không có nguồn tham khảo"
        
        citation = "\n📚 **Nguồn thông tin:**"
        for i, source in enumerate(sources, 1):
            product_name = source['product_name']
            citation += f"\n  {i}. {product_name}"
        
        citation += "\n\n⚠️ **Lưu ý:** Thông tin chỉ mang tính tham khảo. Vui lòng tham khảo ý kiến dược sĩ hoặc bác sĩ trước khi sử dụng."
        
        return citation


# Backward compatibility alias
RetrievalChain = RAGChain

