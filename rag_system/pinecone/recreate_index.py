"""Script to delete and recreate Pinecone index with new document format.

Use this if you've updated the document format in data_loader.py
Loads data from Excel files instead of JSON.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add project root to path
# Get the project root (2 levels up from this file)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

print("\n" + "="*70)
print("🔄 TẠO LẠI PINECONE INDEX (TỪ FILE EXCEL)")
print("="*70)

# Check API key
if not os.getenv("PINECONE_API_KEY"):
    print("❌ Không tìm thấy PINECONE_API_KEY trong .env")
    sys.exit(1)

try:
    from rag_system.pinecone.vector_store import VectorStore
    from rag_system.core.config import EXCEL_DATA_FILES, CHUNK_SIZE, CHUNK_OVERLAP
    from loaders.data_loader import load_multiple_excel_files
    
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
            except Exception as e:
                print(f"⚠️  Lỗi khi xóa index: {e}")
                print("💡 Bạn có thể xóa thủ công tại: https://app.pinecone.io/")
        else:
            print("❌ Hủy bỏ. Index không được thay đổi.")
            sys.exit(0)
    
    # Check Excel files exist
    missing_files = [f for f in EXCEL_DATA_FILES if not f.exists()]
    if missing_files:
        print(f"\n❌ Không tìm thấy các file Excel sau:")
        for f in missing_files:
            print(f"   - {f}")
        sys.exit(1)
    
    print(f"\n📄 Đang đọc dữ liệu từ {len(EXCEL_DATA_FILES)} file Excel:")
    for excel_file in EXCEL_DATA_FILES:
        print(f"   - {excel_file}")
    
    print(f"\n📋 Chỉ lấy dữ liệu cho các sản phẩm được phép:")
    from loaders.data_loader import ALLOWED_PRODUCTS
    for product in ALLOWED_PRODUCTS:
        print(f"   - {product}")
    
    print(f"\n✂️  Chunking documents (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    
    # Load and chunk Excel data
    chunked_documents = load_multiple_excel_files(
        excel_files=[str(f) for f in EXCEL_DATA_FILES],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    if not chunked_documents:
        print("❌ Không trích xuất được dữ liệu từ Excel files")
        sys.exit(1)
    
    print(f"\n✅ Đã tạo {len(chunked_documents)} chunks từ Excel files")
    
    # Create new index
    print(f"\n📤 Đang tạo Pinecone index '{vector_store.index_name}'...")
    print("   Embeddings đang được tạo và upload lên Pinecone...")
    print("   (Quá trình này có thể mất vài phút...)")
    
    vector_store.create_index(chunked_documents)
    
    # Show stats
    stats = vector_store.get_stats()
    print(f"\n📊 Index Statistics:")
    print(f"   Name: {stats.get('index_name', 'N/A')}")
    print(f"   Vectors: {stats.get('total_vectors', 'N/A')}")
    print(f"   Dimension: {stats.get('dimension', 384)}")
    
    print("\n" + "="*70)
    print("🎉 HOÀN TẤT! Index đã được tạo lại với format mới.")
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

