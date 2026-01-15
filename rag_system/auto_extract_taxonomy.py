"""Auto-extract medical taxonomy from training data.

Instead of manually defining conditions, we extract them from actual product metadata.
This ensures we only detect conditions we actually have products for!
"""

import json
import unicodedata
from typing import Dict, List, Set
from pathlib import Path


def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics."""
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def extract_conditions_from_product(product_name: str, metadata: str) -> Dict[str, List[str]]:
    """Extract medical conditions mentioned in product metadata.
    
    Returns dict with detected conditions and their variations.
    """
    metadata_lower = metadata.lower()
    detected_conditions = {}
    
    # Define condition patterns to look for (with variations)
    condition_patterns = {
        "ung_thu": ["ung thư", "ung thu", "cancer", "khối u", "hóa trị", "xạ trị", "tế bào ung thư"],
        "mien_dich": ["miễn dịch", "mien dich", "đề kháng", "de khang", "hệ miễn dịch"],
        "bo_than": ["bổ thận", "bo than", "thận", "than", "thận yếu"],
        "sinh_ly_nam": ["sinh lý nam", "sinh ly nam", "tráng dương", "testosterone", "sinh lực nam"],
        "dot_quy": ["đột quỵ", "dot quy", "tai biến mạch máu não", "tai bien"],
        "mau_dong": ["máu đông", "mau dong", "cục máu đông", "huyết khối"],
        "cholesterol": ["cholesterol", "mỡ máu", "mo mau", "lipid"],
        "cao_huyet_ap": ["cao huyết áp", "cao huyet ap", "huyết áp cao", "huyết áp"],
        "tieu_duong": ["tiểu đường", "tieu duong", "đái tháo đường", "dai thao duong", "diabetes"],
        "gan": ["gan", "giải độc gan", "gan nhiễm mỡ", "bệnh gan"],
        "tim_mach": ["tim mạch", "tim", "mạch máu", "nhồi máu cơ tim", "xơ vữa động mạch"],
        "stress": ["stress", "căng thẳng", "cang thang", "lo âu"],
        "ngu": ["ngủ", "ngu", "giấc ngủ", "mất ngủ", "mat ngu"],
        "dau": ["đau", "dau", "giảm đau", "nhức"],
        "sot": ["sốt", "sot", "hạ sốt", "fever"]
    }
    
    # Check which conditions are mentioned
    for condition_id, patterns in condition_patterns.items():
        for pattern in patterns:
            if pattern in metadata_lower or remove_diacritics(pattern) in remove_diacritics(metadata_lower):
                if condition_id not in detected_conditions:
                    detected_conditions[condition_id] = {
                        "names": patterns,
                        "mentioned_in": pattern
                    }
                break
    
    return detected_conditions


def build_taxonomy_from_data(json_file: str = None) -> tuple:
    """Build MEDICAL_CONDITIONS and PRODUCT_CONDITIONS from actual training data.
    
    Returns:
        (medical_conditions_dict, product_conditions_dict)
    """
    # Load training data
    if json_file is None:
        # Auto-detect path relative to this script
        script_dir = Path(__file__).parent.parent
        json_file = script_dir / "data" / "traning.json"
    
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"[ERROR] File not found: {json_file}")
        return {}, {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        products_data = json.load(f)
    
    # Track all conditions and which products treat them
    all_conditions = {}
    product_conditions = {}
    
    # Extract conditions from each product
    for item in products_data:
        product_name = item.get('name', 'Unknown')
        metadata = item.get('metadata', '')
        
        # Extract conditions mentioned for this product
        detected = extract_conditions_from_product(product_name, metadata)
        
        if detected:
            # Add to product_conditions mapping
            product_conditions[product_name] = {
                "primary_conditions": list(detected.keys()),
                "keywords": [cond["mentioned_in"] for cond in detected.values()],
                "description": metadata[:200]  # First 200 chars
            }
            
            # Add to all_conditions taxonomy
            for condition_id, condition_info in detected.items():
                if condition_id not in all_conditions:
                    all_conditions[condition_id] = {
                        "names": condition_info["names"],
                        "keywords": condition_info["names"],
                        "products": [product_name]
                    }
                else:
                    # Add product to this condition
                    if product_name not in all_conditions[condition_id]["products"]:
                        all_conditions[condition_id]["products"].append(product_name)
    
    return all_conditions, product_conditions


def save_taxonomy_to_file(output_file: str = None):
    """Generate Python file with auto-extracted taxonomy."""
    if output_file is None:
        # Auto-detect path relative to this script
        output_file = Path(__file__).parent / "medical_taxonomy_auto.py"
    
    conditions, products = build_taxonomy_from_data()
    
    # Generate Python code
    code = '''"""Auto-generated Medical Taxonomy from training data.

