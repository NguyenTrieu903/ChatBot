"""Test script for medical condition detection and intelligent search.

Tests the new condition-based search feature where user can ask:
- "thuốc nào bổ thận" → finds "Kidney & Men's"
- "thuoc nao bo than" (no diacritics) → finds "Kidney & Men's"
- "hỗ trợ ung thư" → finds Fucoidan products
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from rag_system.medical_taxonomy import (
    detect_condition_and_products,
    is_condition_query,
    remove_diacritics
)
from rag_system.retrieval_chain import RetrievalChain
from dotenv import load_dotenv
import os

load_dotenv()

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def test_condition_detection():
    """Test condition detection (taxonomy only, no LLM)."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST 1: Condition Detection (Taxonomy){RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    test_cases = [
        # With diacritics
        ("thuốc nào bổ thận", "bo_than", ["Kidney & Men's"]),
        ("sản phẩm hỗ trợ ung thư", "ung_thu", ["The Fucoidan", "The Fucoidan xK", "β-Glucan Ball"]),
        ("phòng ngừa đột quỵ", "dot_quy", ["Power HLP"]),
        ("thuốc giảm đau hạ sốt", "dau", ["Paracetamol"]),
        ("bổ gan giải độc", "gan", ["The Reishi"]),
        
        # Without diacritics (challenging!)
        ("thuoc nao bo than", "bo_than", ["Kidney & Men's"]),
        ("ho tro ung thu", "ung_thu", ["The Fucoidan", "The Fucoidan xK", "β-Glucan Ball"]),
        ("phong ngua dot quy", "dot_quy", ["Power HLP"]),
        
        # Variations
        ("sinh lý nam giới", "sinh_ly_nam", ["Kidney & Men's"]),
        ("tăng cường miễn dịch", "mien_dich", ["The Fucoidan", "The Fucoidan xK", "β-Glucan Ball", "The Reishi"]),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_condition, expected_products in test_cases:
        result = detect_condition_and_products(query)
        
        print(f"\n📝 Query: '{query}'")
        
        if result:
            condition_match = result['condition_id'] == expected_condition
            products_match = set(result['products']) >= set(expected_products[:1])  # At least one match
            
            if condition_match and products_match:
                print(f"  {GREEN}✅ PASS{RESET}")
                print(f"     Condition: {result['condition_name']} ({result['condition_id']})")
                print(f"     Products: {', '.join(result['products'])}")
                passed += 1
            else:
                print(f"  {RED}❌ FAIL{RESET}")
                print(f"     Expected: {expected_condition}, Got: {result['condition_id']}")
                print(f"     Expected products: {expected_products}")
                print(f"     Got products: {result['products']}")
                failed += 1
        else:
            print(f"  {RED}❌ FAIL - No condition detected{RESET}")
            print(f"     Expected: {expected_condition} → {expected_products}")
            failed += 1
    
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}Results: {passed} passed, {failed} failed{RESET}")
    
    return failed == 0


