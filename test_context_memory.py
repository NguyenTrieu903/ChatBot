"""Test script to verify chat context memory works correctly.

This tests the fix for the issue where asking "giá bao nhiêu?" after 
"The Fucoidan là gì?" didn't work because retriever didn't have context.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

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


def test_context_memory():
    """Test chat context memory - follow-up questions should work."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: Chat Context Memory (Query Enhancement){RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    # Initialize
    if not os.getenv("GROQ_API_KEY"):
        print(f"{RED}❌ ERROR: GROQ_API_KEY not found in .env{RESET}")
        return False
    
    rag_chain = RetrievalChain(use_case="vietnamese_support", k=5)
    
    # Test conversation flow
    print(f"\n{YELLOW}Conversation Flow:{RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    
    # Question 1: Ask about product
    q1 = "The Fucoidan là gì?"
    print(f"\n👤 User: {q1}")
    
    response1 = rag_chain.chat(q1)
    answer1 = response1['answer']
    
    print(f"🤖 Bot: {answer1[:200]}...")
    
    # Check if first question got answer
    has_info = "fucoidan" in answer1.lower() and len(answer1) > 100
    if has_info:
        print(f"{GREEN}✅ First question answered correctly{RESET}")
    else:
        print(f"{RED}❌ First question not answered properly{RESET}")
        return False
    
    # Question 2: Follow-up about price (vague question)
    q2 = "Giá bao nhiêu?"
    print(f"\n👤 User: {q2}")
    print(f"{YELLOW}(Note: This is a vague question - should use context from Q1){RESET}")
    
    response2 = rag_chain.chat(q2)
    answer2 = response2['answer']
    
    print(f"🤖 Bot: {answer2[:200]}...")
    
    # Check if second question got answer (should NOT say "không tìm thấy")
    has_price = "2.200.000" in answer2 or "2,200,000" in answer2
    not_failed = "không tìm thấy" not in answer2.lower()
    
    if has_price and not_failed:
        print(f"{GREEN}✅ Follow-up question answered correctly (context preserved!){RESET}")
        success = True
    else:
        print(f"{RED}❌ Follow-up question failed (context not preserved){RESET}")
        print(f"{RED}   Expected: Price information about The Fucoidan{RESET}")
        print(f"{RED}   Got: {answer2[:100]}...{RESET}")
        success = False
    
    # Question 3: Another follow-up (dosage)
    q3 = "Liều dùng thế nào?"
    print(f"\n👤 User: {q3}")
    
    response3 = rag_chain.chat(q3)
    answer3 = response3['answer']
    
    print(f"🤖 Bot: {answer3[:200]}...")
    
    # Check if third question got answer
    has_dosage = "viên" in answer3.lower() and ("3" in answer3 or "6" in answer3)
    not_failed3 = "không tìm thấy" not in answer3.lower()
    
    if has_dosage and not_failed3:
        print(f"{GREEN}✅ Second follow-up answered correctly{RESET}")
    else:
        print(f"{RED}❌ Second follow-up failed{RESET}")
        success = False
    
    # Summary
    print(f"\n{YELLOW}{'='*70}{RESET}")
    if success:
        print(f"{GREEN}🎉 CONTEXT MEMORY TEST PASSED!{RESET}")
        print(f"{GREEN}✅ Bot remembers context from previous messages{RESET}")
        print(f"{GREEN}✅ Follow-up questions work correctly{RESET}")
    else:
        print(f"{RED}❌ CONTEXT MEMORY TEST FAILED{RESET}")
        print(f"{RED}⚠️  Follow-up questions don't work properly{RESET}")
    
    return success


def test_different_products():
    """Test context switching between different products."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST: Context Switching Between Products{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    rag_chain = RetrievalChain(use_case="vietnamese_support", k=5)
    
    # Ask about Product 1
    print(f"\n👤 User: The Fucoidan là gì?")
    response1 = rag_chain.chat("The Fucoidan là gì?")
    print(f"🤖 Bot: {response1['answer'][:150]}...")
    
    # Follow-up about Product 1
    print(f"\n👤 User: Giá bao nhiêu?")
    response2 = rag_chain.chat("Giá bao nhiêu?")
    answer2 = response2['answer']
    print(f"🤖 Bot: {answer2[:150]}...")
    
    has_price1 = "2.200.000" in answer2 or "2,200,000" in answer2
    
    # Switch to Product 2
    print(f"\n👤 User: β-Glucan Ball có tác dụng gì?")
    response3 = rag_chain.chat("β-Glucan Ball có tác dụng gì?")
    print(f"🤖 Bot: {response3['answer'][:150]}...")
    
    # Follow-up about Product 2 (should NOT give Product 1's price)
    print(f"\n👤 User: Giá của sản phẩm này là bao nhiêu?")
    response4 = rag_chain.chat("Giá của sản phẩm này là bao nhiêu?")
    answer4 = response4['answer']
    print(f"🤖 Bot: {answer4[:150]}...")
    
    has_price2 = "3.250.000" in answer4 or "3,250,000" in answer4
    not_price1 = "2.200.000" not in answer4 and "2,200,000" not in answer4
    
    if has_price1 and has_price2 and not_price1:
        print(f"\n{GREEN}✅ Context switching works correctly{RESET}")
        print(f"{GREEN}   - First follow-up got Product 1 price{RESET}")
        print(f"{GREEN}   - Second follow-up got Product 2 price (not Product 1){RESET}")
        return True
    else:
        print(f"\n{RED}❌ Context switching has issues{RESET}")
        return False


if __name__ == "__main__":
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}CHAT CONTEXT MEMORY TEST SUITE{RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    
    test1_pass = test_context_memory()
    test2_pass = test_different_products()
    
    print(f"\n{YELLOW}{'='*70}{RESET}")
    print(f"{YELLOW}FINAL RESULTS{RESET}")
    print(f"{YELLOW}{'='*70}{RESET}")
    
    if test1_pass:
        print(f"{GREEN}✅ Test 1: Context Memory - PASSED{RESET}")
    else:
        print(f"{RED}❌ Test 1: Context Memory - FAILED{RESET}")
    
    if test2_pass:
        print(f"{GREEN}✅ Test 2: Context Switching - PASSED{RESET}")
    else:
        print(f"{RED}❌ Test 2: Context Switching - FAILED{RESET}")
    
    if test1_pass and test2_pass:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}🎉 ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}✅ Chat context memory works correctly{RESET}")
        print(f"{GREEN}{'='*70}{RESET}")
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ SOME TESTS FAILED{RESET}")
        print(f"{RED}⚠️  Please check the implementation{RESET}")
        print(f"{RED}{'='*70}{RESET}")
