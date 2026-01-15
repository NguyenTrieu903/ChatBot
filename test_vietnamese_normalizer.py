"""Test Vietnamese Normalizer - Demo how it converts text without diacritics."""

from rag_system.vietnamese_normalizer import normalize_vietnamese

def test_normalizer():
    """Test Vietnamese text normalization."""
    print("=" * 60)
    print("VIETNAMESE TEXT NORMALIZER TEST")
    print("=" * 60)
    print()
    
    test_cases = [
        "thuoc bo than",
        "gia bao nhieu",
        "lieu luong su dung nhu the nao",
        "thuoc tri tieu duong",
        "co tac dung phu khong",
        "cach su dung ra sao",
        "mua o dau",
        "thuốc bổ thận",  # Already has diacritics
        "giá bao nhiêu?",  # Already has diacritics with punctuation
    ]
    
    print("Testing normalization:")
    print()
    
    for text in test_cases:
        try:
            normalized = normalize_vietnamese(text)
            status = "✓" if normalized != text else "→"
            print(f"{status} '{text}' → '{normalized}'")
        except Exception as e:
            print(f"✗ '{text}' → ERROR: {e}")
    
    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_normalizer()
