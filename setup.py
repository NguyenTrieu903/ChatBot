"""Setup script - Trích xuất dữ liệu và tạo ChromaDB vector index."""

import os
import sys
from pathlib import Path

print("\n" + "="*70)
print("📦 CÀI ĐẶT CHATBOT Y TẾ TIẾNG VIỆT - CHROMADB + GROQ AI")
print("="*70)

# Step 1: Check libraries
print("\n[1/3] Kiểm tra thư viện...")
try:
    import groq
    import chromadb
    import json  # For JSON loading
    from sentence_transformers import SentenceTransformer
    print("✅ Thư viện OK")
except ImportError as e:
    print(f"❌ Thiếu thư viện: {e}")
    print("\n💡 Cài đặt: pip install -r requirements.txt")
    sys.exit(1)

# Step 2: Check .env
print("\n[2/3] Kiểm tra file .env...")
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    print("❌ Không tìm thấy GROQ_API_KEY")
    print("\n💡 Tạo file .env với nội dung:")
    print("GROQ_API_KEY=your-api-key-here")
    print("\n🔑 Lấy API key miễn phí tại: https://console.groq.com/keys")
    sys.exit(1)
else:
    print("✅ GROQ_API_KEY OK")

print("\n💡 ChromaDB không cần API key - hoàn toàn miễn phí và local!")

# Step 3: Create ChromaDB collection from JSON file with chunking
print("\n[3/3] Tạo ChromaDB collection từ JSON (với Chunking)...")
print("   Flow: JSON Data → Chunking → Embeddings → ChromaDB Collection")
print("   🆓 ChromaDB: Local vector database - no API key needed!")
try:
    from rag_system.vector_store import VectorStore
    from data_loader import load_and_chunk_json
    
    json_file = "data/traning.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Không tìm thấy: {json_file}")
        sys.exit(1)
    
    # Load JSON and chunk documents
    print("📄 Đọc dữ liệu từ JSON...")
    print("✂️  Chunking documents (chunk_size=1000, overlap=200)...")
    chunked_documents = load_and_chunk_json(
        json_file,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    if not chunked_documents:
        print("❌ Không trích xuất được dữ liệu")
        sys.exit(1)
    
    print(f"✅ Đã tạo {len(chunked_documents)} chunks từ JSON")
    
    # Create ChromaDB vector store
    print("\n📦 Đang khởi tạo ChromaDB (local vector database)...")
    print("   Lần đầu sẽ tải embedding model (~1.5GB)...")
    vector_store = VectorStore("vietnamese_support")
    
    # Check if collection exists and has documents
    if vector_store.index_exists():
        try:
            stats = vector_store.get_stats()
            doc_count = stats.get('total_documents', 0)
            
            if doc_count > 0:
                print(f"✅ ChromaDB collection '{vector_store.collection_name}' đã tồn tại với {doc_count} documents")
                print("💡 Đang tải collection hiện có...")
                vector_store.load_index()
            else:
                print(f"📤 Collection tồn tại nhưng chưa có documents, đang thêm chunks...")
                print("   Embeddings đang được tạo và lưu vào ChromaDB...")
                vector_store.create_index(chunked_documents)
        except Exception as e:
            print(f"⚠️  Không thể kiểm tra stats, đang tạo collection mới...")
            vector_store.create_index(chunked_documents)
    else:
        print(f"📤 Đang tạo ChromaDB collection '{vector_store.collection_name}'...")
        print("   Embeddings đang được tạo và lưu vào ChromaDB (local)...")
        vector_store.create_index(chunked_documents)
        print("✅ ChromaDB collection đã được tạo và sẵn sàng!")
    
    # Show stats
    stats = vector_store.get_stats()
    print(f"\n📊 Collection Statistics:")
    print(f"   Name: {stats.get('collection_name', 'N/A')}")
    print(f"   Documents: {stats.get('total_documents', 'N/A')}")
    print(f"   Dimension: {stats.get('dimension', 1024)}")
    print(f"   Model: {stats.get('embedding_model', 'N/A')}")
    print(f"   Location: {stats.get('persist_directory', 'N/A')}")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Troubleshooting:")
    print("   1. Kiểm tra GROQ_API_KEY trong .env")
    print("   2. Đảm bảo có đủ dung lượng (~2GB cho embedding model)")
    print("   3. Chạy lại: python setup.py")
    sys.exit(1)

# Success
print("\n" + "="*70)
print("🎉 CÀI ĐẶT HOÀN TẤT!")
print("="*70)
print("\n📝 Cách sử dụng:")
print("   🎨 Web UI:   streamlit run app.py")
print("   💻 Terminal: python vietnamese_chatbot.py")
print("\n💡 Ưu điểm ChromaDB:")
print("   ✅ Hoàn toàn miễn phí - không cần API key")
print("   ✅ Chạy local - dữ liệu an toàn")
print("   ✅ Không giới hạn số lượng vector")
print("   ✅ Tốc độ nhanh với dữ liệu nhỏ-trung bình")
print("\n" + "="*70)
