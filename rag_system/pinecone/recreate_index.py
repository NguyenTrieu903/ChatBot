"""Script to delete and recreate Pinecone index with new document format.

Use this if you've updated the document format in data_loader.py
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv()

print("\n" + "="*70)
print("🔄 TẠO LẠI PINECONE INDEX")
print("="*70)

# Check API key
if not os.getenv("PINECONE_API_KEY"):
    print("❌ Không tìm thấy PINECONE_API_KEY trong .env")
    sys.exit(1)

try:
    from rag_system.pinecone.vector_store import VectorStore
    from loaders.data_loader import load_and_chunk_json
    from rag_system.core.config import CHUNK_SIZE, CHUNK_OVERLAP
    
    # Initialize vector store
    vector_store = VectorStore("vietnamese_support")
    
    # Check if index exists
    if vector_store.index_exists():
        print(f"\n⚠️  Index '{vector_store.index_name}' đã tồn tại")
        response = input("Bạn có muốn XÓA index cũ và tạo lại? (yes/no): ")
        
        if response.lower() in ['yes', 'y', 'có', 'c']:
            print(f"\n🗑️  Đang xóa index '{vector_store.index_name}'...")
            try:
                vector_store.delete_index()
                print("✅ Đã xóa index cũ")
                print("⏳ Đợi 10 giây để Pinecone hoàn tất việc xóa index...")
                import time
                time.sleep(10)  # Đợi Pinecone xóa index hoàn toàn
                print("✅ Sẵn sàng tạo index mới")
            except Exception as e:
                print(f"⚠️  Lỗi khi xóa index: {e}")
                print("💡 Bạn có thể xóa thủ công tại: https://app.pinecone.io/")
                sys.exit(1)
        else:
            print("❌ Hủy bỏ. Index không được thay đổi.")
            sys.exit(0)
    
    # Load JSON data WITHOUT chunking - each product = 1 document
    json_file = "data/traning.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Không tìm thấy: {json_file}")
        sys.exit(1)
    
    print(f"\n📄 Đang đọc dữ liệu từ {json_file}...")
    print(f"📦 Loading và chunking documents...")
    print(f"   Chunk size: {CHUNK_SIZE}, Overlap: {CHUNK_OVERLAP}")
    
    chunked_documents = load_and_chunk_json(
        json_file,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    if not chunked_documents:
        print("❌ Không trích xuất được dữ liệu")
        sys.exit(1)
    
    print(f"✅ Đã tạo {len(chunked_documents)} chunks từ JSON")
    
    # Verify chunk distribution by product
    print(f"\n📋 Phân bố chunks theo sản phẩm:")
    product_chunks = {}
    for doc in chunked_documents:
        product_name = doc.metadata.get('product_name', 'Unknown')
        if product_name not in product_chunks:
            product_chunks[product_name] = 0
        product_chunks[product_name] += 1
    
    for product_name, count in product_chunks.items():
        print(f"   • {product_name}: {count} chunks")
    
    # Create new index
    print(f"\n📤 Đang tạo Pinecone index '{vector_store.index_name}'...")
    print("   Embeddings đang được tạo và upload lên Pinecone...")
    print("   (Quá trình này có thể mất vài phút...)")
    
    vector_store.create_index(chunked_documents)
    
    # Show stats
    stats = vector_store.get_stats()
    print(f"\n📊 Index Statistics:")
    print(f"   Name: {stats.get('index_name', 'N/A')}")
    print(f"   Vectors: {stats.get('total_vectors', 'N/A')} (mong đợi: ~{len(chunked_documents)})")
    print(f"   Dimension: {stats.get('dimension', 1024)}")
    
    print("\n" + "="*70)
    print("🎉 HOÀN TẤT! Index đã được tạo lại với chunking tối ưu.")
    print(f"   Tổng: {len(chunked_documents)} chunks (vectors)")
    print(f"   Mỗi chunk chứa ~{CHUNK_SIZE} ký tự với overlap {CHUNK_OVERLAP}")
    print("="*70)
    print("\n💡 Bây giờ bạn có thể chạy chatbot:")
    print("   python main.py")
    print("   hoặc")
    print("   streamlit run app.py")
    
except Exception as e:
    print(f"\n❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

