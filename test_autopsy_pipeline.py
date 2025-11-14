#!/usr/bin/env python3
"""
Test AutopsyLoop with simulated OHLCV data

Demonstrates full pipeline: Replay → Label → RCA → Explain
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/macbook/zenithedge_trading_hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from django.utils import timezone
from signals.models import Signal
from autopsy.models import InsightAudit
from autopsy.labeler import OutcomeLabeler
from autopsy.rca import analyze_audit
from autopsy.explain import explain_insight

print("="*70)
print("🔬 AutopsyLoop Full Pipeline Test")
print("="*70)

# Get a signal to test
signal = Signal.objects.filter(symbol__isnull=False).order_by('-received_at').first()

if not signal:
    print("\n❌ No signals found in database!")
    sys.exit(1)

print(f"\n📊 Testing with Signal #{signal.id}")
print(f"   Symbol: {signal.symbol}")
print(f"   Side: {signal.side}")
print(f"   Price: {signal.price}")
print(f"   Timeframe: {signal.timeframe}")
print(f"   Received: {signal.received_at}")

# Generate simulated OHLCV data (since we don't have real market data yet)
print("\n1️⃣ Simulating OHLCV Data...")

entry_price = Decimal(str(signal.price))
is_bullish = signal.side.lower() in ['buy', 'long']

# Simulate a successful trade
if is_bullish:
    high_price = entry_price * Decimal('1.002')  # 0.2% move up
    low_price = entry_price * Decimal('0.9995')  # Small drawdown
    close_price = entry_price * Decimal('1.0015')  # Closes in profit
else:
    high_price = entry_price * Decimal('1.0005')  # Small adverse move
    low_price = entry_price * Decimal('0.998')  # 0.2% move down
    close_price = entry_price * Decimal('0.9985')  # Closes in profit

simulated_ohlcv = {
    'open': entry_price,
    'high': high_price,
    'low': low_price,
    'close': close_price,
    'timestamp': timezone.now(),
    'candle_count': 4  # 4 hours = 4 candles for 1H data
}

print(f"   Entry: {entry_price}")
print(f"   High:  {high_price} (+{((high_price - entry_price) / entry_price * 100):.2f}%)")
print(f"   Low:   {low_price} ({((low_price - entry_price) / entry_price * 100):.2f}%)")
print(f"   Close: {close_price} ({((close_price - entry_price) / entry_price * 100):.2f}%)")

# Step 2: Label the outcome
print("\n2️⃣ Labeling Outcome...")

labeler = OutcomeLabeler(signal, horizon='4H')

if not labeler.rule:
    print("   ⚠️  No matching rule - using defaults")
else:
    print(f"   ✅ Using Rule #{labeler.rule.id}: {labeler.rule.symbol or 'All'} / {labeler.rule.timeframe or 'All'}")

outcome, metrics = labeler.evaluate(simulated_ohlcv)

print(f"\n   📋 Outcome: {outcome.upper()}")
print(f"   💰 P&L: {metrics.get('pnl_pct', 0):.2f}%")
print(f"   📉 Max Drawdown: {metrics.get('max_drawdown', 0):.2f} pips")
print(f"   📈 Max Favorable: {metrics.get('favorable_move_pips', 0):.2f} pips")

# Step 3: Create audit record
print("\n3️⃣ Creating Audit Record...")

audit = labeler.create_audit(
    simulated_ohlcv,
    replay_verified=True,  # Simulating successful pattern verification
    needs_manual_review=False
)

print(f"   ✅ Created InsightAudit #{audit.id}")
print(f"   Horizon: {audit.horizon}")
print(f"   Outcome: {audit.get_outcome_display()}")
print(f"   P&L: {audit.pnl_pct}%")

# Step 4: Run RCA (if failed or neutral)
causes = []
if outcome in ['failed', 'neutral']:
    print("\n4️⃣ Running Root Cause Analysis...")
    
    causes = analyze_audit(audit)
    
    if causes:
        print(f"   ✅ Identified {len(causes)} probable causes:")
        for i, cause in enumerate(causes, 1):
            print(f"\n   {i}. {cause.get_cause_display()} ({cause.confidence}% confidence)")
            print(f"      {cause.summary[:100]}...")
    else:
        print("   ⚠️  No causes identified")
else:
    print("\n4️⃣ Skipping RCA (outcome: succeeded)")

# Step 5: Generate explanation
print("\n5️⃣ Generating Explanation...")

explanation = explain_insight(signal)

if 'error' not in explanation:
    print(f"   ✅ Generated explanation")
    print(f"   Summary: {explanation.get('summary', 'N/A')}")
    
    if 'top_features' in explanation and explanation['top_features']:
        print(f"\n   Top 3 Features:")
        for feat in explanation['top_features'][:3]:
            print(f"   • {feat['feature']}: {feat['interpretation']}")
else:
    print(f"   ⚠️  Explanation error: {explanation.get('error')}")

# Success rate context
print("\n6️⃣ Calculating Success Rate Context...")

context = audit.get_success_rate_context()
if context:
    print(f"   ✅ Similar insights: {context['sample_size']}")
    print(f"   Success rate: {context['success_rate']}%")
else:
    print("   ℹ️  Not enough data for context")

# Summary
print("\n" + "="*70)
print("✅ AutopsyLoop Pipeline Complete!")
print("="*70)

print(f"\n📊 Results Summary:")
print(f"   Signal ID: #{signal.id}")
print(f"   Audit ID: #{audit.id}")
print(f"   Outcome: {audit.get_outcome_display()}")
print(f"   P&L: {audit.pnl_pct:.2f}%")
print(f"   Pattern Verified: {'Yes' if audit.replay_verified else 'No'}")

if causes:
    print(f"   Primary Cause: {causes[0].get_cause_display()}")

print(f"\n🌐 View in Admin:")
print(f"   http://localhost:8000/admin/autopsy/insightaudit/{audit.id}/change/")

print(f"\n💡 Run batch analysis:")
print(f"   python3 manage.py run_autopsy --last-days 7 --horizons 4H,24H")

print()
