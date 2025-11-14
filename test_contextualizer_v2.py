"""
Test Enhanced Contextualizer v2.0 with Knowledge Engine Integration
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from zenbot.contextualizer_v2 import EnhancedContextualIntelligenceEngine, generate_narrative

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


def test_basic_narrative():
    """Test 1: Basic narrative generation"""
    print_test("Basic Narrative Generation")
    
    signal_data = {
        'symbol': 'EURUSD',
        'side': 'buy',
        'strategy': 'smc',
        'confidence': 82,
        'price': 1.0850,
        'sl': 1.0820,
        'tp': 1.0920,
        'regime': 'trending',
        'session': 'london'
    }
    
    validation_result = {
        'truth_index': 85.5,
        'status': 'approved',
        'breakdown': {
            'structure': 90,
            'momentum': 85,
            'sentiment': 80
        }
    }
    
    narrative = generate_narrative(signal_data, validation_result, use_kb=True)
    
    print(f"\n{YELLOW}Generated Narrative:{RESET}")
    print(narrative)
    print()
    
    # Checks
    checks = [
        ('Contains symbol', 'EURUSD' in narrative),
        ('Contains confidence/TI', '85' in narrative or '86' in narrative),
        ('Contains strategy', 'SMC' in narrative.upper()),
        ('Contains price action', '1.08' in narrative),
        ('Has minimum length', len(narrative) > 200),
        ('Has KB footer', '🔍' in narrative or 'KB' in narrative or 'Related' in narrative)
    ]
    
    all_pass = all(check[1] for check in checks)
    
    for check_name, passed in checks:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {check_name}")
    
    return all_pass


def test_linguistic_variation():
    """Test 2: Linguistic variation across multiple calls"""
    print_test("Linguistic Variation (No Repetition)")
    
    signal_data = {
        'symbol': 'GBPUSD',
        'side': 'sell',
        'strategy': 'ict',
        'confidence': 78,
        'price': 1.2650,
        'sl': 1.2680,
        'tp': 1.2580,
        'regime': 'volatile',
        'session': 'newyork'
    }
    
    validation_result = {
        'truth_index': 77.0,
        'status': 'approved',
        'breakdown': {}
    }
    
    narratives = []
    for i in range(5):
        narrative = generate_narrative(signal_data, validation_result, use_kb=True)
        narratives.append(narrative)
    
    # Check uniqueness
    unique_narratives = set(narratives)
    uniqueness_pct = (len(unique_narratives) / len(narratives)) * 100
    
    print(f"\n{YELLOW}Uniqueness:{RESET} {len(unique_narratives)}/{len(narratives)} unique ({uniqueness_pct:.0f}%)")
    
    # Show samples
    print(f"\n{YELLOW}Sample 1 (first 200 chars):{RESET}")
    print(narratives[0][:200] + "...")
    
    print(f"\n{YELLOW}Sample 2 (first 200 chars):{RESET}")
    print(narratives[1][:200] + "...")
    
    passed = uniqueness_pct >= 80  # Allow some repetition in small sample
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"\n{status} - {uniqueness_pct:.0f}% unique (target: ≥80%)")
    
    return passed


def test_educational_context():
    """Test 3: Educational context inclusion"""
    print_test("Educational Context for Beginners")
    
    signal_data = {
        'symbol': 'USDJPY',
        'side': 'buy',
        'strategy': 'smc',
        'confidence': 85,
        'price': 150.50,
        'sl': 150.20,
        'tp': 151.00,
        'regime': 'trending',
        'session': 'asia'
    }
    
    validation_result = {
        'truth_index': 88.0,
        'status': 'approved',
        'breakdown': {}
    }
    
    engine = EnhancedContextualIntelligenceEngine()
    
    # Generate with education for intro level
    narrative = engine.generate_narrative(
        signal_data=signal_data,
        validation_result=validation_result,
        user_level='intro',
        include_education=True
    )
    
    print(f"\n{YELLOW}Narrative with Educational Context:{RESET}")
    print(narrative)
    print()
    
    # Check for educational markers
    has_education = '📚' in narrative or 'Key Concept' in narrative or 'concept' in narrative.lower()
    has_kb_footer = '🔍' in narrative or 'KB' in narrative
    
    checks = [
        ('Contains educational section', has_education),
        ('Contains KB metadata', has_kb_footer),
        ('Appropriate length', len(narrative) > 250)
    ]
    
    all_pass = all(check[1] for check in checks)
    
    for check_name, passed in checks:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {check_name}")
    
    return all_pass


def test_fallback_mechanism():
    """Test 4: Graceful fallback to v1.0"""
    print_test("Fallback Mechanism (v1.0 compatibility)")
    
    signal_data = {
        'symbol': 'BTCUSD',
        'side': 'buy',
        'strategy': 'breakout',
        'confidence': 75,
        'price': 35000,
        'sl': 34500,
        'tp': 36000,
        'regime': 'volatile'
    }
    
    validation_result = {
        'truth_index': 72.0,
        'status': 'approved',
        'breakdown': {}
    }
    
    # Test with use_kb=False (should use v1.0)
    narrative_v1 = generate_narrative(signal_data, validation_result, use_kb=False)
    
    print(f"\n{YELLOW}v1.0 Fallback Narrative:{RESET}")
    print(narrative_v1)
    print()
    
    # Should still work
    checks = [
        ('Generated successfully', len(narrative_v1) > 50),
        ('Contains symbol', 'BTC' in narrative_v1 or '35000' in narrative_v1),
        ('Has basic structure', 'setup' in narrative_v1.lower() or 'detected' in narrative_v1.lower())
    ]
    
    all_pass = all(check[1] for check in checks)
    
    for check_name, passed in checks:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {check_name}")
    
    return all_pass


def test_batch_generation():
    """Test 5: Batch narrative generation"""
    print_test("Batch Narrative Generation")
    
    signals = [
        (
            {'symbol': 'EURUSD', 'side': 'buy', 'strategy': 'smc', 'confidence': 80,
             'price': 1.0850, 'sl': 1.0820, 'tp': 1.0920, 'regime': 'trending'},
            {'truth_index': 82.0, 'status': 'approved', 'breakdown': {}}
        ),
        (
            {'symbol': 'GBPUSD', 'side': 'sell', 'strategy': 'ict', 'confidence': 75,
             'price': 1.2650, 'sl': 1.2680, 'tp': 1.2580, 'regime': 'ranging'},
            {'truth_index': 76.0, 'status': 'approved', 'breakdown': {}}
        ),
        (
            {'symbol': 'USDJPY', 'side': 'buy', 'strategy': 'trend', 'confidence': 85,
             'price': 150.50, 'sl': 150.20, 'tp': 151.00, 'regime': 'trending'},
            {'truth_index': 87.0, 'status': 'approved', 'breakdown': {}}
        )
    ]
    
    engine = EnhancedContextualIntelligenceEngine()
    narratives = engine.generate_narrative_batch(signals, user_level='intermediate')
    
    print(f"\n{YELLOW}Generated {len(narratives)} narratives{RESET}")
    
    for i, narrative in enumerate(narratives, 1):
        print(f"\n{YELLOW}Narrative {i} (first 150 chars):{RESET}")
        print(narrative[:150] + "...")
    
    # Checks
    checks = [
        ('Correct count', len(narratives) == 3),
        ('All non-empty', all(len(n) > 100 for n in narratives)),
        ('Contains symbols', any('EURUSD' in n for n in narratives)),
        ('Different narratives', len(set(narratives)) >= 2)  # At least 2 unique
    ]
    
    all_pass = all(check[1] for check in checks)
    
    print()
    for check_name, passed in checks:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {check_name}")
    
    return all_pass


def test_kb_stats():
    """Test 6: KB statistics and metadata"""
    print_test("KB Statistics & Metadata")
    
    engine = EnhancedContextualIntelligenceEngine()
    stats = engine.get_linguistic_stats()
    
    print(f"\n{YELLOW}Linguistic Stats:{RESET}")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    checks = [
        ('Engine version is 2.0', stats.get('engine_version') == '2.0'),
        ('KB powered flag', stats.get('kb_powered') == True),
        ('Has template memory', 'max_template_memory' in stats),
        ('Status operational', stats.get('status') == 'operational')
    ]
    
    all_pass = all(check[1] for check in checks)
    
    print()
    for check_name, passed in checks:
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {check_name}")
    
    return all_pass


def run_all_tests():
    """Run all contextualizer v2.0 tests"""
    print_header("ENHANCED CONTEXTUALIZER V2.0 TESTS")
    
    tests = [
        ("Basic Narrative Generation", test_basic_narrative),
        ("Linguistic Variation", test_linguistic_variation),
        ("Educational Context", test_educational_context),
        ("Fallback Mechanism", test_fallback_mechanism),
        ("Batch Generation", test_batch_generation),
        ("KB Statistics", test_kb_stats)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{RED}ERROR in {test_name}: {e}{RESET}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"{BOLD}Results:{RESET}\n")
    for test_name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"  {test_name:40s} {status}")
    
    print(f"\n{BOLD}Total: {passed}/{total} tests passed ({passed/total*100:.0f}%){RESET}\n")
    
    if passed == total:
        print(f"{GREEN}{BOLD}🎉 All tests passed! Contextualizer v2.0 is operational!{RESET}")
    elif passed >= total * 0.8:
        print(f"{YELLOW}{BOLD}⚠️  Most tests passed. Minor issues to address.{RESET}")
    else:
        print(f"{RED}{BOLD}❌ Multiple test failures. Debugging needed.{RESET}")
    
    print()
    
    # Integration notes
    print_header("INTEGRATION NOTES")
    
    print(f"{BOLD}1. Update signal processing:{RESET}")
    print("   Replace: from zenbot.contextualizer import generate_narrative")
    print("   With:    from zenbot.contextualizer_v2 import generate_narrative\n")
    
    print(f"{BOLD}2. Backward compatibility:{RESET}")
    print("   Use use_kb=False parameter to fall back to v1.0")
    print("   Example: generate_narrative(signal, validation, use_kb=False)\n")
    
    print(f"{BOLD}3. User levels:{RESET}")
    print("   'intro' - Beginners (detailed explanations)")
    print("   'intermediate' - Default (balanced detail)")
    print("   'advanced' - Experts (concise, technical)\n")
    
    print(f"{BOLD}4. Educational mode:{RESET}")
    print("   Set include_education=True for learning insights")
    print("   Adds concept explanations to narratives\n")
    
    print(f"{BOLD}5. Performance:{RESET}")
    print("   Use generate_narrative_batch() for multiple signals")
    print("   Skips education by default for faster processing\n")


if __name__ == '__main__':
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n{RED}{BOLD}FATAL ERROR: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
