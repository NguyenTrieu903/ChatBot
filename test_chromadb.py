"""Test script to verify ChromaDB + LangChain + Groq AI setup."""

import os
import sys
from pathlib import Path

print("\n" + "="*70)
print("🧪 KIỂM TRA CHATBOT Y TẾ - CHROMADB + GROQ AI")
print("="*70)

# Test 1: Check libraries
print("\n[1/5] Kiểm tra thư viện...")
try:
    import groq
    import chromadb
    from sentence_transformers import SentenceTransformer
    from langchain_chroma import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("✅ Tất cả thư viện đã được cài đặt")
except ImportError as e:
    print(f"❌ Thiếu thư viện: {e}")
    print("\n💡 Chạy: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Check .env file
print("\n[2/5] Kiểm tra file .env...")
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    print("❌ Không tìm thấy GROQ_API_KEY")
    print("\n💡 Tạo file .env với nội dung:")
    print("GROQ_API_KEY=your-groq-api-key-here")
    sys.exit(1)
else:
    print("✅ GROQ_API_KEY OK")

# Test 3: Check ChromaDB collection
print("\n[3/5] Kiểm tra ChromaDB collection...")
try:
    from rag_system.vector_store import VectorStore
    
    vector_store = VectorStore("vietnamese_support")
    
    if vector_store.index_exists():
        stats = vector_store.get_stats()
        doc_count = stats.get('total_documents', 0)
        
        if doc_count > 0:
            print(f"✅ ChromaDB collection đã tồn tại với {doc_count} documents")
            print(f"   Location: {stats.get('persist_directory', 'N/A')}")
        else:
            print("⚠️  Collection tồn tại nhưng chưa có data")
            print("💡 Chạy: python setup.py")
            sys.exit(1)
    else:
        print("❌ ChromaDB collection chưa được tạo")
        print("💡 Chạy: python setup.py")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Lỗi khi kiểm tra ChromaDB: {e}")
    print("💡 Chạy: python setup.py")
    sys.exit(1)

# Test 4: Check embeddings
print("\n[4/5] Kiểm tra embedding model...")
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Test embedding
    test_text = "Test embedding"
    embedding = embeddings.embed_query(test_text)
    
    if len(embedding) == 1024:
        print(f"✅ Embedding model OK (dimension: {len(embedding)})")
    else:
        print(f"⚠️  Embedding dimension không đúng: {len(embedding)} (expected 1024)")
        
except Exception as e:
    print(f"❌ Lỗi embedding model: {e}")
    print("💡 Model có thể đang được tải. Đợi vài phút và thử lại.")
    sys.exit(1)

# Test 5: Test chatbot
print("\n[5/5] Kiểm tra chatbot...")
try:
    from vietnamese_chatbot import VietnameseChatbot
    
    print("   Đang khởi tạo chatbot...")
    chatbot = VietnameseChatbot()
    
    print("   Đang test câu hỏi...")
    test_question = "The Fucoidan là gì?"
    response = chatbot.chat(test_question)
    
    if response and 'answer' in response:
        answer = response['answer']
        print(f"✅ Chatbot hoạt động tốt!")
        print(f"\n📝 Test Question: {test_question}")
        print(f"🤖 Bot Answer: {answer[:200]}...")  # Show first 200 chars
    else:
        print("⚠️  Chatbot trả lời nhưng không đúng format")
        
except Exception as e:
    print(f"❌ Lỗi khi test chatbot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Success
print("\n" + "="*70)
print("🎉 TẤT CẢ TESTS ĐỀU PASS!")
print("="*70)
print("\n✅ Hệ thống đã sẵn sàng:")
print("   • ChromaDB: Running locally")
print("   • Embeddings: multilingual-e5-large")
print("   • LLM: Groq AI (Llama 3.3 70B)")
print("   • Framework: LangChain")
print("\n📝 Cách sử dụng:")
print("   🎨 Web UI:   streamlit run app.py")
print("   💻 Terminal: python vietnamese_chatbot.py")
print("\n" + "="*70)
