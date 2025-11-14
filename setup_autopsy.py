#!/usr/bin/env python3
"""
Setup default labeling rules for AutopsyLoop and run test audit
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/macbook/zenithedge_trading_hub')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from autopsy.models import LabelingRule
from signals.models import Signal
from decimal import Decimal

print("🔧 Setting up AutopsyLoop default labeling rules...\n")

# Create default rules for common scenarios
rules_to_create = [
    {
        'name': 'Conservative EURUSD 4H',
        'symbol': 'EURUSD',
        'timeframe': '4h',
        'horizon': '4H',
        'success_tp_pips': Decimal('25'),
        'success_rr_ratio': Decimal('2.0'),
        'fail_sl_pips': Decimal('12'),
        'fail_adverse_pct': Decimal('0.8'),
        'neutral_band_pips': Decimal('8'),
        'priority': 100,
        'notes': 'Conservative rule for EURUSD 4H timeframe'
    },
    {
        'name': 'Conservative GBPUSD 4H',
        'symbol': 'GBPUSD',
        'timeframe': '4h',
        'horizon': '4H',
        'success_tp_pips': Decimal('30'),
        'success_rr_ratio': Decimal('2.0'),
        'fail_sl_pips': Decimal('15'),
        'fail_adverse_pct': Decimal('0.9'),
        'neutral_band_pips': Decimal('10'),
        'priority': 100,
        'notes': 'Conservative rule for GBPUSD 4H - higher volatility'
    },
    {
        'name': 'Default 4H Rule (All Pairs)',
        'symbol': '',  # Applies to all
        'timeframe': '4h',
        'horizon': '4H',
        'success_tp_pips': Decimal('20'),
        'success_rr_ratio': Decimal('2.0'),
        'fail_sl_pips': Decimal('15'),
        'fail_adverse_pct': Decimal('1.0'),
        'neutral_band_pips': Decimal('10'),
        'priority': 50,
        'notes': 'Default fallback rule for 4H timeframe'
    },
    {
        'name': 'Default 24H Rule (All Pairs)',
        'symbol': '',
        'timeframe': '',
        'horizon': '24H',
        'success_tp_pips': Decimal('50'),
        'success_rr_ratio': Decimal('2.5'),
        'fail_sl_pips': Decimal('25'),
        'fail_adverse_pct': Decimal('1.5'),
        'neutral_band_pips': Decimal('15'),
        'priority': 40,
        'notes': 'Default fallback rule for 24H timeframe'
    },
    {
        'name': 'Scalping 1H Rule',
        'symbol': '',
        'timeframe': '1h',
        'horizon': '1H',
        'success_tp_pips': Decimal('15'),
        'success_rr_ratio': Decimal('1.5'),
        'fail_sl_pips': Decimal('10'),
        'fail_adverse_pct': Decimal('0.6'),
        'neutral_band_pips': Decimal('5'),
        'priority': 60,
        'notes': 'Tighter parameters for 1H scalping'
    },
]

created_count = 0
existing_count = 0

for rule_data in rules_to_create:
    name = rule_data.pop('name')
    
    # Check if similar rule exists
    existing = LabelingRule.objects.filter(
        symbol=rule_data['symbol'],
        timeframe=rule_data['timeframe'],
        horizon=rule_data['horizon']
    ).first()
    
    if existing:
        print(f"⏭️  {name}: Already exists (ID: {existing.id})")
        existing_count += 1
    else:
        rule = LabelingRule.objects.create(**rule_data)
        print(f"✅ {name}: Created (ID: {rule.id})")
        created_count += 1

print(f"\n📊 Summary: {created_count} created, {existing_count} already existed")

# Show all active rules
print("\n" + "="*60)
print("📋 Active Labeling Rules:")
print("="*60)

active_rules = LabelingRule.objects.filter(is_active=True).order_by('-priority')
for rule in active_rules:
    scope = f"{rule.symbol or 'All'} / {rule.timeframe or 'All'}"
    print(f"\nRule #{rule.id} [{rule.priority}]: {scope} ({rule.horizon})")
    print(f"  Success: {rule.success_tp_pips} pips (R:R {rule.success_rr_ratio})")
    print(f"  Failure: {rule.fail_sl_pips} pips")
    print(f"  Neutral: ±{rule.neutral_band_pips} pips")

# Test with a signal
print("\n" + "="*60)
print("🧪 Testing AutopsyLoop with sample signal...")
print("="*60)

# Get a recent signal
test_signal = Signal.objects.filter(symbol__isnull=False).order_by('-received_at').first()

if test_signal:
    print(f"\n📊 Test Signal: #{test_signal.id}")
    print(f"   Symbol: {test_signal.symbol}")
    print(f"   Timeframe: {test_signal.timeframe}")
    print(f"   Side: {test_signal.side}")
    print(f"   Price: {test_signal.price}")
    print(f"   Received: {test_signal.received_at}")
    
    # Find matching rule
    from autopsy.labeler import OutcomeLabeler
    
    labeler = OutcomeLabeler(test_signal, '4H')
    if labeler.rule:
        print(f"\n✅ Matched Rule: #{labeler.rule.id}")
        print(f"   {labeler.rule.symbol or 'All'} / {labeler.rule.timeframe or 'All'} ({labeler.rule.horizon})")
    else:
        print("\n⚠️  No matching rule found - create more specific rules!")
    
    print("\n💡 To audit this signal, run:")
    print(f"   python3 manage.py run_autopsy --insight-id {test_signal.id} --horizons 4H")
else:
    print("\n⚠️  No signals found in database. Create some signals first!")

print("\n" + "="*60)
print("✅ AutopsyLoop Setup Complete!")
print("="*60)
print("\n📚 Next Steps:")
print("1. Access admin: http://localhost:8000/admin/autopsy/")
print("2. Run audit: python3 manage.py run_autopsy --last-days 7 --dry-run")
print("3. View docs: AUTOPSY_QUICK_START.md")
print()
