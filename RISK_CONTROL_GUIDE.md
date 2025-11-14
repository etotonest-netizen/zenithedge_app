# Risk Control System - Loss Spiral Protection

## Overview

ZenithEdge now includes **automatic risk control** to protect against loss spirals and excessive trading. The system automatically halts trading when risk thresholds are exceeded, preventing emotional trading and protecting capital.

## Features Implemented

### 1. **RiskControl Model** ✅
- Per-user risk management settings
- Three protection mechanisms:
  - **Max Consecutive Losers**: Halt after N losses in a row
  - **Max Daily Trades**: Limit total trades per day
  - **Max Red Signals**: Limit rejected/blocked signals per day
- Automatic halt triggering
- Manual or automatic reset options

### 2. **Signal Outcome Tracking** ✅
- New `outcome` field: win, loss, or pending
- Tracks trade results for risk calculations
- Enables accurate consecutive loss counting

### 3. **Automatic Trading Halt** ✅
- Real-time evaluation before each signal
- Blocks all incoming signals when halted
- Clear rejection reasons in webhook responses
- Persistent halt until manual reset

### 4. **Dashboard Warning Banner** ✅
- Red pulsing warning when trading is halted
- Displays halt reason and trigger time
- Direct link to admin panel for reset
- High visibility alert system

---

## Database Models

### RiskControl Model

```python
class RiskControl(models.Model):
    # User ownership
    user = models.ForeignKey('accounts.CustomUser')
    
    # Risk thresholds
    max_consecutive_losers = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(20)])
    max_daily_trades = models.IntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(100)])
    max_red_signals_per_day = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(50)])
    
    # Control settings
    is_active = models.BooleanField(default=True)
    halt_until_reset = models.BooleanField(default=True)
    
    # Tracking
    is_halted = models.BooleanField(default=False)
    halt_reason = models.TextField(blank=True)
    halt_triggered_at = models.DateTimeField(null=True)
    last_reset_at = models.DateTimeField(null=True)
```

**Key Methods:**
- `trigger_halt(reason)` - Activate trading halt
- `reset_halt()` - Manually reset halt status
- `should_auto_reset()` - Check if new trading day (for auto-reset mode)

### Signal Model (Updated)

```python
class Signal(models.Model):
    # ... existing fields ...
    
    # Risk control fields
    outcome = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('win', 'Win'), ('loss', 'Loss')], default='pending')
    is_risk_blocked = models.BooleanField(default=False)
    risk_control_checked = models.ForeignKey('RiskControl', null=True)
```

---

## Risk Control Logic

### Evaluation Flow

```
1. Webhook receives signal
   ↓
2. evaluate_risk_controls(user)
   ↓
3. Check if already halted → Block if yes
   ↓
4. Check consecutive losses → Halt if ≥ limit
   ↓
5. Check daily trade count → Halt if ≥ limit
   ↓
6. Check red signals count → Halt if ≥ limit
   ↓
7. Signal allowed/blocked based on result
```

### Halt Conditions

| Condition | Default Limit | Trigger |
|-----------|--------------|---------|
| **Consecutive Losses** | 3 | 3 losses in a row (no wins between) |
| **Daily Trades** | 10 | 10 total signals in one day |
| **Red Signals** | 5 | 5 rejected signals in one day |

**All conditions reset at UTC midnight (optional auto-reset)**

---

## Usage Examples

### Creating Risk Control via Django Shell

```python
from signals.models import RiskControl
from accounts.models import CustomUser

user = CustomUser.objects.get(email='trader@example.com')

RiskControl.objects.create(
    user=user,
    max_consecutive_losers=3,
    max_daily_trades=10,
    max_red_signals_per_day=5,
    is_active=True,
    halt_until_reset=True,  # Manual reset required
    notes='Conservative risk management'
)
```

### Via Django Admin

