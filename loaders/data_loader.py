"""Data loader for JSON and Excel files with chunking support.

Implements: JSON/Excel Data → Chunking → Documents
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas không được cài đặt. Cần cài: pip install pandas openpyxl")

# Danh sách các sản phẩm được phép (có thể mở rộng sau này)
ALLOWED_PRODUCTS = [
    "The Fucoidan",
    "The Fucoidan xK (Phiên bản nâng cấp)",
    "β-Glucan Ball",
    "Kidney & Men's",
    "Power HLP",
    "The Reishi"
]


def load_json_data(json_file: str) -> List[Dict[str, Any]]:
    """Load data from JSON file.
    
    Args:
        json_file: Path to JSON file
        
    Returns:
        List of dictionaries from JSON
    """
    json_path = Path(json_file)
    
    if not json_path.exists():
        raise FileNotFoundError(f"❌ Không tìm thấy file: {json_file}")
    
    print(f"📄 Đang đọc file JSON: {json_file}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Đã đọc {len(data)} items từ JSON")
    
    return data


def json_to_documents(json_data: List[Dict[str, Any]]) -> List[Document]:
    """Convert JSON data to LangChain Documents.
    
    Args:
        json_data: List of dictionaries from JSON
        
    Returns:
        List of LangChain Document objects
    """
    documents = []
    
    for item in json_data:
        # Extract name and metadata
        name = item.get('name', 'Unknown')
        metadata_text = item.get('metadata', '')
        
        # Create document content with better structure for search
        # Include product name multiple times to improve matching
        # Format: Product name + synonyms + full metadata
        content = f"""Tên sản phẩm: {name}
Sản phẩm: {name}

{metadata_text}

Thông tin về {name}: {metadata_text}"""
        
        # Create LangChain Document
        doc = Document(
            page_content=content,
            metadata={
                'source': 'traning.json',
                'product_name': name,
                'type': 'product_info'
            }
        )
        
        documents.append(doc)
    
    print(f"✅ Đã chuyển đổi {len(documents)} items thành Documents")
    
    return documents


def chunk_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """Split documents into chunks using RecursiveCharacterTextSplitter.
    
    Args:
        documents: List of LangChain Documents
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked Documents
    """
    print(f"✂️  Đang chunking {len(documents)} documents...")
    print(f"   Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
    
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Vietnamese-friendly separators
    )
    
    # Split documents
    chunks = text_splitter.split_documents(documents)
    
    print(f"✅ Đã tạo {len(chunks)} chunks từ {len(documents)} documents")
    
    return chunks


def load_and_chunk_json(
    json_file: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """Complete pipeline: Load JSON → Convert to Documents → Chunk.
    
    Args:
        json_file: Path to JSON file
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked Documents ready for embedding
    """
    # Step 1: Load JSON
    json_data = load_json_data(json_file)
    
    # Step 2: Convert to Documents
    documents = json_to_documents(json_data)
    
    # Step 3: Chunk documents
    chunks = chunk_documents(documents, chunk_size, chunk_overlap)
    
    return chunks


def load_excel_data(excel_file: str) -> pd.DataFrame:
    """Load data from Excel file.
    
    Args:
        excel_file: Path to Excel file
        
    Returns:
        DataFrame from Excel file
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas không được cài đặt. Cần cài: pip install pandas openpyxl")
    
    excel_path = Path(excel_file)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"❌ Không tìm thấy file: {excel_file}")
    
    print(f"📄 Đang đọc file Excel: {excel_file}")
    
    df = pd.read_excel(excel_path)
    
    print(f"✅ Đã đọc {len(df)} rows từ Excel")
    print(f"   Columns: {df.columns.tolist()}")
    
    return df


def match_product_name(text: str, allowed_products: List[str] = None) -> Optional[str]:
    """So khớp tên sản phẩm từ text với danh sách sản phẩm được phép.
    
    Args:
        text: Text cần kiểm tra
        allowed_products: Danh sách sản phẩm được phép (mặc định dùng ALLOWED_PRODUCTS)
        
    Returns:
        Tên sản phẩm nếu tìm thấy, None nếu không
    """
    if allowed_products is None:
        allowed_products = ALLOWED_PRODUCTS
    
    text_clean = text.strip()
    
    # So khớp chính xác
    for product in allowed_products:
        if product in text_clean or text_clean.startswith(product):
            return product
    
    # So khớp không phân biệt hoa thường
    text_lower = text_clean.lower()
    for product in allowed_products:
        if product.lower() in text_lower or text_lower.startswith(product.lower()):
            return product
    
    return None


