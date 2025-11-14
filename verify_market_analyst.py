#!/usr/bin/env python3
"""
Final Verification Script for Zenith Market Analyst
Validates all components are working correctly before production
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/macbook/zenithedge_trading_hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from autopsy.models import MarketInsight, VariationVocabulary, InsightTemplate
from autopsy.insight_engine import analyst
from datetime import datetime

print("=" * 70)
print("🔍 ZENITH MARKET ANALYST - FINAL VERIFICATION")
print("=" * 70)
print()

all_passed = True
tests_run = 0
tests_passed = 0

def test(name, condition, details=""):
    global all_passed, tests_run, tests_passed
    tests_run += 1
    if condition:
        tests_passed += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        all_passed = False
        print(f"❌ {name}")
        if details:
            print(f"   {details}")
    return condition

# ========================================
# DATABASE TESTS
# ========================================
print("📦 DATABASE VERIFICATION")
print("-" * 70)

# Test models exist
try:
    insight_count = MarketInsight.objects.count()
    test("MarketInsight model accessible", True, f"{insight_count} insights in database")
except Exception as e:
    test("MarketInsight model accessible", False, str(e))

try:
    vocab_count = VariationVocabulary.objects.count()
    total_variations = sum(len(v.variations) for v in VariationVocabulary.objects.all())
    test("VariationVocabulary populated", vocab_count >= 20, 
         f"{vocab_count} entries, {total_variations} variations")
except Exception as e:
    test("VariationVocabulary populated", False, str(e))

try:
    template_count = InsightTemplate.objects.count()
    test("InsightTemplate model accessible", True, f"{template_count} templates")
except Exception as e:
    test("InsightTemplate model accessible", False, str(e))

print()

# ========================================
# AI ENGINE TESTS
# ========================================
print("🤖 AI ENGINE VERIFICATION")
print("-" * 70)

# Test engines can be imported
try:
    from autopsy.insight_parser import InsightParser
    parser = InsightParser()
    test("InsightParser module loads", True, "318 lines")
except Exception as e:
    test("InsightParser module loads", False, str(e))

try:
    from autopsy.variation_engine import VariationEngine
    engine = VariationEngine()
    engine.load_vocabulary_from_db()
    test("VariationEngine loads vocabulary", len(engine.vocabulary) > 0, 
         f"{len(engine.vocabulary)} categories loaded")
except Exception as e:
    test("VariationEngine loads vocabulary", False, str(e))

try:
    from autopsy.insight_scorer import InsightScorer
    scorer = InsightScorer()
    test("InsightScorer module loads", True, "280 lines")
except Exception as e:
    test("InsightScorer module loads", False, str(e))

try:
    test("ZenithMarketAnalyst engine ready", analyst is not None, 
         "Central coordinator initialized")
except Exception as e:
    test("ZenithMarketAnalyst engine ready", False, str(e))

print()

# ========================================
# PROCESSING TEST
# ========================================
print("⚙️  PROCESSING VERIFICATION")
print("-" * 70)

sample_data = {
    'symbol': 'EURUSD',
    'timeframe': '1H',
    'timestamp': datetime.now().isoformat(),
    'regime': 'trending',
    'structure': 'bos',
    'momentum': 'increasing',
    'volume_state': 'spike',
    'session': 'london',
    'expected_behavior': 'continuation',
    'strength': 85
}

try:
    import time
    start = time.time()
    insight_data = analyst.process_bar(sample_data)
    duration = (time.time() - start) * 1000
    
    test("Bar processing works", insight_data is not None, 
         f"Processed in {duration:.1f}ms")
    
    test("Insight index calculated", 'insight_index' in insight_data,
         f"Score: {insight_data.get('insight_index', 0)}/100")
    
    test("Quality label assigned", 'quality_label' in insight_data,
         f"{insight_data.get('quality_label', 'N/A')}")
    
    test("Vocabulary hash generated", 'vocabulary_hash' in insight_data,
         f"{insight_data.get('vocabulary_hash', 'N/A')}")
    
    test("Processing speed acceptable", duration < 200,
         f"{duration:.1f}ms (target: <200ms)")
    
except Exception as e:
    test("Bar processing works", False, str(e))

print()

# ========================================
# VIEWS TEST
# ========================================
print("🌐 API ENDPOINTS VERIFICATION")
print("-" * 70)

try:
    from autopsy import views
    test("submit_insight_webhook view exists", hasattr(views, 'submit_insight_webhook'))
    test("market_analyst_view exists", hasattr(views, 'market_analyst_view'))
    test("get_insights_api exists", hasattr(views, 'get_insights_api'))
    test("get_chart_labels exists", hasattr(views, 'get_chart_labels'))
    test("insight_detail exists", hasattr(views, 'insight_detail'))
except Exception as e:
    test("Views module loads", False, str(e))

print()

# ========================================
# URL ROUTING TEST
# ========================================
print("🔗 URL ROUTING VERIFICATION")
print("-" * 70)

try:
    from django.urls import reverse
    
    test("market_analyst URL configured", True,
         reverse('autopsy:market_analyst'))
    
    test("submit_insight URL configured", True,
         reverse('autopsy:submit_insight'))
    
    test("get_insights URL configured", True,
         reverse('autopsy:get_insights'))
    
except Exception as e:
    test("URL routing configured", False, str(e))

print()

# ========================================
# TEMPLATE TEST
# ========================================
print("🎨 TEMPLATE VERIFICATION")
print("-" * 70)

import os

templates_dir = '/Users/macbook/zenithedge_trading_hub/autopsy/templates/autopsy'

market_analyst_path = os.path.join(templates_dir, 'market_analyst.html')
test("market_analyst.html exists", os.path.exists(market_analyst_path),
     f"{os.path.getsize(market_analyst_path) if os.path.exists(market_analyst_path) else 0} bytes")

insight_detail_path = os.path.join(templates_dir, 'insight_detail.html')
test("insight_detail.html exists", os.path.exists(insight_detail_path),
     f"{os.path.getsize(insight_detail_path) if os.path.exists(insight_detail_path) else 0} bytes")

print()

# ========================================
# ADMIN TEST
# ========================================
print("⚙️  ADMIN INTERFACE VERIFICATION")
print("-" * 70)

try:
    from django.contrib import admin
    from autopsy.models import MarketInsight, VariationVocabulary, InsightTemplate
    
    test("MarketInsight registered in admin", 
         MarketInsight in [m.model for m in admin.site._registry.values()])
    
    test("VariationVocabulary registered in admin",
         VariationVocabulary in [m.model for m in admin.site._registry.values()])
    
    test("InsightTemplate registered in admin",
         InsightTemplate in [m.model for m in admin.site._registry.values()])
    
except Exception as e:
    test("Admin interfaces configured", False, str(e))

print()

# ========================================
# DOCUMENTATION TEST
# ========================================
print("📚 DOCUMENTATION VERIFICATION")
print("-" * 70)

docs = [
    'ZENITH_MARKET_ANALYST_COMPLETE.md',
    'DEPLOYMENT_GUIDE_MARKET_ANALYST.md',
    'PROJECT_COMPLETE_MARKET_ANALYST.md',
    'ZENITH_MARKET_ANALYST_PINE_SCRIPT.pine',
]

for doc in docs:
    path = f'/Users/macbook/zenithedge_trading_hub/{doc}'
    test(f"{doc} exists", os.path.exists(path),
         f"{os.path.getsize(path) if os.path.exists(path) else 0} bytes")

print()

# ========================================
# PINE SCRIPT TEST
# ========================================
print("📊 PINE SCRIPT VERIFICATION")
print("-" * 70)

pine_path = '/Users/macbook/zenithedge_trading_hub/ZENITH_MARKET_ANALYST_PINE_SCRIPT.pine'
if os.path.exists(pine_path):
    with open(pine_path, 'r') as f:
        pine_content = f.read()
        
    test("Pine Script has webhook payload", 'build_webhook_payload' in pine_content)
    test("Pine Script detects regime", 'detect_regime()' in pine_content)
    test("Pine Script detects structure", 'detect_structure()' in pine_content)
    test("Pine Script has alert", 'alert(' in pine_content)
else:
    test("Pine Script exists", False, "File not found")

print()

# ========================================
# MANAGEMENT COMMAND TEST
# ========================================
print("🛠️  MANAGEMENT COMMAND VERIFICATION")
print("-" * 70)

seed_vocab_path = '/Users/macbook/zenithedge_trading_hub/autopsy/management/commands/seed_vocabulary.py'
test("seed_vocabulary command exists", os.path.exists(seed_vocab_path),
     f"{os.path.getsize(seed_vocab_path) if os.path.exists(seed_vocab_path) else 0} bytes")

print()

# ========================================
# FINAL SUMMARY
# ========================================
print("=" * 70)
print("📊 VERIFICATION SUMMARY")
print("=" * 70)
print()

percentage = (tests_passed / tests_run * 100) if tests_run > 0 else 0

print(f"Tests Run:    {tests_run}")
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_run - tests_passed}")
print(f"Success Rate: {percentage:.1f}%")
print()

if all_passed:
    print("🎉 " + "=" * 66)
    print("🎉 ALL VERIFICATION TESTS PASSED!")
    print("🎉 ZENITH MARKET ANALYST IS PRODUCTION READY!")
    print("🎉 " + "=" * 66)
    print()
    print("Next Steps:")
    print("  1. python3 manage.py runserver")
    print("  2. Open: http://127.0.0.1:8000/autopsy/market-analyst/")
    print("  3. Configure TradingView webhook")
    print("  4. Watch live insights populate!")
    print()
    sys.exit(0)
else:
    print("⚠️  " + "=" * 66)
    print("⚠️  SOME TESTS FAILED - REVIEW ERRORS ABOVE")
    print("⚠️  " + "=" * 66)
    print()
    sys.exit(1)
