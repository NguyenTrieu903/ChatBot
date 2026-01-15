"""Vietnamese Text Normalizer - Convert text without diacritics to proper Vietnamese with diacritics.

This utility uses a lightweight LLM to normalize Vietnamese text input.
"""

import os
from typing import Optional
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


class VietnameseNormalizer:
    """Normalize Vietnamese text without diacritics to proper Vietnamese with diacritics."""
    
    def __init__(self):
        """Initialize the normalizer with a fast LLM."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        # Use a fast, small model for normalization
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.0,  # Deterministic output
            max_tokens=200  # Short responses only
        )
        
        self.system_prompt = """Bạn là một hệ thống chuẩn hóa tiếng Việt.

NHIỆM VỤ: Chuyển đổi text tiếng Việt KHÔNG DẤU thành text tiếng Việt CÓ DẤU chính xác.

QUY TẮC:
1. CHỈ trả về text đã được thêm dấu, KHÔNG giải thích gì thêm
2. Giữ nguyên cấu trúc câu, chỉ thêm dấu
3. Nếu text đã có dấu đầy đủ → trả về nguyên văn
4. Sửa lỗi chính tả phổ biến nếu có
5. Phải trả về tiếng Việt chuẩn, dễ hiểu

VÍ DỤ:
Input: "thuoc bo than"
Output: "thuốc bổ thận"

Input: "gia bao nhieu"
Output: "giá bao nhiêu"

Input: "lieu luong su dung nhu the nao"
Output: "liều lượng sử dụng như thế nào"

Input: "thuốc bổ thận" (đã có dấu)
Output: "thuốc bổ thận"

BẮT ĐẦU:"""
    
    def normalize(self, text: str) -> str:
        """Normalize Vietnamese text by adding proper diacritics.
        
        Args:
            text: Input text (with or without diacritics)
            
        Returns:
            Normalized text with proper Vietnamese diacritics
        """
        if not text or not text.strip():
            return text
        
        # Quick check: if text already has Vietnamese diacritics, return as-is
        vietnamese_chars = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
        if any(c in vietnamese_chars for c in text.lower()):
            # Text already has diacritics, but may be incomplete
            # Let LLM fix it
            pass
        
        try:
            # Use LLM to normalize
            messages = [
                ("system", self.system_prompt),
                ("human", text)
            ]
            
            response = self.llm.invoke(messages)
            normalized = response.content.strip()
            
            # Validation: make sure output is reasonable
            if not normalized or len(normalized) > len(text) * 2:
                # LLM failed, return original
                print(f"⚠️  Normalization failed for: {text}")
                return text
            
            if normalized != text:
                print(f"✨ Normalized: '{text}' → '{normalized}'")
            
            return normalized
            
        except Exception as e:
            print(f"⚠️  Error normalizing text: {e}")
            return text


# Singleton instance
_normalizer: Optional[VietnameseNormalizer] = None


def get_normalizer() -> VietnameseNormalizer:
    """Get singleton normalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = VietnameseNormalizer()
    return _normalizer


def normalize_vietnamese(text: str) -> str:
    """Convenience function to normalize Vietnamese text.
    
    Args:
        text: Input text (with or without diacritics)
        
    Returns:
        Normalized text with proper Vietnamese diacritics
    """
    normalizer = get_normalizer()
    return normalizer.normalize(text)
