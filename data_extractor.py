"""Script to extract training data from Excel and Word files for Vietnamese chatbot."""

import os
import re
from typing import List, Dict, Any
from pathlib import Path

try:
    from openpyxl import load_workbook
    from docx import Document
except ImportError:
    print("Please install required packages: pip install openpyxl python-docx")
    raise


def extract_from_excel(file_path: str) -> List[Dict[str, Any]]:
    """Extract data from Excel file, grouping by product.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        List of document dictionaries with Vietnamese content
    """
    documents = []
    
    try:
        wb = load_workbook(file_path)
        
        # Process all sheets
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            
            # Skip empty sheets
            if sheet.max_row <= 1:
                continue
                
            # Get headers from first row
            headers = []
            for cell in sheet[1]:
                if cell.value:
                    headers.append(str(cell.value).strip())
            
            if not headers:
                continue
            
            # Find column indices for "Câu hỏi" and "Trả lời"
            question_col = None
            answer_col = None
            for idx, header in enumerate(headers, start=1):
                if "câu hỏi" in header.lower():
                    question_col = idx
                elif "trả lời" in header.lower():
                    answer_col = idx
            
            # Group rows by product
            current_product = None
            product_info = {}
            
            for row_idx in range(2, sheet.max_row + 1):
                question_val = sheet.cell(row=row_idx, column=question_col).value if question_col else None
                answer_val = sheet.cell(row=row_idx, column=answer_col).value if answer_col else None
                
                if not question_val:
                    continue
                
                question_text = str(question_val).strip()
                answer_text = str(answer_val).strip() if answer_val else ""
                
                # Check if this is a product header (e.g., "1. The Fucoidan", "4. Kidney & Men's")
                if re.match(r'^\d+\.\s+', question_text):
                    # Save previous product if exists
                    if current_product and product_info:
                        doc = create_product_document(current_product, product_info, sheet_name)
                        if doc:
                            documents.append(doc)
                    
                    # Start new product
                    current_product = question_text
                    product_info = {"Tên sản phẩm": current_product}
                    
                elif current_product:
                    # Add Q&A to current product
                    if answer_text:
                        # Store the answer with the question as key
                        product_info[question_text] = answer_text
            
            # Save last product
            if current_product and product_info:
                doc = create_product_document(current_product, product_info, sheet_name)
                if doc:
                    documents.append(doc)
        
        print(f"✅ Extracted {len(documents)} product documents from Excel file")
        return documents
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def create_product_document(product_name: str, product_info: Dict[str, str], sheet_name: str) -> Dict[str, Any]:
    """Create a comprehensive document for a product.
    
    Args:
        product_name: Name of the product
        product_info: Dictionary of product Q&A
        sheet_name: Name of the Excel sheet
        
    Returns:
        Document dictionary or None
    """
    if not product_info or len(product_info) <= 1:
        return None
    
    # Build comprehensive content
    content_parts = []
    
    # Add product name prominently
    content_parts.append(f"SẢN PHẨM: {product_name}")
    content_parts.append("=" * 50)
    
    # Extract and organize key information
    product_name_clean = None
    features = None
    benefits = None
    dosage = None
    price_specs = None
    manufacturer = None
    
    for question, answer in product_info.items():
        question_lower = question.lower()
        
        if "tên sản phẩm" in question_lower:
            product_name_clean = answer
        elif "điểm nổi bật" in question_lower or "đặc điểm" in question_lower:
            features = answer
        elif "công dụng" in question_lower or "tác dụng" in question_lower:
            benefits = answer
        elif "liều dùng" in question_lower or "cách dùng" in question_lower:
            dosage = answer
        elif "giá" in question_lower or "quy cách" in question_lower:
            price_specs = answer
        elif "sản xuất" in question_lower or "nhà sản xuất" in question_lower:
            manufacturer = answer
    
    # Add information in structured format
    if product_name_clean:
        content_parts.append(f"\n📦 TÊN SẢN PHẨM:\n{product_name_clean}")
    
    if price_specs:
        content_parts.append(f"\n💰 GIÁ VÀ QUY CÁCH:\n{price_specs}")
    
    if dosage:
        content_parts.append(f"\n💊 LIỀU DÙNG:\n{dosage}")
    
    if benefits:
        content_parts.append(f"\n✨ CÔNG DỤNG:\n{benefits}")
    
    if features:
        content_parts.append(f"\n🌟 ĐIỂM NỔI BẬT:\n{features}")
    
    if manufacturer:
        content_parts.append(f"\n🏭 NHÀ SẢN XUẤT:\n{manufacturer}")
    
    # Add all Q&A at the end for completeness
    content_parts.append("\n" + "=" * 50)
    content_parts.append("CHI TIẾT CÂU HỎI - TRẢ LỜI:")
    content_parts.append("=" * 50)
    
    for question, answer in product_info.items():
        if question != "Tên sản phẩm" and answer:
            content_parts.append(f"\nQ: {question}")
            content_parts.append(f"A: {answer}")
    
    # Create document
    document = {
        "page_content": "\n".join(content_parts),
        "metadata": {
            "source": f"Excel - {product_name}",
            "category": "Sản phẩm",
            "product_name": product_name_clean or product_name,
            "has_price": bool(price_specs),
            "priority": "high",  # Product documents are high priority
            "language": "vietnamese"
        }
    }
    
    return document


