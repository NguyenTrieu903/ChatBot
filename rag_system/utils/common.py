"""Common utility functions for RAG system."""

from typing import List
from langchain_core.documents import Document


def format_docs(docs: List[Document]) -> str:
    """Format retrieved documents into context string with improved structure.
    
    Args:
        docs: List of Document objects from retriever
        
    Returns:
        Formatted context string optimized for medical domain
    """
    if not docs:
        return "Không có thông tin liên quan trong cơ sở dữ liệu."
    
    context_parts = []
    max_length = 1500  # Giảm để tiết kiệm tokens nhưng vẫn đủ thông tin
    
    for i, doc in enumerate(docs, 1):
        content = doc.page_content
        metadata = doc.metadata
        source = metadata.get('source', 'Unknown')
        product_name = metadata.get('product_name', 'Unknown')
        
        # Truncate long documents nhưng giữ phần quan trọng
        if len(content) > max_length:
            # Giữ phần đầu (thường chứa tên sản phẩm và thông tin chính)
            content = content[:max_length] + "\n... (nội dung đã rút gọn)"
        
        # Format với cấu trúc rõ ràng hơn
        chunk_info = ""
        if 'chunk_index' in metadata and 'total_chunks' in metadata:
            chunk_index = metadata.get('chunk_index', 0)
            total_chunks = metadata.get('total_chunks', 1)
            chunk_info = f" (Chunk {chunk_index + 1}/{total_chunks})"
        
        context_parts.append(
            f"[THÔNG TIN {i}] Sản phẩm: {product_name}{chunk_info}\n"
            f"Nguồn: {source}\n"
            f"Nội dung:\n{content}"
        )
    
    return "\n\n" + "="*70 + "\n\n".join(context_parts) + "\n" + "="*70
