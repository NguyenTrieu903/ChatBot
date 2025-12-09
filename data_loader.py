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

