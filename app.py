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

from rag_system.rag_chain import RAGChain
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


@st.cache_resource
def auto_initialize_chromadb():
    """Auto-initialize ChromaDB if not exists. Cached to avoid reloading on each session."""
    from rag_system.vector_store import VectorStore
    from data_loader import load_and_chunk_json
    
    # Check if ChromaDB already exists
    vector_store = VectorStore("vietnamese_support")
    
    if not vector_store.index_exists():
        st.info("📥 ChromaDB not found. Please run initialization script first.")
        st.info("💡 Run: python -c \"from app import auto_initialize_chromadb; auto_initialize_chromadb()\"")
        return False
    
    # Load existing index
    try:
        vector_store.load_index()
        stats = vector_store.get_stats()
        doc_count = stats.get('total_documents', 0)
        if doc_count == 0:
            st.warning("⚠️ ChromaDB exists but is empty. Please reinitialize.")
            return False
        return True
    except Exception as e:
        st.error(f"❌ Error loading ChromaDB: {str(e)}")
        return False


@st.cache_resource
def get_rag_chain():
    """Get or create RAG chain. Cached to avoid reloading model on each session."""
    return RAGChain(use_case="vietnamese_support", k=5)


def initialize_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []


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
    
    # Initialize ChromaDB (cached - runs once across all sessions)
    if not auto_initialize_chromadb():
        st.stop()
    
    # Get RAG chain (cached - model loaded once across all sessions)
    rag_chain = get_rag_chain()
    
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
                    response = rag_chain.chat(prompt)
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

