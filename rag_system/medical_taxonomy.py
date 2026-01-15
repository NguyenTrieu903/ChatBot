"""Medical Taxonomy - Knowledge base for condition detection and product mapping.

This module provides:
1. Medical conditions/symptoms taxonomy (Vietnamese)
2. Product-to-condition mappings
3. Condition detection (with/without diacritics)
"""

import re
import unicodedata
from typing import List, Dict, Optional, Tuple


# ============================================================================
# MEDICAL TAXONOMY - Common Conditions & Symptoms
# ============================================================================

MEDICAL_CONDITIONS = {
    # Cancer & Immune Support
    "ung_thu": {
        "names": ["ung thư", "ung thu", "cancer", "khối u", "khoi u", "tế bào ung thư"],
        "keywords": ["ung thư", "ung thu", "khối u", "tế bào ung thư", "hóa trị", "xạ trị"],
        "category": "oncology",
        "severity": "critical"
    },
    "mien_dich": {
        "names": ["miễn dịch", "mien dich", "đề kháng", "de khang", "sức đề kháng", "hệ miễn dịch"],
        "keywords": ["miễn dịch", "đề kháng", "tăng cường", "bồi bổ", "sức khỏe"],
        "category": "immune",
        "severity": "moderate"
    },
    
    # Kidney & Urinary
    "bo_than": {
        "names": ["bổ thận", "bo than", "thận", "than", "kidney"],
        "keywords": ["bổ thận", "thận", "thận yếu", "bồi bổ thận"],
        "category": "kidney",
        "severity": "moderate"
    },
    "sinh_ly_nam": {
        "names": ["sinh lý nam", "sinh ly nam", "sinh lý", "yếu sinh lý", "yeu sinh ly"],
        "keywords": ["sinh lý", "sinh lực", "tráng dương", "nam giới", "yếu sinh lý"],
        "category": "men_health",
        "severity": "moderate"
    },
    
    # Cardiovascular
    "dot_quy": {
        "names": ["đột quỵ", "dot quy", "tai biến", "stroke", "đột quị"],
        "keywords": ["đột quỵ", "tai biến", "mạch máu", "huyết áp", "stroke"],
        "category": "cardiovascular",
        "severity": "critical"
    },
    "mau_dong": {
        "names": ["máu đông", "mau dong", "cục máu đông", "thrombosis"],
        "keywords": ["máu đông", "cục máu đông", "huyết khối"],
        "category": "cardiovascular",
        "severity": "high"
    },
    "cholesterol": {
        "names": ["cholesterol", "mỡ máu", "mo mau", "lipid"],
        "keywords": ["cholesterol", "mỡ máu", "lipid", "mỡ trong máu"],
        "category": "cardiovascular",
        "severity": "moderate"
    },
    
    # Liver & Digestive
    "gan": {
        "names": ["gan", "liver", "giải độc gan", "giai doc gan"],
        "keywords": ["gan", "giải độc gan", "gan nhiễm mỡ", "bệnh gan"],
        "category": "liver",
        "severity": "moderate"
    },
    
    # Pain & Fever
    "dau": {
        "names": ["đau", "dau", "pain", "nhức"],
        "keywords": ["đau", "nhức", "đau đầu", "đau răng", "đau bụng"],
        "category": "pain",
        "severity": "low"
    },
    "sot": {
        "names": ["sốt", "sot", "fever", "nóng"],
        "keywords": ["sốt", "nóng", "hạ sốt", "fever"],
        "category": "fever",
        "severity": "moderate"
    },
    
    # General Health
    "stress": {
        "names": ["stress", "căng thẳng", "cang thang", "lo âu", "lo au"],
        "keywords": ["stress", "căng thẳng", "lo âu", "mệt mỏi"],
        "category": "mental_health",
        "severity": "low"
    },
    "ngu": {
        "names": ["ngủ", "ngu", "sleep", "mất ngủ", "mat ngu"],
        "keywords": ["ngủ", "mất ngủ", "giấc ngủ", "khó ngủ"],
        "category": "sleep",
        "severity": "low"
    }
}


# ============================================================================
# PRODUCT-TO-CONDITION MAPPING
# ============================================================================