1. Log in to Django Admin: `http://localhost:8000/admin/`
2. Navigate to **Signals > Risk Controls**
3. Click **Add Risk Control**
4. Configure:
   - **User**: Select your account
   - **Max Consecutive Losers**: 3 (recommended)
   - **Max Daily Trades**: 10-20
   - **Max Red Signals Per Day**: 5-10
   - **Is Active**: Check
   - **Halt Until Reset**: Check (for manual control)
5. Click **Save**

---

## Webhook Behavior

### Before Halt (Normal Operation)

```bash
curl -X POST "http://localhost:8000/signals/api/webhook/?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "timeframe": "1h",
    "side": "buy",
    "sl": 1.0900,
    "tp": 1.1000,
    "confidence": 85,
    "strategy": "ZenithEdge",
    "regime": "Trend"
  }'
```

**Response:**
```json
{
  "status": "received",
  "signal_id": 123,
  "allowed": true,
  "reason": "Signal passed all prop rules checks"
}
```

### After Halt (Risk Control Triggered)

Same request after 3 consecutive losses:

**Response:**
```json
{
  "status": "received",
  "signal_id": 124,
  "allowed": false,
  "reason": "risk_control: Trading halted: Consecutive loss limit reached (3/3)"
}
```

**Note:** Signal is saved to database with `is_risk_blocked=True`

---

## Dashboard View

### Risk Control Warning Banner

When trading is halted, a prominent red banner appears at the top of the dashboard:

```
╔══════════════════════════════════════════════════════════════╗
║  🚫 AUTO-TRADING HALTED                                      ║
║                                                              ║
║  Reason: Consecutive loss limit reached (3/3)               ║
║  Triggered At: 2025-11-09 04:00:32 UTC                      ║
║                                                              ║
║  All incoming signals will be blocked until risk controls   ║
║  are manually reset.                                        ║
║                                                              ║
║  [Manage Risk Controls] ← Button to admin panel             ║
╚══════════════════════════════════════════════════════════════╝
```

