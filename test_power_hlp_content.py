"""Script test để xem nội dung trả về cho sản phẩm Power HLP."""

from loaders.data_loader import extract_product_name_from_text, excel_to_documents, load_excel_data
import pandas as pd

# Ví dụ text từ cột "Trả lời" trong Excel cho sản phẩm Power HLP
example_text = """Power HLP
Chứa các thành phần quý hiếm từ Nhật Bản
Công dụng: Hỗ trợ sức khỏe, tăng cường miễn dịch
Liều dùng: 2 viên/ngày, sau ăn
Giá: 1.500.000 VNĐ
Hộp 60 viên"""

print("="*70)
print("VÍ DỤ: Xử lý text từ cột 'Trả lời' cho sản phẩm Power HLP")
print("="*70)

print("\n📝 Text gốc từ cột 'Trả lời':")
print("-" * 70)
print(example_text)
print("-" * 70)

# Test hàm extract_product_name_from_text
product_name, content_text = extract_product_name_from_text(example_text)

print(f"\n✅ Kết quả trích xuất:")
print(f"   Tên sản phẩm: {product_name}")
print(f"\n   Nội dung (content_text):")
print("-" * 70)
print(content_text)
print("-" * 70)

# Tạo document giả để xem format cuối cùng
if product_name and content_text:
    from langchain_core.documents import Document
    
    # Format giống như trong excel_to_documents
    final_content = f"""Tên sản phẩm: {product_name}

{content_text}"""
    
    doc = Document(
        page_content=final_content,
        metadata={
            'source': 'traning.xlsx',
            'product_name': product_name,
            'type': 'product_answer'
        }
    )
    
    print(f"\n📄 Document cuối cùng (page_content):")
    print("="*70)
    print(doc.page_content)
    print("="*70)
    
    print(f"\n📊 Metadata:")
    print(f"   - product_name: {doc.metadata['product_name']}")
    print(f"   - source: {doc.metadata['source']}")
    print(f"   - type: {doc.metadata['type']}")

print("\n" + "="*70)
print("💡 LƯU Ý:")
print("   - content_text chứa TOÀN BỘ nội dung từ cột 'Trả lời'")
print("   - Bao gồm cả tên sản phẩm ở đầu (nếu có)")
print("   - Đây là nội dung sẽ được lưu vào Pinecone index")
print("="*70)