def extract_product_name_from_text(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Trích xuất tên sản phẩm từ text trong cột "Trả lời".
    
    Tên sản phẩm phải nằm trong danh sách ALLOWED_PRODUCTS.
    Tên sản phẩm thường là dòng đầu tiên của text.
    Trả về toàn bộ nội dung thực tế của sản phẩm (không chỉ tên).
    
    Args:
        text: Text từ cột "Trả lời"
        
    Returns:
        Tuple (product_name, content) - product_name chỉ trả về nếu tìm thấy trong ALLOWED_PRODUCTS,
        content là toàn bộ nội dung thực tế về sản phẩm
    """
    if not text or text.strip() == '' or text == 'nan':
        return None, None
    
    text_original = text.strip()
    lines = text_original.split('\n')
    
    # Loại bỏ các dòng trống nhưng giữ lại thứ tự
    lines_clean = []
    for line in lines:
        line_stripped = line.strip()
        if line_stripped:
            lines_clean.append(line_stripped)
    
    if not lines_clean:
        return None, None
    
    # Thử lấy dòng đầu tiên làm tên sản phẩm
    first_line = lines_clean[0]
    first_line_clean = first_line.strip('*').strip('_').strip('-').strip()
    
    # Kiểm tra xem dòng đầu tiên có phải là tên sản phẩm được phép không
    matched_product = match_product_name(first_line_clean)
    
    if matched_product:
        # Nếu tìm thấy tên sản phẩm, dùng TOÀN BỘ text gốc làm nội dung
        # Vì tên sản phẩm là phần của thông tin, không cần loại bỏ
        # Điều này đảm bảo lưu đầy đủ thông tin về sản phẩm
        return matched_product, text_original
    
    # Nếu dòng đầu tiên không khớp, thử tìm tên sản phẩm trong toàn bộ text
    matched_product = match_product_name(text_original)
    if matched_product:
        # Nếu tìm thấy tên sản phẩm ở đâu đó trong text, dùng TOÀN BỘ text làm nội dung
        # Điều này đảm bảo lưu đầy đủ thông tin về sản phẩm
        return matched_product, text_original
    
    # Không tìm thấy sản phẩm được phép
    return None, None


def excel_to_documents(
    df: pd.DataFrame,
    excel_file: str = None,
    product_name_column: str = None,
    answer_column: str = None
) -> List[Document]:
    """Convert Excel data to LangChain Documents.
    Gộp TẤT CẢ các câu trả lời về cùng một sản phẩm thành một document duy nhất.
    Chỉ lưu câu trả lời, không lưu câu hỏi để tối ưu tìm kiếm.
    
    Args:
        df: DataFrame from Excel file
        excel_file: Path to Excel file (for metadata)
        product_name_column: Tên cột chứa tên sản phẩm (nếu có cột riêng, None nếu tên nằm trong cột trả lời)
        answer_column: Tên cột chứa phần trả lời (tự động phát hiện nếu None)
        
    Returns:
        List of LangChain Document objects
    """
    # Tự động phát hiện các cột
    columns = df.columns.tolist()
    
    # Tìm cột câu hỏi
    question_column = None
    for col in columns:
        col_lower = str(col).lower().strip()
        if any(keyword in col_lower for keyword in ['câu hỏi', 'question', 'câu hỏi']):
            question_column = col
            break
    
    # Tìm cột trả lời
    if answer_column is None:
        possible_answer_cols = ['trả lời', 'answer', 'câu trả lời', 'response', 'answers']
        answer_column = None
        for col in columns:
            col_lower = str(col).lower().strip()
            if any(possible in col_lower for possible in possible_answer_cols):
                answer_column = col
                break
        
        if answer_column is None:
            answer_column = columns[-1]
            print(f"⚠️  Không tìm thấy cột trả lời, sử dụng cột cuối cùng: {answer_column}")
    
    print(f"📋 Sử dụng cột câu hỏi: '{question_column}'")
    print(f"📋 Sử dụng cột trả lời: '{answer_column}'")
    print(f"📋 Chỉ lấy dữ liệu cho {len(ALLOWED_PRODUCTS)} sản phẩm được phép:")
    for product in ALLOWED_PRODUCTS:
        print(f"   - {product}")
    
    # Bước 1: Nhóm tất cả các dòng theo sản phẩm
    # Dictionary: {product_name: [(question, answer, row_index), ...]}
    product_data = {}
    
    for idx, row in df.iterrows():
        answer_text = str(row.get(answer_column, '')).strip()
        question_text = str(row.get(question_column, '')).strip() if question_column else ''
        
        # Bỏ qua nếu không có dữ liệu
        if not answer_text or answer_text == 'nan' or answer_text == '':
            continue
        
        # Tìm tên sản phẩm trong cột trả lời
        product_name, _ = extract_product_name_from_text(answer_text)
        
        # Nếu không tìm thấy trong trả lời, thử tìm trong câu hỏi
        if not product_name and question_text:
            product_name, _ = extract_product_name_from_text(question_text)
        
        # Chỉ xử lý sản phẩm được phép
        if not product_name:
            continue
        
        # Thêm vào dictionary
        if product_name not in product_data:
            product_data[product_name] = []
        
        product_data[product_name].append((question_text, answer_text, idx))
    
    # Bước 2: Tạo documents từ dữ liệu đã nhóm
    documents = []
    
    for product_name, qa_pairs in product_data.items():
        # Gộp TẤT CẢ các câu trả lời về sản phẩm này (KHÔNG lưu câu hỏi)
        content_parts = [f"Tên sản phẩm: {product_name}"]
        content_parts.append("")
        
        # Chỉ lấy các câu trả lời, bỏ qua câu hỏi
        answers_only = []
        for question, answer, row_idx in qa_pairs:
            # Chỉ thêm câu trả lời, không thêm câu hỏi
            if answer and answer.strip() and answer != 'nan':
                answers_only.append(answer)
        
        # Gộp tất cả câu trả lời lại, mỗi câu trả lời trên một dòng
        for answer in answers_only:
            content_parts.append(answer)
            content_parts.append("")  # Dòng trống giữa các câu trả lời
        
        # Loại bỏ dòng trống cuối cùng
        while content_parts and content_parts[-1] == "":
            content_parts.pop()
        
        content = "\n".join(content_parts)
        
        # Tạo LangChain Document
        source_name = Path(excel_file).name if excel_file else 'excel'
        doc = Document(
            page_content=content,
            metadata={
                'source': source_name,
                'product_name': product_name,
                'type': 'product_answer',
                'qa_count': len(qa_pairs)  # Số lượng Q&A pairs
            }
        )
        
        documents.append(doc)
    
    print(f"✅ Đã tạo {len(documents)} documents từ {sum(len(qa_pairs) for qa_pairs in product_data.values())} Q&A pairs")
    
    return documents


def load_and_chunk_excel(
    excel_file: str,
    product_name_column: str = None,
    answer_column: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """Complete pipeline: Load Excel → Extract answers by product name → Convert to Documents → Chunk.
    
    Args:
        excel_file: Path to Excel file
        product_name_column: Tên cột chứa tên sản phẩm (tự động phát hiện nếu None)
        answer_column: Tên cột chứa phần trả lời (tự động phát hiện nếu None)
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked Documents ready for embedding
    """
    # Step 1: Load Excel
    df = load_excel_data(excel_file)
    
    # Step 2: Convert to Documents (lấy phần trả lời theo tên sản phẩm)
    documents = excel_to_documents(df, excel_file, product_name_column, answer_column)
    
    # Step 3: Chunk documents
    chunks = chunk_documents(documents, chunk_size, chunk_overlap)
    
    return chunks


def load_multiple_excel_files(
    excel_files: List[str],
    product_name_column: str = None,
    answer_column: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """Load multiple Excel files and combine into documents.
    
    Args:
        excel_files: List of paths to Excel files
        product_name_column: Tên cột chứa tên sản phẩm (tự động phát hiện nếu None)
        answer_column: Tên cột chứa phần trả lời (tự động phát hiện nếu None)
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked Documents from all Excel files
    """
    all_chunks = []
    
    for excel_file in excel_files:
        print(f"\n{'='*70}")
        print(f"📂 Đang xử lý file: {excel_file}")
        print(f"{'='*70}")
        
        chunks = load_and_chunk_excel(
            excel_file=excel_file,
            product_name_column=product_name_column,
            answer_column=answer_column,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        all_chunks.extend(chunks)
    
    print(f"\n✅ Tổng cộng đã tạo {len(all_chunks)} chunks từ {len(excel_files)} file Excel")
    
    return all_chunks