def combine_and_save_data(excel_file: str, word_file: str, output_file: str = None) -> List[Dict[str, Any]]:
    """Extract and combine data from both files.
    
    Args:
        excel_file: Path to Excel file
        word_file: Path to Word file
        output_file: Optional path to save combined data as Python module (legacy, not recommended)
        
    Returns:
        Combined list of documents
    """
    all_documents = []
    
    print("\n📄 Đang trích xuất dữ liệu từ file nguồn...")
    print(f"Excel: {excel_file}")
    print(f"Word: {word_file}")
    print("-" * 60)
    
    # Extract from Excel
    if os.path.exists(excel_file):
        excel_docs = extract_from_excel(excel_file)
        all_documents.extend(excel_docs)
    else:
        print(f"⚠️  Không tìm thấy file Excel: {excel_file}")

    
    print("-" * 60)
    print(f"✅ Tổng số tài liệu: {len(all_documents)}")
    
    # Save to Python module only if explicitly requested (not recommended)
    if output_file and all_documents:
        print(f"⚠️  Đang lưu vào file mock (không khuyến khích): {output_file}")
        save_as_python_module(all_documents, output_file)
    
    return all_documents


def save_as_python_module(documents: List[Dict[str, Any]], output_file: str):
    """Save documents as a Python module file.
    
    Args:
        documents: List of document dictionaries
        output_file: Path to output Python file
    """
    import json
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('"""Vietnamese support data extracted from training files."""\n\n')
            f.write('from typing import List, Dict, Any\n\n')
            f.write('# Vietnamese Chatbot Training Data\n')
            f.write('VIETNAMESE_SUPPORT_DOCS = ')
            
            # Use json.dumps for pretty formatting with Vietnamese characters
            json_str = json.dumps(documents, ensure_ascii=False, indent=4)
            f.write(json_str)
            
            f.write('\n\n')
            f.write('def get_vietnamese_support_data() -> List[Dict[str, Any]]:\n')
            f.write('    """Get all Vietnamese support documents."""\n')
            f.write('    return VIETNAMESE_SUPPORT_DOCS\n')
        
        print(f"✅ Data saved to Python module: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving Python module: {str(e)}")


if __name__ == "__main__":
    # Define file paths
    excel_file = "../traning.xlsx"
    word_file = "../Training data.docx"
    output_file = "mock_data/vietnamese_support.py"
    
    # Extract and combine data
    documents = combine_and_save_data(excel_file, word_file, output_file)
    
    # Print summary
    if documents:
        print("\n📊 Data Summary:")
        print(f"Total documents: {len(documents)}")
        
        # Count by category
        categories = {}
        for doc in documents:
            cat = doc['metadata'].get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nDocuments by category:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count}")
        
        # Show first document as sample
        print("\n📝 Sample document:")
        print(f"Category: {documents[0]['metadata']['category']}")
        print(f"Source: {documents[0]['metadata']['source']}")
        print(f"Content preview: {documents[0]['page_content'][:200]}...")

