"""Vietnamese Chatbot with Groq AI and Pinecone RAG.

This module provides a high-level interface for the Vietnamese chatbot
using RAG (Retrieval-Augmented Generation) with Groq AI and Pinecone.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_system.retrieval_chain import RetrievalChain
from rag_system.core.config import DEFAULT_USE_CASE, MEMORY_WINDOW_SIZE, validate_config
from rag_system.core.logger import get_logger
from rag_system.core.exceptions import ConfigurationError

logger = get_logger(__name__)


class ChatBot:
    """Chatbot with RAG capabilities.
    
    Uses Groq AI for LLM inference and Pinecone for vector storage.
    Memory is managed by ConversationBufferWindowMemory.
    """
    
    def __init__(self, use_case: str = DEFAULT_USE_CASE):
        """Initialize chatbot.
        
        Args:
            use_case: Use case identifier for vector store
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        try:
            validate_config()
            logger.info("Initializing Vietnamese chatbot...")
            
            self.retrieval_chain = RetrievalChain(
                use_case=use_case,
                memory_window_size=MEMORY_WINDOW_SIZE
            )
            
            logger.info("Chatbot ready")
            logger.info(f"Using ConversationBufferWindowMemory (k={MEMORY_WINDOW_SIZE})")
            
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            raise ConfigurationError(f"Chatbot initialization failed: {e}") from e
    
    def chat(self, user_message: str) -> dict:
        """Chat with user.
        
        Args:
            user_message: User's message
            
        Returns:
            Response dictionary with answer
        """
        return self.retrieval_chain.chat(user_message)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.retrieval_chain.clear_memory()
        logger.info("Conversation history cleared")


def interactive_chat() -> int:
    """Interactive chat mode for command line.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("\n" + "="*70)
    print("🇻🇳  CHATBOT AI TIẾNG VIỆT - GROQ AI (FREE & FAST!)")
    print("="*70)
    print("\nLệnh:")
    print("  • Gõ 'thoát' hoặc 'exit' để kết thúc")
    print("  • Gõ 'xóa' hoặc 'clear' để xóa lịch sử")
    print("-"*70 + "\n")
    
    try:
        chatbot = ChatBot()
        
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
                logger.error(f"Error in chat loop: {e}")
                print(f"\n❌ Lỗi: {str(e)}")
    
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        print(f"\n❌ Lỗi khởi tạo: {str(e)}")
        print("\n💡 Hướng dẫn:")
        print("1. Tạo file .env với GROQ_API_KEY và PINECONE_API_KEY")
        print("2. Chạy: pip install -r requirements.txt")
        print("3. Chạy: python setup.py")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = interactive_chat()
    sys.exit(exit_code)