### Banner Features:
- **Animated pulse effect** for high visibility
- **Clear halt reason** (consecutive losses, daily limit, etc.)
- **Timestamp** of when halt was triggered
- **Direct link** to risk control management
- **Red gradient** background (#991b1b → #dc2626)

---

## Managing Trade Outcomes

### Marking Signals as Win/Loss

**Via Django Shell:**
```python
from signals.models import Signal

# Mark as win
signal = Signal.objects.get(id=123)
signal.outcome = 'win'
signal.save()

# Mark as loss
signal = Signal.objects.get(id=124)
signal.outcome = 'loss'
signal.save()
```

**Via Django Admin:**
1. Go to **Signals > Signals**
2. Click on a signal
3. Change **Outcome** to Win or Loss
4. Click **Save**

**Important:** Only signals with `outcome='win'` or `outcome='loss'` are counted for consecutive loss streaks. Pending signals are ignored.

---

## Resetting Trading Halt

### Method 1: Admin Action (Bulk Reset)

1. Go to **Signals > Risk Controls**
2. Select risk control(s) to reset
3. Choose action: **Reset halt status**
4. Click **Go**

### Method 2: Edit Risk Control

1. Go to **Signals > Risk Controls**
2. Click on your risk control
3. Under **Halt Status**, uncheck **Is halted**
4. Clear **Halt reason**
5. Click **Save**

### Method 3: Django Shell

```python
from signals.models import RiskControl
from accounts.models import CustomUser

user = CustomUser.objects.get(email='your@email.com')
risk_control = RiskControl.objects.get(user=user, is_active=True)
risk_control.reset_halt()

print(f'✅ Trading halt reset. Status: {"Halted" if risk_control.is_halted else "Active"}')
```

---

## Testing Risk Controls

### Simulating Loss Spiral

```python
#!/usr/bin/env python3
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from signals.models import Signal, RiskControl
from accounts.models import CustomUser

# Get user
user = CustomUser.objects.get(email='admin@zenithedge.com')

# Mark last 3 signals as losses
from django.utils import timezone
today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
signals = Signal.objects.filter(
    user=user,
    received_at__gte=today_start,
    outcome='pending'
).order_by('-id')[:3]

for sig in signals:
    sig.outcome = 'loss'
    sig.save()
    print(f'❌ Marked Signal #{sig.id} as LOSS')

# Check risk control
risk_control = RiskControl.objects.get(user=user, is_active=True)
print(f'\n📊 Risk Control: {"🚫 HALTED" if risk_control.is_halted else "✅ ACTIVE"}')

# Send new signal via webhook to trigger halt
print('\n📝 Next: Send webhook signal - it should be blocked')
```

### Expected Behavior

1. **First 3 signals**: Marked as losses
2. **4th signal via webhook**: Triggers halt
3. **All subsequent signals**: Blocked with reason "risk_control: ..."
4. **Dashboard**: Shows red warning banner
5. **Admin panel**: Shows halt status and reason

---

## Admin Interface

### RiskControl Admin

**List Display:**
- User
- Is Active
- Is Halted
- Max Consecutive Losers
- Max Daily Trades
- Max Red Signals Per Day
- Halt Triggered At
- Updated At

**Filters:**
- Is Active
- Is Halted
- Halt Until Reset
- User

**Actions:**
- Reset halt status (bulk action)

**Permissions:**
- Admins see all risk controls
- Traders see only their own

---

## Migration Applied

**File:** `signals/migrations/0004_signal_is_risk_blocked_signal_outcome_riskcontrol_and_more.py`

**Changes:**
1. Added `is_risk_blocked` field to Signal
2. Added `outcome` field to Signal (win/loss/pending)
3. Created RiskControl model
4. Added `risk_control_checked` FK to Signal

**Applied:** ✅ Successfully migrated

**Existing Data:** All signals default to `outcome='pending'`, `is_risk_blocked=False`

---

## API Response Updates

### Webhook Response (Halted)

```json
{
  "status": "received",
  "signal_id": 125,
  "allowed": false,
  "reason": "risk_control: Trading halted: Consecutive loss limit reached (3/3)"
}
```

### Signal.to_dict() Output

```json
{
  "id": 125,
  "symbol": "EURUSD",
  "outcome": "pending",  // ← NEW FIELD
  "is_risk_blocked": true,  // ← NEW FIELD
  "is_allowed": false,
  "rejection_reason": "risk_control: Trading halted: Consecutive loss limit reached (3/3)",
  // ... other fields ...
}
```

---

## Troubleshooting

### Issue: Risk control not triggering

**Checks:**
1. Verify RiskControl exists and is_active=True
2. Check that signals are marked with outcomes (win/loss)
3. Ensure consecutive losses, not just any losses
4. Verify user is authenticated via API key

```python
# Check risk control
from signals.models import RiskControl
RiskControl.objects.filter(is_active=True)

# Check today's losses
from signals.models import Signal
from django.utils import timezone
today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
Signal.objects.filter(received_at__gte=today_start, outcome='loss')
```

### Issue: Halt won't reset

**Fix:** Use admin action or call `reset_halt()`:

```python
from signals.models import RiskControl
risk_control = RiskControl.objects.get(id=1)
risk_control.reset_halt()
```

### Issue: Warning banner not showing

**Fix:** Clear browser cache and refresh

```bash
# Restart Django server
pkill -f "python3 manage.py runserver"
cd /tmp/django_trading_webhook
python3 manage.py runserver 0.0.0.0:8000
```

---

## Performance Considerations

### Database Queries

- Risk evaluation: 2-3 queries per webhook request
  1. Get RiskControl for user
  2. Count today's signals (filtered)
  3. Check consecutive losses (filtered query)
- Dashboard: +1 query to check halt status

### Optimization Tips

```python
# Cache risk control per user (production)
from django.core.cache import cache

def get_risk_control(user):
    cache_key = f'risk_control_{user.id}'
    rc = cache.get(cache_key)
    
    if rc is None:
        rc = RiskControl.objects.filter(user=user, is_active=True).first()
        cache.set(cache_key, rc, timeout=300)  # 5 minutes
    
    return rc
```

---

## Configuration Recommendations

### Conservative (Low Risk Tolerance)

```python
RiskControl.objects.create(
    user=user,
    max_consecutive_losers=2,  # Halt after 2 losses
    max_daily_trades=5,         # Max 5 trades/day
    max_red_signals_per_day=3,  # Max 3 rejected/day
    halt_until_reset=True       # Manual reset required
)
```

### Moderate (Balanced)

```python
RiskControl.objects.create(
    user=user,
    max_consecutive_losers=3,  # Halt after 3 losses
    max_daily_trades=10,        # Max 10 trades/day
    max_red_signals_per_day=5,  # Max 5 rejected/day
    halt_until_reset=True       # Manual reset required
)
```

### Aggressive (Higher Risk Tolerance)

```python
RiskControl.objects.create(
    user=user,
    max_consecutive_losers=5,   # Halt after 5 losses
    max_daily_trades=20,         # Max 20 trades/day
    max_red_signals_per_day=10,  # Max 10 rejected/day
    halt_until_reset=False       # Auto-reset daily
)
```

---

## Future Enhancements

### Planned Features

1. **Drawdown-Based Halt**
   ```python
   max_daily_drawdown_pct = models.FloatField(default=5.0)
   # Halt when daily loss exceeds % of account
   ```

2. **Time-Based Auto-Reset**
   ```python
   auto_reset_time = models.TimeField(default='00:00:00')
   # Reset at specific time instead of midnight
   ```

3. **Email/SMS Alerts**
   ```python
   def trigger_halt(self, reason):
       self.is_halted = True
       self.halt_reason = reason
       self.halt_triggered_at = timezone.now()
       self.save()
       
       # Send alert
       send_mail(
           'Trading Halted - Risk Control',
           f'Reason: {reason}',
           'noreply@zenithedge.com',
           [self.user.email]
       )
   ```

4. **Partial Position Sizing**
   ```python
   reduce_position_after_loss = models.BooleanField(default=False)
   position_reduction_pct = models.FloatField(default=50.0)
   # Reduce position size by 50% after each loss
   ```

---

## Testing Checklist

- [x] RiskControl model created with constraints
- [x] Signal outcome field added (win/loss/pending)
- [x] evaluate_risk_controls() function implemented
- [x] Webhook checks risk controls before prop rules
- [x] Consecutive loss detection working
- [x] Daily trade limit working
- [x] Red signal limit working
- [x] Trading halt persists across signals
- [x] Dashboard shows warning banner when halted
- [x] Admin panel allows halt reset
- [x] Migration applied successfully
- [x] Tested with 3 consecutive losses → halt triggered
- [x] Tested subsequent signals → all blocked

---

## Quick Reference

### Risk Control Thresholds (Default)

- **Consecutive Losses**: 3
- **Daily Trades**: 10
- **Red Signals**: 5

### Halt Reasons

- `Consecutive loss limit reached (3/3)`
- `Daily trade limit reached (10/10)`
- `Too many rejected signals today (5/5)`

### Key URLs

- Dashboard: `http://localhost:8000/signals/dashboard/`
- Risk Controls Admin: `http://localhost:8000/admin/signals/riskcontrol/`
- Signals Admin: `http://localhost:8000/admin/signals/signal/`

### Test Accounts

- **Admin**: admin@zenithedge.com / admin123
  - API Key: `_yHwEIMeW5srLawBzhqWuup2ZwI9rOukOy2IxtFm3FeMlGUuojUgQSPPMGd_6Jrz`
  - Risk Control: Active (3/10/5 limits)

---

## Support

For issues or questions:
1. Check Django logs for risk control evaluation
2. Verify RiskControl is active in admin
3. Check signal outcomes are properly marked
4. Review this guide's Troubleshooting section

---

**Last Updated:** November 9, 2025  
**Version:** 2.2.0  
**Author:** ZenithEdge Development Team
