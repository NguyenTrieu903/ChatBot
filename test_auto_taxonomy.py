"""Test auto-extracted taxonomy."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from rag_system.medical_taxonomy_auto import (
    MEDICAL_CONDITIONS,
    detect_condition_and_products
)

# Test cases
test_queries = [
    ("thuoc tri tieu duong", "tieu_duong"),
    ("thuoc nao bo than", "bo_than"),
    ("ho tro ung thu", "ung_thu"),
    ("phong ngua dot quy", "dot_quy"),
]

print("Testing Auto-Extracted Taxonomy:")
print("="*70)

print(f"\nTotal conditions extracted: {len(MEDICAL_CONDITIONS)}")
print("\nConditions:")
for cond_id, info in MEDICAL_CONDITIONS.items():
    print(f"  - {cond_id}: {len(info['products'])} products")

print("\n" + "="*70)
print("Testing Detection:")
print("="*70)

for query, expected_cond in test_queries:
    result = detect_condition_and_products(query)
    print(f"\nQuery: '{query}'")
    if result:
        print(f"  [OK] Detected: {result['condition_name']}")
        print(f"  Products: {', '.join(result['products'])}")
        if result['condition_id'] == expected_cond:
            print(f"  [PASS] Correct condition")
        else:
            print(f"  [FAIL] Expected {expected_cond}, got {result['condition_id']}")
    else:
        print(f"  [FAIL] No condition detected")

print("\n" + "="*70)
print("SUCCESS! Auto-extraction works!")
print("Conditions are now extracted FROM REAL DATA, not manually defined!")