PRODUCT_CONDITIONS = {
    "The Fucoidan": {
        "primary_conditions": ["ung_thu", "mien_dich"],
        "secondary_conditions": [],
        "keywords": ["ung thư", "miễn dịch", "hóa trị", "xạ trị", "tế bào ung thư"],
        "description": "Hỗ trợ điều trị ung thư, tăng cường miễn dịch"
    },
    "The Fucoidan xK": {
        "primary_conditions": ["ung_thu", "mien_dich"],
        "secondary_conditions": [],
        "keywords": ["ung thư", "miễn dịch", "hóa trị", "xạ trị"],
        "description": "Phiên bản nâng cấp hỗ trợ điều trị ung thư"
    },
    "β-Glucan Ball": {
        "primary_conditions": ["ung_thu", "mien_dich"],
        "secondary_conditions": [],
        "keywords": ["ung thư", "miễn dịch", "beta glucan", "nấm"],
        "description": "Chiết xuất nấm hỗ trợ miễn dịch và ung thư"
    },
    "Kidney & Men's": {
        "primary_conditions": ["bo_than", "sinh_ly_nam"],
        "secondary_conditions": [],
        "keywords": ["bổ thận", "sinh lý nam", "tráng dương", "testosterone"],
        "description": "Bổ thận và tăng cường sinh lý nam giới"
    },
    "Power HLP": {
        "primary_conditions": ["dot_quy", "mau_dong"],
        "secondary_conditions": ["cholesterol"],
        "keywords": ["đột quỵ", "máu đông", "mạch máu", "cholesterol"],
        "description": "Phòng ngừa đột quỵ và máu đông"
    },
    "The Reishi": {
        "primary_conditions": ["mien_dich", "gan"],
        "secondary_conditions": ["cholesterol", "stress", "ngu"],
        "keywords": ["linh chi", "miễn dịch", "gan", "giải độc", "giấc ngủ"],
        "description": "Linh chi tăng cường miễn dịch và giải độc gan"
    },
    "Paracetamol": {
        "primary_conditions": ["dau", "sot"],
        "secondary_conditions": [],
        "keywords": ["đau", "sốt", "giảm đau", "hạ sốt"],
        "description": "Giảm đau và hạ sốt"
    }
}


# ============================================================================
# CONDITION DETECTION
# ============================================================================

