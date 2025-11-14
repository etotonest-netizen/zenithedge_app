# PropRules Integration Guide

## Overview

The `PropRules` model allows you to define and enforce proprietary trading rules on incoming signals from TradingView. Signals are validated against active prop rules before being saved.

## PropRules Model Fields

### Daily Limits
- **max_daily_loss_pct** (default: 5.0): Maximum daily loss as % of account balance
- **max_daily_loss_amount**: Optional absolute dollar amount limit
- **max_trades_per_day** (default: 10): Maximum number of trades per day

### Position Management
- **max_open_positions** (default: 3): Maximum simultaneous open positions
- **max_position_size_pct** (default: 2.0): Max position size as % of account
- **max_risk_per_trade_pct** (default: 1.0): Max risk per trade as % of account

### Time Restrictions
- **blackout_minutes** (default: 5): Minutes to wait between trades on same symbol
- **trading_start_time**: Start of allowed trading hours (UTC, optional)
- **trading_end_time**: End of allowed trading hours (UTC, optional)
- **allow_weekend_trading** (default: False): Allow trades on Saturday/Sunday

### Symbol Restrictions
- **allowed_symbols**: Comma-separated whitelist (empty = all allowed)
- **blacklisted_symbols**: Comma-separated blacklist

### Quality Filters
- **min_confidence_score** (default: 60.0): Minimum confidence to accept signal

### Account
- **account_balance** (default: 10000.00): Current balance for % calculations
- **is_active**: Whether this rule set is currently active

## Validation Checks

The `check_signal_against_prop()` function performs these checks in order:

1. **Confidence Score**: Signal confidence must meet minimum threshold
2. **Symbol Whitelist**: If defined, only whitelisted symbols allowed
3. **Symbol Blacklist**: Blacklisted symbols are always rejected
4. **Weekend Trading**: Rejects weekend signals if not allowed
5. **Trading Hours**: Must be within specified UTC hours if defined
6. **Daily Trade Limit**: Counts allowed signals for today
7. **Blackout Period**: Checks time since last trade on same symbol
8. **Max Open Positions**: Counts distinct symbols with allowed signals

## Setting Up Prop Rules

### Via Django Admin

1. Go to Django admin: `/admin/`
2. Navigate to "Prop Trading Rules"
3. Click "Add Prop Trading Rule"
4. Configure your rules:

```
Name: FTMO Challenge
Is Active: ✓
Account Balance: 10000.00
Max Daily Loss %: 5.0
Max Trades Per Day: 10
Max Open Positions: 3
Blackout Minutes: 10
Min Confidence Score: 70.0
Allow Weekend Trading: ☐
Allowed Symbols: BTCUSDT, ETHUSDT, EURUSD
Blacklisted Symbols: DOGEUSDT, SHIBUSDT
Trading Start Time: 08:00:00
Trading End Time: 22:00:00
```

### Via Python Shell

```python
from signals.models import PropRules
from decimal import Decimal

prop_rules = PropRules.objects.create(
    name='FTMO Challenge',
    max_daily_loss_pct=5.0,
    max_trades_per_day=10,
    max_open_positions=3,
    blackout_minutes=10,
    min_confidence_score=70.0,
    allow_weekend_trading=False,
    allowed_symbols='BTCUSDT, ETHUSDT, EURUSD',
    blacklisted_symbols='DOGEUSDT, SHIBUSDT',
    account_balance=Decimal('10000.00'),
    is_active=True
)
```

## Webhook Response Format

### Signal Allowed
```json
{
  "status": "received",
  "signal_id": 123,
  "allowed": true,
  "reason": "Signal passed all prop rules checks"
}
```

### Signal Rejected
```json
{
  "status": "received",
  "signal_id": 124,
  "allowed": false,
  "reason": "Confidence 45.50% below minimum 70.0%"
}
```

Note: Signals are always saved to the database, but marked as `is_allowed=False` if they fail validation.

## Common Rejection Reasons

- `"Confidence X% below minimum Y%"` - Confidence score too low
- `"Symbol X not in allowed list: Y, Z"` - Symbol not whitelisted
- `"Symbol X is blacklisted"` - Symbol on blacklist
- `"Weekend trading not allowed"` - Trade attempted on Sat/Sun
- `"Outside trading hours (08:00:00 - 22:00:00 UTC)"` - Outside allowed hours
- `"Daily trade limit reached (10/10)"` - Hit max trades for day
- `"Blackout period active for X (wait Y min between trades)"` - Too soon after last trade
- `"Maximum open positions reached (3/3)"` - Too many open positions

## Multiple Rule Sets

You can create multiple prop rule sets (e.g., different prop firms), but only ONE should be marked as `is_active=True`. The webhook uses the active rule set for validation.

## Querying Signals

### Get all allowed signals
```python
allowed_signals = Signal.objects.filter(is_allowed=True)
```

### Get all rejected signals
```python
rejected_signals = Signal.objects.filter(is_allowed=False)
```

### Get signals by rejection reason
```python
low_confidence = Signal.objects.filter(
    is_allowed=False,
    rejection_reason__icontains='Confidence'
)
```

### Get today's allowed signals
```python
from django.utils import timezone

today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_signals = Signal.objects.filter(
    received_at__gte=today,
    is_allowed=True
)
```

## Updating Account Balance

As your account balance changes, update the prop rules:

```python
prop_rules = PropRules.objects.get(name='FTMO Challenge', is_active=True)
prop_rules.account_balance = Decimal('12500.00')
prop_rules.save()
```

## Disabling Prop Rules

To temporarily disable all prop rules validation:

```python
PropRules.objects.filter(is_active=True).update(is_active=False)
```

Signals will then be allowed with reason: "No active prop rules configured"

## Testing Prop Rules

Run the prop rules test suite:

```bash
python manage.py test signals.tests_prop_rules
```

## Integration with Trading Bots

Your trading bot should:

1. Poll the webhook endpoint or listen for signals
2. Check `is_allowed` field in response
3. Only execute trades when `is_allowed=True`
4. Log `rejection_reason` for rejected signals

Example bot logic:
```python
import requests

response = requests.post(
    'https://yourserver.com/api/signals/webhook/',
    json=signal_data,
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)

result = response.json()
if result['allowed']:
    execute_trade(signal_data)
else:
    log_rejection(result['reason'])
```

## Best Practices

1. **Test in Demo**: Test prop rules with paper trading first
2. **Conservative Limits**: Start with strict limits, loosen gradually
3. **Monitor Rejections**: Review rejection reasons regularly
4. **Update Balance**: Keep account_balance field current
5. **Backup Rules**: Document your prop firm's rules accurately
6. **Multiple Timeframes**: Consider blackout periods across timeframes
7. **Symbol Lists**: Keep allowed/blacklisted symbols updated

## Migration

After adding PropRules to existing installation:

```bash
python manage.py makemigrations signals
python manage.py migrate signals
```

Existing signals will have `is_allowed=True` and `prop_rule_checked=NULL` by default.
