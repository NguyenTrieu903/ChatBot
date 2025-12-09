"""Common utility functions for RAG system."""

from typing import List
from langchain_core.documents import Document


def format_docs(docs: List[Document]) -> str:
    """Format retrieved documents into context string.
    
    Args:
        docs: List of Document objects from retriever
        
    Returns:
        Formatted context string
    """
    if not docs:
        return "Không có thông tin liên quan trong cơ sở dữ liệu."
    
    context_parts = []
    max_length = 1500
    
    for i, doc in enumerate(docs, 1):
        content = doc.page_content
        metadata = doc.metadata
        source = metadata.get('source', 'Unknown')
        product_name = metadata.get('product_name', 'Unknown')
        
        # Truncate long documents
        if len(content) > max_length:
            content = content[:max_length] + "\n... (nội dung đã rút gọn)"
        
        context_parts.append(
            f"Tài liệu {i} (Sản phẩm: {product_name}, Nguồn: {source}):\n{content}"
        )
    
    return "\n\n".join(context_parts)