This file is AUTO-GENERATED by auto_extract_taxonomy.py
DO NOT EDIT MANUALLY - changes will be overwritten!

To regenerate: python -m rag_system.auto_extract_taxonomy
"""

import unicodedata
from typing import List, Dict, Optional, Tuple


def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics from text."""
    nfd = unicodedata.normalize('NFD', text)
    without_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    return without_diacritics


# ============================================================================
# AUTO-EXTRACTED MEDICAL CONDITIONS
# ============================================================================

MEDICAL_CONDITIONS = {\n'''
    
    # Add conditions
    for condition_id, info in conditions.items():
        code += f'    "{condition_id}": {{\n'
        code += f'        "names": {info["names"]},\n'
        code += f'        "keywords": {info["keywords"]},\n'
        code += f'        "products": {info["products"]}\n'
        code += f'    }},\n'
    
    code += '}\n\n'
    code += '# ============================================================================\n'
    code += '# AUTO-EXTRACTED PRODUCT-CONDITION MAPPINGS\n'
    code += '# ============================================================================\n\n'
    code += 'PRODUCT_CONDITIONS = {\n'
    
    # Add products
    for product_name, info in products.items():
        code += f'    "{product_name}": {{\n'
        code += f'        "primary_conditions": {info["primary_conditions"]},\n'
        code += f'        "keywords": {info["keywords"][:5]},  # Top 5 keywords\n'
        code += f'        "description": """{info["description"]}..."""\n'
        code += f'    }},\n'
    
    code += '}\n\n'
    
    # Add detection functions (copy from original)
    code += '''
def detect_medical_condition(query: str) -> Optional[Tuple[str, Dict]]:
    """Detect medical condition from user query."""
    query_lower = query.lower()
    query_no_diacritics = remove_diacritics(query_lower)
    
    best_match = None
    best_score = 0
    
    for condition_id, condition_info in MEDICAL_CONDITIONS.items():
        for name in condition_info["names"]:
            name_lower = name.lower()
            name_no_diacritics = remove_diacritics(name_lower)
            
            if name_lower in query_lower:
                return (condition_id, condition_info)
            
            if name_no_diacritics in query_no_diacritics:
                return (condition_id, condition_info)
        
        for keyword in condition_info["keywords"]:
            keyword_lower = keyword.lower()
            keyword_no_diacritics = remove_diacritics(keyword_lower)
            
            if keyword_lower in query_lower or keyword_no_diacritics in query_no_diacritics:
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = (condition_id, condition_info)
    
    return best_match


def find_products_for_condition(condition_id: str) -> List[str]:
    """Find all products that treat a specific medical condition."""
    condition_info = MEDICAL_CONDITIONS.get(condition_id)
    if condition_info:
        return condition_info.get("products", [])
    return []


def detect_condition_and_products(query: str) -> Optional[Dict]:
    """Complete pipeline: Detect condition and find matching products."""
    condition_match = detect_medical_condition(query)
    
    if not condition_match:
        return None
    
    condition_id, condition_info = condition_match
    products = condition_info.get("products", [])
    
    if not products:
        return None
    
    return {
        "condition_id": condition_id,
        "condition_name": condition_info["names"][0],
        "products": products,
        "query_type": "condition_search"
    }
'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"[OK] Generated taxonomy file: {output_file}")
    print(f"[INFO] Extracted {len(conditions)} conditions from {len(products)} products")
    print("\nConditions found:")
    for condition_id, info in conditions.items():
        print(f"  - {condition_id}: {', '.join(info['products'])}")


if __name__ == "__main__":
    print("Auto-extracting medical taxonomy from training data...")
    print("="*70)
    
    save_taxonomy_to_file()
    
    print("\nDone! Now update rag_chain.py to import from medical_taxonomy_auto")
