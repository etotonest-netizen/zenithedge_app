"""
Test ZenBot Knowledge Base Integration
Tests the integration between ZenBot and Knowledge Engine v2.0
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from bot.kb_integration import (
    answer_trading_question,
    get_strategy_explanation,
    search_knowledge_base
)

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{CYAN}{BOLD}{'='*80}{RESET}")
    print(f"{CYAN}{BOLD}{text:^80}{RESET}")
    print(f"{CYAN}{BOLD}{'='*80}{RESET}\n")


def print_test(test_name):
    """Print test name"""
    print(f"{BLUE}▶ TEST: {test_name}{RESET}")


def print_result(result):
    """Print KB result in formatted way"""
    print(f"\n{YELLOW}Answer:{RESET}")
    print(result['answer'])
    print(f"\n{YELLOW}Confidence:{RESET} {result['confidence']:.1f}%")
    
    if result.get('strategy'):
        print(f"{YELLOW}Strategy:{RESET} {result['strategy']}")
    
    if result.get('related_concepts'):
        print(f"{YELLOW}Related:{RESET} {', '.join(result['related_concepts'][:5])}")
    
    if result.get('sources'):
        print(f"{YELLOW}Sources:{RESET} {len(result['sources'])} source(s)")
    
    print()


def run_tests():
    """Run comprehensive integration tests"""
    
    print_header("ZENBOT KNOWLEDGE BASE INTEGRATION TESTS")
    
    # Test 1: Basic "What is" question
    print_test("Basic Definition Question")
    result = answer_trading_question("What is an order block?")
    print_result(result)
    test1_pass = result['confidence'] > 0 and len(result['answer']) > 100
    print(f"Status: {GREEN}✓ PASS{RESET}" if test1_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 2: "How to" question
    print_test("How-To Question")
    result = answer_trading_question("How do I trade a fair value gap?")
    print_result(result)
    test2_pass = result['confidence'] > 0 and 'step' in result['answer'].lower()
    print(f"Status: {GREEN}✓ PASS{RESET}" if test2_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 3: "When" timing question
    print_test("Timing Question")
    result = answer_trading_question("When should I enter after a liquidity sweep?")
    print_result(result)
    test3_pass = result['confidence'] > 0
    print(f"Status: {GREEN}✓ PASS{RESET}" if test3_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 4: "Why" question
    print_test("Why Question")
    result = answer_trading_question("Why do order blocks work?")
    print_result(result)
    test4_pass = result['confidence'] > 0
    print(f"Status: {GREEN}✓ PASS{RESET}" if test4_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 5: Comparison question
    print_test("Comparison Question")
    result = answer_trading_question("What's the difference between SMC and ICT?")
    print_result(result)
    test5_pass = result['confidence'] > 0
    print(f"Status: {GREEN}✓ PASS{RESET}" if test5_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 6: Strategy overview
    print_test("Strategy Overview")
    result = get_strategy_explanation('smc')
    print_result(result)
    test6_pass = result['confidence'] > 0 and 'smart money' in result['answer'].lower()
    print(f"Status: {GREEN}✓ PASS{RESET}" if test6_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 7: Direct KB search
    print_test("Direct Knowledge Base Search")
    results = search_knowledge_base("liquidity", strategy_filter="smc", limit=3)
    print(f"\n{YELLOW}Found {len(results)} results:{RESET}")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['entry'].term} (similarity: {r['similarity']:.3f})")
    test7_pass = len(results) > 0
    print(f"\nStatus: {GREEN}✓ PASS{RESET}" if test7_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 8: Non-trading question (should fall back)
    print_test("Non-Trading Question (Fallback Test)")
    result = answer_trading_question("What is the weather like?")
    print_result(result)
    test8_pass = result['confidence'] == 0  # Should not match
    print(f"Status: {GREEN}✓ PASS{RESET}" if test8_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 9: Complex multi-concept question
    print_test("Complex Multi-Concept Question")
    result = answer_trading_question("How do order blocks and fair value gaps work together?")
    print_result(result)
    test9_pass = result['confidence'] > 0
    print(f"Status: {GREEN}✓ PASS{RESET}" if test9_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Test 10: Strategy-specific question
    print_test("Strategy-Specific Question")
    result = answer_trading_question("Tell me about ICT trading concepts")
    print_result(result)
    test10_pass = result['confidence'] > 0
    print(f"Status: {GREEN}✓ PASS{RESET}" if test10_pass else f"Status: {RED}✗ FAIL{RESET}")
    
    # Summary
    print_header("TEST SUMMARY")
    
    tests = [
        ("Basic Definition", test1_pass),
        ("How-To Question", test2_pass),
        ("Timing Question", test3_pass),
        ("Why Question", test4_pass),
        ("Comparison Question", test5_pass),
        ("Strategy Overview", test6_pass),
        ("Direct KB Search", test7_pass),
        ("Fallback Test", test8_pass),
        ("Multi-Concept Question", test9_pass),
        ("Strategy-Specific", test10_pass),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"{BOLD}Results:{RESET}\n")
    for name, result in tests:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"  {name:30s} {status}")
    
    print(f"\n{BOLD}Total: {passed}/{total} tests passed ({passed/total*100:.0f}%){RESET}\n")
    
    if passed == total:
        print(f"{GREEN}{BOLD}🎉 All tests passed! ZenBot KB integration is fully operational!{RESET}")
    elif passed >= total * 0.7:
        print(f"{YELLOW}{BOLD}⚠️  Most tests passed. Some issues need attention.{RESET}")
    else:
        print(f"{RED}{BOLD}❌ Multiple test failures. Integration needs debugging.{RESET}")
    
    print()
    
    # Integration recommendations
    print_header("INTEGRATION RECOMMENDATIONS")
    
    print(f"{BOLD}1. Update bot/views.py chat_api():{RESET}")
    print("   The Knowledge Base is now automatically queried via bot/logic.py")
    print("   No changes needed - integration is seamless!\n")
    
    print(f"{BOLD}2. Add KB-specific endpoints (optional):{RESET}")
    print("   POST /bot/kb/search - Direct KB search")
    print("   GET /bot/kb/strategy/<name> - Strategy overview")
    print("   GET /bot/kb/concepts - List all concepts\n")
    
    print(f"{BOLD}3. Update frontend UI:{RESET}")
    print("   • Show confidence scores for KB answers")
    print("   • Display related concepts as clickable links")
    print("   • Add 'Explain this' button for deeper dives")
    print("   • Show strategy badges (SMC, ICT, etc.)\n")
    
    print(f"{BOLD}4. Populate Knowledge Base:{RESET}")
    print("   Current: 5 entries (test data)")
    print("   Target: 100+ entries for production")
    print("   Use: python3 manage.py shell")
    print("   Then: from knowledge_engine.enhanced_scraper import EnhancedKnowledgeScraper")
    print("         scraper = EnhancedKnowledgeScraper()")
    print("         scraper.scrape_web_page('URL', 'smc')\n")
    
    print(f"{BOLD}5. Enable in ZenBot settings:{RESET}")
    print("   Set BotSettings.enable_knowledge_base = True (if not already)")
    print("   Adjust confidence thresholds as needed\n")


if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"\n{RED}{BOLD}ERROR: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
