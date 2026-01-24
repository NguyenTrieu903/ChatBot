"""Data loader for JSON files with chunking support.

Implements: JSON Data → Chunking → Documents
"""

import json
from typing import List, Dict, Any
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
    """Convert JSON data to LangChain Documents with structured medical fields.
    
    Parses medical product information into structured fields for better retrieval.
    
    Args:
        json_data: List of dictionaries from JSON
        
    Returns:
        List of LangChain Document objects with structured content
    """
    documents = []
    
    for item in json_data:
        # Extract name and metadata
        name = item.get('name', 'Unknown')
        metadata_text = item.get('metadata', '')
        
        # Parse structured medical information from metadata
        parsed_info = _parse_medical_metadata(metadata_text)
        
        # Create structured document content
        # Format for better semantic search and retrieval
        content = f"""TÊN SẢN PHẨM: {name}

THÀNH PHẦN & MÔ TẢ:
{parsed_info.get('description', metadata_text)}

CÔNG DỤNG:
{parsed_info.get('indication', 'Thông tin công dụng có trong mô tả chung')}

LIỀU DÙNG:
{parsed_info.get('dosage', 'Thông tin liều dùng có trong mô tả chung')}

GIÁ & QUY CÁCH:
{parsed_info.get('price_info', 'Thông tin giá có trong mô tả chung')}

NHÀ SẢN XUẤT:
{parsed_info.get('manufacturer', 'Thông tin nhà sản xuất có trong mô tả chung')}

---
Sản phẩm: {name}
Thông tin đầy đủ: {metadata_text}"""
        
        # Create LangChain Document with rich metadata
        doc = Document(
            page_content=content,
            metadata={
                'source': 'traning.json',
                'product_name': name,
                'type': 'product_info',
                'has_dosage': bool(parsed_info.get('dosage')),
                'has_price': bool(parsed_info.get('price_info')),
                'has_indication': bool(parsed_info.get('indication'))
            }
        )
        
        documents.append(doc)
    
    print(f"✅ Đã chuyển đổi {len(documents)} items thành Documents với cấu trúc y khoa")
    
    return documents


def _parse_medical_metadata(metadata_text: str) -> Dict[str, str]:
    """Parse medical metadata into structured fields.
    
    Extracts: description, indication, dosage, price, manufacturer
    
    Args:
        metadata_text: Raw metadata text
        
    Returns:
        Dictionary with parsed fields
    """
    parsed = {
        'description': '',
        'indication': '',
        'dosage': '',
        'price_info': '',
        'manufacturer': ''
    }
    
    lines = metadata_text.split('\n')
    current_section = 'description'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect indication section (công dụng)
        if any(keyword in line.lower() for keyword in ['tăng cường', 'hỗ trợ', 'giảm', 'phòng ngừa', 'điều trị', 'bồi bổ']):
            if not parsed['indication']:
                parsed['indication'] = line
            else:
                parsed['indication'] += ' ' + line
        
        # Detect dosage section (liều dùng)
        elif any(keyword in line.lower() for keyword in ['viên/ngày', 'lần/ngày', 'g/ngày', 'duy trì', 'tăng cường', 'liều']):
            if not parsed['dosage']:
                parsed['dosage'] = line
            else:
                parsed['dosage'] += ' ' + line
        
        # Detect price section
        elif '₫' in line or 'hộp' in line.lower() or 'gói' in line.lower():
            if not parsed['price_info']:
                parsed['price_info'] = line
            else:
                parsed['price_info'] += ' ' + line
        
        # Detect manufacturer
        elif any(keyword in line for keyword in ['Co., Ltd', 'Pharmaceutical', 'UMEKEN', 'Waki', 'Nhật Bản']):
            if not parsed['manufacturer']:
                parsed['manufacturer'] = line
            else:
                parsed['manufacturer'] += ' ' + line
        
        # Default to description
        else:
            if not parsed['description']:
                parsed['description'] = line
            else:
                parsed['description'] += ' ' + line
    
    # Fallback: if sections are empty, use full metadata
    if not parsed['description']:
        parsed['description'] = metadata_text
    
    return parsed


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

