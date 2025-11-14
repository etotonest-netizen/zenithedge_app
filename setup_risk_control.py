#!/usr/bin/env python3
"""Script to create RiskControl test data and simulate loss spiral"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from signals.models import RiskControl, Signal
from accounts.models import CustomUser

# Get admin user
admin_user = CustomUser.objects.get(email='admin@zenithedge.com')

# Create risk control
risk_control, created = RiskControl.objects.get_or_create(
    user=admin_user,
    defaults={
        'max_consecutive_losers': 3,
        'max_daily_trades': 10,
        'max_red_signals_per_day': 5,
        'is_active': True,
        'halt_until_reset': True,
        'notes': 'Protection against loss spirals'
    }
)

if created:
    print('✅ Created RiskControl for admin user')
else:
    # Update existing
    risk_control.max_consecutive_losers = 3
    risk_control.max_daily_trades = 10
    risk_control.max_red_signals_per_day = 5
    risk_control.is_active = True
    risk_control.save()
    print('✅ Updated RiskControl for admin user')

print(f'\n📋 Risk Control Settings:')
print(f'  Max Consecutive Losers: {risk_control.max_consecutive_losers}')
print(f'  Max Daily Trades: {risk_control.max_daily_trades}')
print(f'  Max Red Signals Per Day: {risk_control.max_red_signals_per_day}')
print(f'  Is Active: {risk_control.is_active}')
print(f'  Is Halted: {risk_control.is_halted}')

# Check current status
from django.utils import timezone
today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_signals = Signal.objects.filter(user=admin_user, received_at__gte=today_start)

print(f'\n📊 Today\'s Stats:')
print(f'  Total signals: {today_signals.count()}')
print(f'  Rejected signals: {today_signals.filter(is_allowed=False).count()}')
print(f'  Risk blocked: {today_signals.filter(is_risk_blocked=True).count()}')

# Count consecutive losses
consecutive_losses = 0
for signal in today_signals.filter(outcome__in=['win', 'loss']).order_by('-received_at'):
    if signal.outcome == 'loss':
        consecutive_losses += 1
    else:
        break

print(f'  Consecutive losses: {consecutive_losses}')

print('\n✅ RiskControl setup complete!')
print('📖 To simulate loss spiral, mark signals as losses and send new signals')
