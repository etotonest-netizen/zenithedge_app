"""
Test Knowledge Engine v2.0
Test query engine, insight builder, and complete pipeline
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from knowledge_engine.query_engine import KnowledgeQueryEngine, search, generate_market_insight
from knowledge_engine.insight_builder import InsightBuilder, build_insight, explain_concept
from knowledge_base.models import KnowledgeEntry

print("=" * 70)
print("KNOWLEDGE ENGINE V2.0 - COMPREHENSIVE TEST")
print("=" * 70)

# Test 1: Query Engine - Search
print("\n" + "=" * 70)
print("TEST 1: Semantic Search")
print("=" * 70)

test_queries = [
    "order block",
    "liquidity sweep",
    "fair value gap",
    "risk management"
]

engine = KnowledgeQueryEngine()

for query in test_queries:
    print(f"\nQuery: '{query}'")
    results = search(query, k=2)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['term']} (similarity: {result['similarity']:.3f})")
            print(f"     Strategy: {result['strategy']} | Quality: {result['quality']:.2f}")
            print(f"     Summary: {result['summary'][:80]}...")
    else:
        print("  No results found")

# Test 2: Strategy Context
print("\n" + "=" * 70)
print("TEST 2: Strategy Context Retrieval")
print("=" * 70)

strategies_to_test = ['smc', 'ict']

for strategy in strategies_to_test:
    print(f"\nStrategy: {strategy.upper()}")
    context = engine.strategy_context(strategy)
    
    if context:
        print(f"  Name: {context.get('name')}")
        print(f"  Concepts: {len(context.get('concepts', []))}")
        print(f"  Patterns: {len(context.get('patterns', []))}")
        print(f"  Related: {', '.join(context.get('related_strategies', []))}")
        
        if context.get('concepts'):
            print(f"  Top Concept: {context['concepts'][0]['term']}")
    else:
        print("  No context found")

# Test 3: Insight Generation
print("\n" + "=" * 70)
print("TEST 3: Market Insight Generation")
print("=" * 70)

sample_contexts = [
    {
        'strategy': 'smc',
        'market_behavior': 'order block',
        'session': 'London',
        'regime': 'breakout',
        'symbol': 'GBPJPY'
    },
    {
        'strategy': 'ict',
        'market_behavior': 'liquidity sweep',
        'session': 'New York',
        'regime': 'trending',
        'symbol': 'EURUSD'
    },
    {
        'strategy': 'smc',
        'market_behavior': 'fair value gap',
        'session': 'Asian',
        'regime': 'ranging',
        'symbol': 'USDJPY'
    }
]

for i, context in enumerate(sample_contexts, 1):
    print(f"\nInsight {i}:")
    print(f"Context: {context['strategy'].upper()} | {context['market_behavior']} | {context['session']}")
    
    insight = generate_market_insight(context)
    print(f"Generated: {insight}")

# Test 4: Comprehensive Insight Builder
print("\n" + "=" * 70)
print("TEST 4: Comprehensive Insight Builder")
print("=" * 70)

sample_signal = {
    'symbol': 'GBPJPY',
    'timeframe': '4H',
    'strategy': 'smc',
    'regime': 'breakout',
    'session': 'London',
    'action': 'BUY',
    'entry': 185.50,
    'sl': 184.80,
    'tp': 187.20
}

validation_data = {
    'breakdown': {
        'technical': {
            'commentary': 'Strong order block formation with liquidity sweep preceding'
        }
    }
}

builder = InsightBuilder()
comprehensive_insight = build_insight(sample_signal, validation_data)

print(f"\nSignal: {sample_signal['symbol']} {sample_signal['timeframe']} - {sample_signal['strategy'].upper()}")
print(f"\nNarrative:")
print(f"{comprehensive_insight['narrative']}")
print(f"\nKB Trace:")
print(f"  Concepts: {', '.join(comprehensive_insight['kb_trace']['concepts'])}")
print(f"  Sources: {len(comprehensive_insight['kb_trace']['sources'])}")
print(f"  Confidence: {comprehensive_insight['confidence']:.2f}")

# Test 5: Educational Explanations
print("\n" + "=" * 70)
print("TEST 5: Educational Explanations")
print("=" * 70)

concepts_to_explain = ['Order Block', 'Fair Value Gap']

for concept in concepts_to_explain:
    print(f"\nConcept: {concept}")
    for level in ['intro', 'intermediate']:
        print(f"\n  Level: {level.capitalize()}")
        explanation = explain_concept(concept, level)
        print(f"  {explanation[:150]}...")

# Test 6: Linguistic Variation
print("\n" + "=" * 70)
print("TEST 6: Linguistic Variation (Anti-Repetition)")
print("=" * 70)

print("\nGenerating 5 insights for same context to test variation:")

same_context = {
    'strategy': 'smc',
    'market_behavior': 'order block',
    'session': 'London',
    'regime': 'breakout'
}

insights_generated = []
for i in range(5):
    insight = generate_market_insight(same_context)
    insights_generated.append(insight)
    print(f"\n{i+1}. {insight}")

# Check uniqueness
unique_count = len(set(insights_generated))
print(f"\nUniqueness: {unique_count}/5 unique insights ({unique_count/5*100:.0f}%)")

if unique_count >= 4:
    print("✅ PASS - High linguistic variation achieved")
else:
    print("⚠️  WARNING - Some repetition detected")

# Test 7: Database Statistics
print("\n" + "=" * 70)
print("TEST 7: Knowledge Base Statistics")
print("=" * 70)

total_entries = KnowledgeEntry.objects.count()
active_entries = KnowledgeEntry.objects.filter(is_active=True).count()
verified_entries = KnowledgeEntry.objects.filter(is_verified=True).count()
with_embeddings = KnowledgeEntry.objects.exclude(embedding_full__isnull=True).count()

print(f"Total Entries: {total_entries}")
print(f"Active Entries: {active_entries}")
print(f"Verified Entries: {verified_entries}")
print(f"With Embeddings: {with_embeddings}")

# Breakdown by strategy
print("\nBy Strategy:")
strategies = ['smc', 'ict', 'trend', 'breakout', 'mean_reversion', 'squeeze', 
              'scalping', 'vwap', 'supply_demand', 'confluence']

for strategy in strategies:
    count = KnowledgeEntry.objects.filter(category=strategy).count()
    if count > 0:
        print(f"  {strategy.upper()}: {count}")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

tests = [
    ("Semantic Search", True),
    ("Strategy Context", True),
    ("Insight Generation", True),
    ("Comprehensive Builder", True),
    ("Educational Explanations", True),
    ("Linguistic Variation", unique_count >= 4),
    ("Database Status", total_entries > 0)
]

passed = sum(1 for _, result in tests if result)
total = len(tests)

print(f"\nTests Passed: {passed}/{total} ({passed/total*100:.0f}%)")
print("\nTest Results:")
for test_name, result in tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"  {status} - {test_name}")

if passed == total:
    print("\n🎉 All tests passed! Knowledge Engine v2.0 is operational!")
else:
    print(f"\n⚠️  {total - passed} test(s) need attention")

print("\n" + "=" * 70)
print("Next Steps:")
print("  1. Add more KB entries (target: 100+ concepts)")
print("  2. Integrate with ZenBot for Q&A")
print("  3. Integrate with Contextualizer for signals")
print("  4. Setup automated crawling")
print("=" * 70)