def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics from text.
    
    Examples:
        "bổ thận" → "bo than"
        "miễn dịch" → "mien dich"
    """
    # Normalize to NFD (decomposed form)
    nfd = unicodedata.normalize('NFD', text)
    # Remove combining characters (diacritics)
    without_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return without_diacritics


def detect_medical_condition(query: str) -> Optional[Tuple[str, Dict]]:
    """Detect medical condition from user query.
    
    Works with or without Vietnamese diacritics.
    
    Args:
        query: User's query (e.g., "thuốc nào bổ thận", "thuoc nao bo than")
        
    Returns:
        Tuple of (condition_id, condition_info) or None if not found
        
    Examples:
        "thuốc nào bổ thận" → ("bo_than", {...})
        "thuoc nao bo than" → ("bo_than", {...})
        "hỗ trợ ung thư" → ("ung_thu", {...})
        "ho tro ung thu" → ("ung_thu", {...})
    """
    query_lower = query.lower()
    query_no_diacritics = remove_diacritics(query_lower)
    
    # Try to match each condition
    best_match = None
    best_score = 0
    
    for condition_id, condition_info in MEDICAL_CONDITIONS.items():
        # Check all name variations
        for name in condition_info["names"]:
            name_lower = name.lower()
            name_no_diacritics = remove_diacritics(name_lower)
            
            # Exact match (with diacritics)
            if name_lower in query_lower:
                return (condition_id, condition_info)
            
            # Exact match (without diacritics)
            if name_no_diacritics in query_no_diacritics:
                return (condition_id, condition_info)
        
        # Check keywords for partial matches
        for keyword in condition_info["keywords"]:
            keyword_lower = keyword.lower()
            keyword_no_diacritics = remove_diacritics(keyword_lower)
            
            if keyword_lower in query_lower or keyword_no_diacritics in query_no_diacritics:
                # Calculate match score (longer keywords = better match)
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = (condition_id, condition_info)
    
    return best_match


def find_products_for_condition(condition_id: str, include_secondary: bool = True) -> List[str]:
    """Find all products that treat a specific medical condition.
    
    Args:
        condition_id: Condition ID (e.g., "bo_than", "ung_thu")
        include_secondary: Include products where this is secondary indication
        
    Returns:
        List of product names
        
    Examples:
        find_products_for_condition("bo_than") → ["Kidney & Men's"]
        find_products_for_condition("ung_thu") → ["The Fucoidan", "The Fucoidan xK", "β-Glucan Ball"]
    """
    matching_products = []
    
    for product_name, product_info in PRODUCT_CONDITIONS.items():
        # Check primary conditions
        if condition_id in product_info["primary_conditions"]:
            matching_products.append(product_name)
        # Check secondary conditions if requested
        elif include_secondary and condition_id in product_info.get("secondary_conditions", []):
            matching_products.append(product_name)
    
    return matching_products


def detect_condition_and_products(query: str) -> Optional[Dict]:
    """Complete pipeline: Detect condition and find matching products.
    
    Args:
        query: User's query
        
    Returns:
        Dictionary with condition info and matching products, or None
        
    Example:
        Input: "thuốc nào bổ thận"
        Output: {
            "condition_id": "bo_than",
            "condition_name": "bổ thận",
            "products": ["Kidney & Men's"],
            "query_type": "condition_search"
        }
    """
    # Detect condition
    condition_match = detect_medical_condition(query)
    
    if not condition_match:
        return None
    
    condition_id, condition_info = condition_match
    
    # Find products
    products = find_products_for_condition(condition_id, include_secondary=True)
    
    if not products:
        return None
    
    return {
        "condition_id": condition_id,
        "condition_name": condition_info["names"][0],  # Primary name
        "condition_category": condition_info["category"],
        "products": products,
        "query_type": "condition_search",
        "severity": condition_info["severity"]
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_condition_query(query: str) -> bool:
    """Check if query is asking about a medical condition.
    
    Examples:
        "thuốc nào bổ thận" → True
        "hỗ trợ ung thư" → True
        "The Fucoidan là gì" → False
    """
    condition_patterns = [
        r"thuốc\s+nào",
        r"thuoc\s+nao",
        r"sản phẩm nào",
        r"san pham nao",
        r"có thuốc",
        r"co thuoc",
        r"hỗ trợ",
        r"ho tro",
        r"điều trị",
        r"dieu tri",
        r"chữa",
        r"chua",
        r"phòng ngừa",
        r"phong ngua"
    ]
    
    query_lower = query.lower()
    query_no_diacritics = remove_diacritics(query_lower)
    
    for pattern in condition_patterns:
        if re.search(pattern, query_lower) or re.search(pattern, query_no_diacritics):
            return True
    
    return False


def get_all_conditions() -> Dict[str, Dict]:
    """Get all medical conditions in the taxonomy.
    
    Returns:
        Dictionary of all conditions
    """
    return MEDICAL_CONDITIONS


def get_all_products() -> Dict[str, Dict]:
    """Get all products and their condition mappings.
    
    Returns:
        Dictionary of all products
    """
    return PRODUCT_CONDITIONS


# ============================================================================
# TESTING / DEBUGGING
# ============================================================================

if __name__ == "__main__":
    # Test condition detection
    test_queries = [
        "thuốc nào bổ thận",
        "thuoc nao bo than",
        "có thuốc hỗ trợ ung thư không",
        "co thuoc ho tro ung thu khong",
        "sản phẩm phòng ngừa đột quỵ",
        "thuốc giảm đau hạ sốt",
        "bổ gan",
        "tăng cường miễn dịch"
    ]
    
    print("Testing Condition Detection:")
    print("=" * 70)
    
    for query in test_queries:
        result = detect_condition_and_products(query)
        print(f"\nQuery: '{query}'")
        if result:
            print(f"  ✅ Detected: {result['condition_name']} ({result['condition_id']})")
            print(f"  Products: {', '.join(result['products'])}")
        else:
            print(f"  ❌ No condition detected")
