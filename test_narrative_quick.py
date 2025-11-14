#!/usr/bin/env python3
"""
Quick test of narrative composer to verify unique output generation.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from zenbot.narrative_composer import NarrativeComposer

# Initialize composer
composer = NarrativeComposer()

# Test signal contexts
test_signals = [
    {
        'symbol': 'GBPUSD',
        'side': 'sell',
        'strategy': 'smc',
        'price': 1.265,
        'session': 'london',
        'regime': 'ranging',
        'confidence': 88,
        'truth_index': 81
    },
    {
        'symbol': 'EURUSD',
        'side': 'buy',
        'strategy': 'ict',
        'price': 1.085,
        'session': 'newyork',
        'regime': 'trending',
        'confidence': 92,
        'truth_index': 87
    },
    {
        'symbol': 'GBPUSD',
        'side': 'sell',
        'strategy': 'smc',
        'price': 1.265,
        'session': 'london',
        'regime': 'ranging',
        'confidence': 88,
        'truth_index': 81
    }
]

# Mock KB hits
kb_hits = [
    {
        'term': 'Smart Money Concepts',
        'definition': 'Trading methodology based on institutional order flow',
        'summary': 'Focus on market structure breaks and liquidity',
        'related_concepts': ['Order Blocks', 'Fair Value Gaps'],
        'market_behavior_patterns': ['CHoCH', 'BOS'],
        'similarity': 0.95
    },
    {
        'term': 'Liquidity Sweep',
        'definition': 'Price movement that triggers stop losses before reversal',
        'summary': 'Institutional traders hunt liquidity before entry',
        'related_concepts': ['Stop Loss Hunting', 'Premium/Discount'],
        'market_behavior_patterns': ['Wick formation', 'False breakout'],
        'similarity': 0.89
    }
]

print("=" * 80)
print("NARRATIVE COMPOSER TEST - Uniqueness Verification")
print("=" * 80)
print()

narratives = []
for i, signal in enumerate(test_signals, 1):
    print(f"\n{'─' * 80}")
    print(f"TEST {i}: {signal['symbol']} {signal['side'].upper()} - {signal['strategy'].upper()}")
    print(f"{'─' * 80}")
    
    result = composer.generate_narrative(
        signal_context=signal,
        knowledge_hits=kb_hits,
        tone='analytical'
    )
    
    narrative = result['narrative']
    narratives.append(narrative)
    
    print(f"\n📝 NARRATIVE:")
    print(f"{narrative}")
    print(f"\n📊 METRICS:")
    print(f"   Insight Index: {result['insight_index']*100:.0f}%")
    print(f"   Uniqueness: {result['linguistic_uniqueness']*100:.0f}%")
    print(f"   Generation Time: {result['generation_time_ms']}ms")
    print(f"   Confidence: {result['confidence']*100:.0f}%")

# Compare similarity between narratives
print(f"\n\n{'=' * 80}")
print("UNIQUENESS ANALYSIS")
print("=" * 80)

# Simple word overlap check
def calculate_overlap(text1, text2):
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    overlap = words1.intersection(words2)
    total = words1.union(words2)
    return len(overlap) / len(total) * 100 if total else 0

for i in range(len(narratives)):
    for j in range(i+1, len(narratives)):
        overlap = calculate_overlap(narratives[i], narratives[j])
        print(f"\nNarrative {i+1} vs {j+1}:")
        print(f"   Word Overlap: {overlap:.1f}%")
        if overlap > 70:
            print(f"   ⚠️  HIGH SIMILARITY DETECTED!")
        elif overlap > 50:
            print(f"   ⚡ Moderate similarity (acceptable)")
        else:
            print(f"   ✅ Good uniqueness")

print(f"\n{'=' * 80}")
print("Test Complete!")
print("=" * 80)
