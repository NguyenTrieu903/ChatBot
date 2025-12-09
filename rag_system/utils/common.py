from data_loader import load_and_chunk_json

def format_docs(docs) -> str:
            """Format retrieved documents into context string.
            
            Args:
                docs: List of Document objects from retriever
                
            Returns:
                Formatted context string
            """
            if not docs:
                return "Không có thông tin liên quan trong cơ sở dữ liệu."
            
            context_parts = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content
                metadata = doc.metadata
                source = metadata.get('source', 'Unknown')
                product_name = metadata.get('product_name', 'Unknown')
                
                # Truncate long documents
                if len(content) > 1500:
                    content = content[:1500] + "\n... (nội dung đã rút gọn)"
                
                context_parts.append(f"Tài liệu {i} (Sản phẩm: {product_name}, Nguồn: {source}):\n{content}")
            
            return "\n\n".join(context_parts)
