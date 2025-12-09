"""Streamlit UI cho Vietnamese Chatbot với Google Gemini AI."""

# Fix Pinecone deprecated plugin error - MUST be before any imports
import os
os.environ.setdefault("PINECONE_DISABLE_DEPRECATED_PLUGIN_CHECK", "1")

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from vietnamese_chatbot import VietnameseChatbot


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


def initialize_session_state():
    """Initialize session state variables."""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_started' not in st.session_state:
        st.session_state.chat_started = False
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False


def display_message(message: dict, index: int):
    """Display a chat message."""
    role = message['role']
    content = message['content']
    
    with st.chat_message(role):
        st.write(content)
        
        # Show method indicator (removed sources display)
        if role == "assistant":
            method = message.get('method', '')
            doc_count = message.get('doc_count', 0)
            
            if method == 'direct':
                st.caption("💡 Sử dụng kiến thức chung")


def main():
    """Main Streamlit app."""
    initialize_session_state()
    
    # Auto-initialize chatbot
    if not st.session_state.initialized:
        with st.spinner("🤖 Đang khởi tạo chatbot..."):
            try:
                st.session_state.chatbot = VietnameseChatbot()
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Lỗi khởi tạo: {str(e)}")
                st.info("💡 Vui lòng kiểm tra file .env và API key")
                st.stop()
    
    # Header
    st.markdown("""
    <div class="header-container">
        <h1>🇻🇳 Chatbot AI Tiếng Việt</h1>
        <p>Powered by Groq AI & Local Embeddings</p>
    </div>
    """, unsafe_allow_html=True)
    
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
                        response = st.session_state.chatbot.chat(prompt)
                        answer = response.get('answer', '')
                        
                        # Display response
                        st.write(answer)
                        
                        # Add assistant message to session state
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "timestamp": datetime.now().isoformat(),
                            "method": response.get('method', 'rag')
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

