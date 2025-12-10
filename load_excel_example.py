"""Ví dụ script để load dữ liệu từ file Excel và tạo Documents.

Script này sẽ:
1. Load dữ liệu từ traning.xlsx và traning_new.xlsx
2. Trích xuất tên sản phẩm từ cột "Trả lời" 
3. Tạo Documents cho mỗi sản phẩm
4. Hiển thị kết quả
"""

from loaders.data_loader import load_multiple_excel_files

def main():
    print("\n" + "="*70)
    print("📊 LOAD DỮ LIỆU TỪ FILE EXCEL")
    print("="*70)
    
    # Danh sách các file Excel cần load
    excel_files = [
        "data/traning.xlsx",
        "data/traning_new.xlsx"
    ]
    
    print(f"\n📂 Sẽ load {len(excel_files)} file Excel:")
    for file in excel_files:
        print(f"   - {file}")
    
    try:
        # Load và tạo documents từ các file Excel
        # Tên sản phẩm sẽ được tự động trích xuất từ cột "Trả lời"
        documents = load_multiple_excel_files(
            excel_files=excel_files,
            # Để None để tự động phát hiện cột "Trả lời"
            answer_column=None,
            # Chunk size và overlap
            chunk_size=1000,
            chunk_overlap=200
        )
        
        print(f"\n{'='*70}")
        print(f"✅ HOÀN THÀNH")
        print(f"{'='*70}")
        print(f"\n📊 Tổng số Documents đã tạo: {len(documents)}")
        
        # Hiển thị một vài ví dụ
        print(f"\n📋 Ví dụ Documents (hiển thị 3 đầu tiên):")
        print("-" * 70)
        
        for i, doc in enumerate(documents[:3], 1):
            print(f"\n📄 Document {i}:")
            print(f"   Tên sản phẩm: {doc.metadata.get('product_name', 'N/A')}")
            print(f"   Nguồn: {doc.metadata.get('source', 'N/A')}")
            print(f"   Độ dài nội dung: {len(doc.page_content)} ký tự")
            print(f"   Nội dung (100 ký tự đầu): {doc.page_content[:100]}...")
        
        if len(documents) > 3:
            print(f"\n   ... và {len(documents) - 3} documents khác")
        
        print(f"\n{'='*70}")
        print("💡 Bạn có thể sử dụng các documents này để:")
        print("   - Upload lên Pinecone vector store")
        print("   - Sử dụng trong RAG system")
        print("   - Tìm kiếm semantic")
        print(f"{'='*70}\n")
        
        return documents
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    documents = main()

