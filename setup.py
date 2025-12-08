"""Setup script - Trích xuất dữ liệu và tạo vector index."""

import os
import sys
from pathlib import Path

print("\n" + "="*70)
print("📦 CÀI ĐẶT CHATBOT TIẾNG VIỆT - GROQ AI")
print("="*70)

# Step 1: Check libraries
print("\n[1/3] Kiểm tra thư viện...")
try:
    import groq
    import pinecone
    import json  # For JSON loading
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

if not os.getenv("PINECONE_API_KEY"):
    print("❌ Không tìm thấy PINECONE_API_KEY")
    print("\n💡 Thêm vào file .env:")
    print("PINECONE_API_KEY=your-pinecone-api-key")
    print("\n🔑 Lấy API key miễn phí tại: https://app.pinecone.io/")
    sys.exit(1)
else:
    print("✅ PINECONE_API_KEY OK")

# Step 3: Create Pinecone index from JSON file with chunking
print("\n[3/3] Tạo Pinecone index từ JSON (với Chunking)...")
print("   Flow: JSON Data → Chunking → Embeddings → Pinecone Index")
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
    
    # Create Pinecone vector store
    print("📦 Đang kết nối với Pinecone...")
    vector_store = VectorStore("vietnamese_support")
    
    # Check if index exists and has vectors
    if vector_store.index_exists():
        try:
            stats = vector_store.get_stats()
            vector_count = stats.get('total_vectors', 0)
            
            if vector_count > 0:
                print(f"✅ Pinecone index '{vector_store.index_name}' đã tồn tại với {vector_count} vectors")
                print("💡 Đang tải index hiện có...")
                vector_store.load_index()
            else:
                print(f"📤 Index tồn tại nhưng chưa có vectors, đang upload chunks...")
                print("   Embeddings đang được tạo và upload lên Pinecone...")
                vector_store.create_index(chunked_documents)
        except Exception as e:
            print(f"⚠️  Không thể kiểm tra stats, đang tạo index mới...")
            vector_store.create_index(chunked_documents)
    else:
        print(f"📤 Đang tạo Pinecone index '{vector_store.index_name}'...")
        print("   Embeddings đang được tạo và upload lên Pinecone...")
        vector_store.create_index(chunked_documents)
        print("✅ Pinecone index đã được tạo và sẵn sàng!")
    
    # Show stats
    stats = vector_store.get_stats()
    print(f"\n📊 Index Statistics:")
    print(f"   Name: {stats.get('index_name', 'N/A')}")
    print(f"   Vectors: {stats.get('total_vectors', 'N/A')}")
    print(f"   Dimension: {stats.get('dimension', 384)}")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Troubleshooting:")
    print("   1. Kiểm tra PINECONE_API_KEY trong .env")
    print("   2. Kiểm tra kết nối internet")
    print("   3. Xem PINECONE_MIGRATION.md để biết thêm")
    sys.exit(1)

# Success
print("\n" + "="*70)
print("🎉 CÀI ĐẶT HOÀN TẤT!")
print("="*70)
print("\n📝 Cách sử dụng:")
print("   python vietnamese_chatbot.py")
print("\n" + "="*70)
