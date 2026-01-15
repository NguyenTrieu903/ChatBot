"""Streamlit UI cho Vietnamese Medical Chatbot với ChromaDB + Groq AI.

Auto-initializes ChromaDB on first run - no setup.py needed!
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv()

from rag_system.retrieval_chain import RetrievalChain
from langchain_core.messages import HumanMessage, AIMessage


# Page config
st.set_page_config(
    page_title="Chatbot AI Tiếng Việt",
    page_icon="🇻🇳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #f5f7fa;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* User message */
    [data-testid="stChatMessageContent"] {
        background-color: #e3f2fd;
    }
    
    /* Header */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 500;
    }
    
    /* Stats */
    .stat-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_environment():
    """Check if environment is properly configured."""
    if not os.getenv("GROQ_API_KEY"):
        st.error("❌ GROQ_API_KEY not found in .env file!")
        st.info("""
        **Setup Instructions:**
        1. Get a free API key from: https://console.groq.com/keys
        2. Create a `.env` file in the AI_Master_Hackathon folder
        3. Add this line: `GROQ_API_KEY=your-api-key-here`
        4. Restart the app
        """)
        st.stop()
        return False
    return True


def auto_initialize_chromadb():
    """Auto-initialize ChromaDB if not exists."""
    from rag_system.vector_store import VectorStore
    from data_loader import load_and_chunk_json
    
    # Check if ChromaDB already exists
    vector_store = VectorStore("vietnamese_support")
    
    if not vector_store.index_exists():
        with st.spinner("🔧 First time setup: Initializing ChromaDB... (this may take a few minutes)"):
            st.info("📥 Downloading embedding model and creating vector database...")
            
            # Load and chunk data
            json_file = "data/traning.json"
            if not os.path.exists(json_file):
                st.error(f"❌ Training data not found: {json_file}")
                st.stop()
                return False
            
            try:
                chunked_documents = load_and_chunk_json(json_file, chunk_size=1000, chunk_overlap=200)
                vector_store.create_index(chunked_documents)
                st.success("✅ ChromaDB initialized successfully!")
                return True
            except Exception as e:
                st.error(f"❌ Error initializing ChromaDB: {str(e)}")
                st.stop()
                return False
    else:
        # Load existing index
        try:
            vector_store.load_index()
            stats = vector_store.get_stats()
            doc_count = stats.get('total_documents', 0)
            if doc_count == 0:
                st.warning("⚠️ ChromaDB exists but is empty. Reinitializing...")
                return auto_initialize_chromadb()
            return True
        except Exception as e:
            st.error(f"❌ Error loading ChromaDB: {str(e)}")
            st.stop()
            return False


def initialize_session_state():
    """Initialize session state variables."""
    if 'rag_chain' not in st.session_state:
        st.session_state.rag_chain = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False


def display_message(message: dict, index: int):
    """Display a chat message without sources (cleaner UI)."""
    role = message['role']
    content = message['content']
    
    with st.chat_message(role):
        st.write(content)


def main():
    """Main Streamlit app."""
    initialize_session_state()
    
    # Check environment configuration
    if not check_environment():
        return
    
    # Auto-initialize ChromaDB (first time only)
    if not st.session_state.initialized:
        auto_initialize_chromadb()
        
        # Initialize RAG chain
        with st.spinner("🤖 Initializing chatbot..."):
            try:
                st.session_state.rag_chain = RetrievalChain(use_case="vietnamese_support", k=5)
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Error initializing chatbot: {str(e)}")
                st.info("💡 Please check your .env file and API key")
                st.stop()
    
    # Header
    st.markdown("""
    <div class="header-container">
        <h1>🏥 Chatbot Y Tế Tiếng Việt</h1>
        <p>Powered by ChromaDB + LangChain + Groq AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Safety Warning Banner
    st.info("""
    ⚠️ **LƯU Ý QUAN TRỌNG VỀ AN TOÀN Y TẾ:**
    
    - ✅ Chatbot này CHỈ cung cấp **thông tin về sản phẩm** từ cơ sở dữ liệu
    - ❌ KHÔNG thay thế tư vấn y tế chuyên môn từ bác sĩ/dược sĩ
    - ❌ KHÔNG đưa ra chẩn đoán bệnh hoặc chỉ định điều trị
    - ✅ Mọi thông tin đều được **trích dẫn nguồn** và **kiểm tra độ chính xác**
    - 🔒 Hệ thống có các lớp bảo vệ an toàn để tránh thông tin sai lệch
    
    💡 **Luôn tham khảo ý kiến chuyên gia y tế trước khi sử dụng bất kỳ sản phẩm nào!**
    """, icon="⚠️")
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        display_message(message, idx)
    
    # Chat input
    if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ..."):
                try:
                    response = st.session_state.rag_chain.chat(prompt)
                    answer = response.get('answer', '')
                    
                    # Display response (clean, no sources)
                    st.write(answer)
                    
                    # Add assistant message to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    error_msg = f"Xin lỗi, đã xảy ra lỗi: {str(e)}"
                    st.error(error_msg)
                    # Add error message to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat(),
                        "error": True
                    })


if __name__ == "__main__":
    main()

