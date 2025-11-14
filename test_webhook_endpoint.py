"""
Test Script for Zenith Market Analyst - Webhook Endpoint Simulation
Tests the complete pipeline without HTTP server
"""

import os
import sys
import django
from datetime import datetime
import json

# Setup Django environment
sys.path.append('/Users/macbook/zenithedge_trading_hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from autopsy.insight_engine import analyst
from autopsy.models import MarketInsight

print("=" * 70)
print("🚀 ZENITH MARKET ANALYST - WEBHOOK ENDPOINT TEST")
print("=" * 70)
print()

# Sample Pine Script payload (matching required fields)
sample_data = {
    'symbol': 'EURUSD',
    'timeframe': '1H',
    'timestamp': datetime.now().isoformat(),
    'regime': 'trending',
    'structure': 'bos',
    'momentum': 'increasing',
    'volume_state': 'spike',
    'session': 'london',
    'expected_behavior': 'continuation',  # Required field
    'strength': 85,  # Required field
    'metadata': {
        'liquidity_state': 'building',
        'structure_type': 'bos',
        'chart_labels': {
            'structure': 'BOS',
            'regime': 'Trending',
            'momentum': 'Momentum ↑',
            'volume': 'Volume Spike'
        }
    }
}

print("📦 Test Payload:")
print(json.dumps(sample_data, indent=2))
print()

print("🔄 Processing through Zenith Market Analyst...")
print()

try:
    # Process the bar data (simulating webhook endpoint logic)
    insight_data = analyst.process_bar(sample_data)
    
    print("✅ Step 1: Bar processed successfully")
    print(f"   - Insight Index: {insight_data['insight_index']}/100")
    print(f"   - Quality Label: {insight_data['quality_label']}")
    print()
    
    # Save to database
    insight = analyst.save_insight(insight_data)
    
    print("✅ Step 2: Insight saved to database")
    print(f"   - Insight ID: {insight.id}")
    print(f"   - Vocabulary Hash: {insight.vocabulary_hash}")
    print()
    
    # Display full insight
    print("=" * 70)
    print("📊 GENERATED INSIGHT")
    print("=" * 70)
    print(f"Symbol: {insight.symbol} {insight.timeframe}")
    print(f"Regime: {insight.get_regime_display()} | Structure: {insight.get_structure_display()}")
    print(f"Session: {insight.get_session_display()} | Time: {insight.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Insight Index: {insight.insight_index}/100 ({insight_data['quality_label']})")
    print()
    print("Insight Text:")
    print(f"  {insight.insight_text}")
    print()
    print("Suggestion:")
    print(f"  {insight.suggestion}")
    print()
    
    if insight.chart_labels:
        print("Chart Labels:")
        for key, value in insight.chart_labels.items():
            print(f"  - {key}: {value}")
        print()
    
    print("Score Breakdown:")
    print(f"  - Structure Clarity: {insight.structure_clarity}/100")
    print(f"  - Regime Stability: {insight.regime_stability}/100")
    print(f"  - Volume Quality: {insight.volume_quality}/100")
    print(f"  - Momentum Alignment: {insight.momentum_alignment}/100")
    print(f"  - Session Validity: {insight.session_validity}/100")
    print(f"  - Risk Level: {insight.risk_level}/100")
    print()
    
    print("=" * 70)
    print("🎉 WEBHOOK ENDPOINT TEST SUCCESSFUL!")
    print("=" * 70)
    print()
    
    # Test retrieval
    print("📊 Testing retrieval methods...")
    latest = MarketInsight.objects.filter(symbol='EURUSD').order_by('-timestamp')[:3]
    print(f"✅ Found {latest.count()} recent EURUSD insights")
    print()
    
    # Simulate API response
    api_response = {
        'status': 'success',
        'insight_id': insight.id,
        'insight_index': insight.insight_index,
        'quality_label': insight_data['quality_label'],
        'vocabulary_hash': insight.vocabulary_hash,
        'insight_text': insight.insight_text,
        'suggestion': insight.suggestion,
        'timestamp': insight.timestamp.isoformat()
    }
    
    print("📡 Simulated API Response:")
    print(json.dumps(api_response, indent=2))
    print()
    
    print("✅ All systems operational!")
    print("🌟 Zenith Market Analyst is ready for production!")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