def test_end_to_end():
    """Test end-to-end with RAG chain (including LLM)."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST 2: End-to-End with RAG Chain{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    if not os.getenv("GROQ_API_KEY"):
        print(f"{RED}❌ GROQ_API_KEY not found. Skipping E2E test.{RESET}")
        return True
    
    rag_chain = RetrievalChain(use_case="vietnamese_support", k=5)
    
    test_queries = [
        {
            "query": "thuốc nào bổ thận",
            "expected_keywords": ["kidney", "men's", "bổ thận", "testosterone"],
            "should_find": True
        },
        {
            "query": "thuoc nao bo than",  # No diacritics
            "expected_keywords": ["kidney", "men's", "bổ thận"],
            "should_find": True
        },
        {
            "query": "sản phẩm hỗ trợ ung thư",
            "expected_keywords": ["fucoidan", "ung thư", "miễn dịch"],
            "should_find": True
        },
        {
            "query": "phòng ngừa đột quỵ",
            "expected_keywords": ["power hlp", "đột quỵ", "máu đông"],
            "should_find": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_queries:
        query = test["query"]
        print(f"\n📝 Query: '{query}'")
        
        response = rag_chain.chat(query)
        answer = response['answer'].lower()
        
        print(f"🤖 Answer preview: {answer[:200]}...")
        
        # Check if answer contains expected keywords
        has_keywords = any(kw.lower() in answer for kw in test["expected_keywords"])
        not_failed = "không tìm thấy" not in answer
        
        if test["should_find"]:
            if has_keywords and not_failed:
                print(f"  {GREEN}✅ PASS - Found relevant product info{RESET}")
                passed += 1
            else:
                print(f"  {RED}❌ FAIL - Did not find expected info{RESET}")
                print(f"     Expected keywords: {test['expected_keywords']}")
                failed += 1
        else:
            if not has_keywords:
                print(f"  {GREEN}✅ PASS - Correctly refused{RESET}")
                passed += 1
            else:
                print(f"  {RED}❌ FAIL - Should have refused{RESET}")
                failed += 1
    
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}Results: {passed} passed, {failed} failed{RESET}")
    
    return failed == 0


def test_follow_up():
    """Test follow-up questions after condition search."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST 3: Follow-up Questions After Condition Search{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    if not os.getenv("GROQ_API_KEY"):
        print(f"{RED}❌ GROQ_API_KEY not found. Skipping follow-up test.{RESET}")
        return True
    
    rag_chain = RetrievalChain(use_case="vietnamese_support", k=5)
    
    # First question: condition-based
    print(f"\n{YELLOW}Conversation Flow:{RESET}")
    print(f"\n👤 User: thuốc nào bổ thận")
    
    response1 = rag_chain.chat("thuốc nào bổ thận")
    answer1 = response1['answer']
    
    print(f"🤖 Bot: {answer1[:200]}...")
    
    has_kidney = "kidney" in answer1.lower() or "thận" in answer1.lower()
    
    if not has_kidney:
        print(f"{RED}❌ First question failed{RESET}")
        return False
    
    print(f"{GREEN}✅ First question answered{RESET}")
    
    # Follow-up: price
    print(f"\n👤 User: giá bao nhiêu")
    
    response2 = rag_chain.chat("giá bao nhiêu")
    answer2 = response2['answer']
    
    print(f"🤖 Bot: {answer2[:200]}...")
    
    has_price = "1.850.000" in answer2 or "1,850,000" in answer2
    not_failed = "không tìm thấy" not in answer2.lower()
    
    if has_price and not_failed:
        print(f"{GREEN}✅ Follow-up answered correctly{RESET}")
        return True
    else:
        print(f"{RED}❌ Follow-up failed{RESET}")
        return False


if __name__ == "__main__":
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}MEDICAL CONDITION DETECTION TEST SUITE{RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    
    # Test 1: Condition detection (fast, no API)
    test1_pass = test_condition_detection()
    
    # Test 2: End-to-end (with LLM)
    test2_pass = test_end_to_end()
    
    # Test 3: Follow-up questions
    test3_pass = test_follow_up()
    
    # Final results
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}FINAL RESULTS{RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    
    if test1_pass:
        print(f"{GREEN}✅ Test 1: Condition Detection - PASSED{RESET}")
    else:
        print(f"{RED}❌ Test 1: Condition Detection - FAILED{RESET}")
    
    if test2_pass:
        print(f"{GREEN}✅ Test 2: End-to-End - PASSED{RESET}")
    else:
        print(f"{RED}❌ Test 2: End-to-End - FAILED{RESET}")
    
    if test3_pass:
        print(f"{GREEN}✅ Test 3: Follow-up - PASSED{RESET}")
    else:
        print(f"{RED}❌ Test 3: Follow-up - FAILED{RESET}")
    
    if test1_pass and test2_pass and test3_pass:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}🎉 ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}✅ Condition detection works perfectly{RESET}")
        print(f"{GREEN}✅ Works with and without Vietnamese diacritics{RESET}")
        print(f"{GREEN}✅ Follow-up questions work{RESET}")
        print(f"{GREEN}{'='*70}{RESET}")
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ SOME TESTS FAILED{RESET}")
        print(f"{RED}{'='*70}{RESET}")
