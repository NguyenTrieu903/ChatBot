"""Vietnamese Chatbot with Google Gemini AI (Free)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from rag_system.retrieval_chain import RetrievalChain
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()


class VietnameseChatbot:
    """Chatbot AI tiếng Việt sử dụng Groq AI với LangChain native chat history.
    
    Theo best practices từ:
    - https://realpython.com/build-llm-rag-chatbot-with-langchain/
    - https://docs.langchain.com/oss/python/langchain/rag#pinecone
    """
    
    def __init__(self):
        """Khởi tạo chatbot."""
        print("🤖 Đang khởi tạo chatbot với Groq AI...")
        
        # Check API key
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError(
                "❌ Không tìm thấy GROQ_API_KEY!\n"
                "   Vui lòng tạo file .env với:\n"
                "   GROQ_API_KEY=your-api-key\n"
                "   Lấy API key miễn phí tại: https://console.groq.com/keys"
            )
        
        self.retrieval_chain = RetrievalChain(use_case="vietnamese_support", k=5)
        
        # Memory is now managed by ConversationBufferWindowMemory in RAGChain
        # No need to manually manage chat_history
        
        print("✅ Chatbot đã sẵn sàng!")
        print("💾 Sử dụng ConversationBufferWindowMemory (k=5 exchanges)")
    
    def chat(self, user_message: str) -> dict:
        """Chat with user.
        
        Memory is automatically managed by ConversationBufferWindowMemory in RAGChain.
        
        Args:
            user_message: User's message
            
        Returns:
            Response dictionary with answer
        """
        # Get response from RAG chain
        # Memory will be automatically loaded and saved inside RAGChain.chat()
        response = self.retrieval_chain.chat(user_message)
        
        return response
    
    def clear_history(self):
        """Xóa lịch sử hội thoại."""
        self.retrieval_chain.clear_memory()


def interactive_chat():
    """Chế độ chat tương tác."""
    print("\n" + "="*70)
    print("🇻🇳  CHATBOT AI TIẾNG VIỆT - GROQ AI (FREE & FAST!)")
    print("="*70)
    print("\nLệnh:")
    print("  • Gõ 'thoát' hoặc 'exit' để kết thúc")
    print("  • Gõ 'xóa' hoặc 'clear' để xóa lịch sử")
    print("-"*70 + "\n")
    
    try:
        # Initialize chatbot
        chatbot = VietnameseChatbot()
        
        # Main loop
        while True:
            try:
                user_input = input("\n👤 Bạn: ").strip()
                
                if not user_input:
                    continue
                
                # Exit commands
                if user_input.lower() in ['thoát', 'exit', 'quit', 'q']:
                    print("\n👋 Tạm biệt!")
                    break
                
                # Clear commands
                if user_input.lower() in ['xóa', 'clear']:
                    chatbot.clear_history()
                    continue
                
                # Get response
                print("\n🤖 Bot: ", end="", flush=True)
                response = chatbot.chat(user_input)
                print(response['answer'])
 
                
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {str(e)}")
    
    except Exception as e:
        print(f"\n❌ Lỗi khởi tạo: {str(e)}")
        print("\n💡 Hướng dẫn:")
        print("1. Tạo file .env với GEMINI_API_KEY")
        print("2. Chạy: pip install -r requirements.txt")
        print("3. Chạy: python setup.py")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = interactive_chat()
    sys.exit(exit_code)
