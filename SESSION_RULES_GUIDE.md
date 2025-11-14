# Session-Based Trading Rules Guide

## Overview

ZenithEdge now includes **session-based weighting and blocking** for trading signals. The system automatically detects which FX trading session a signal occurs in (Asia, London, or New York) and applies user-defined rules.

## Features Implemented

### 1. **Auto-Session Detection** ✅
- All incoming signals are automatically assigned to one of three FX trading sessions
- Session is determined by the signal's `received_at` timestamp (UTC)
- No manual session assignment required

### 2. **SessionRule Model** ✅
- Per-user, per-session trading rules
- Configurable weight multiplier (0.0 - 10.0)
- Session blocking capability
- Optional notes for documentation

### 3. **Automatic Signal Blocking** ✅
- Signals received during blocked sessions are auto-rejected
- Rejection reason set to: `session_block: [Session] session is blocked by user settings`
- Blocked signals still saved to database for audit trail

### 4. **Dashboard Visualization** ✅
- Session column added to signal table
- Color-coded session badges:
  - **Blue**: New York session (16:00-23:59 UTC)
  - **Green**: London session (08:00-15:59 UTC)
  - **Yellow**: Asia session (00:00-07:59 UTC)

---

## Session Time Ranges

| Session | UTC Time Range | Major Markets |
|---------|---------------|---------------|
| **Asia** | 00:00 - 07:59 | Tokyo, Sydney, Singapore |
| **London** | 08:00 - 15:59 | London, Frankfurt, Zurich |
| **New York** | 16:00 - 23:59 | New York, Chicago, Toronto |

---

## Database Models

### Signal Model (Updated)

```python
class Signal(models.Model):
    # ... existing fields ...
    
    session = models.CharField(
        max_length=20,
        choices=[
            ('Asia', 'Asia Session'),
            ('London', 'London Session'),
            ('New York', 'New York Session'),
        ],
        null=True,
        blank=True,
        db_index=True,
        help_text="FX trading session (auto-detected from timestamp)"
    )
```

**Key Methods:**
- `detect_session(dt)` - Static method to detect session from datetime
- `save()` - Overridden to auto-populate session field

### SessionRule Model (New)

```python
class SessionRule(models.Model):
    session = models.CharField(max_length=20, choices=SESSION_CHOICES)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    weight = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    is_blocked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Constraints:**
- Unique together: `[user, session]` - one rule per user per session

---

## Usage Examples

### Creating Session Rules via Django Shell

```python
from signals.models import SessionRule
from accounts.models import CustomUser

user = CustomUser.objects.get(email='trader@example.com')

# Block Asia session completely
SessionRule.objects.create(
    user=user,
    session='Asia',
    is_blocked=True,
    weight=1.0,
    notes='Low liquidity, avoid trading'
)

# Increase weight for London session
SessionRule.objects.create(
    user=user,
    session='London',
    is_blocked=False,
    weight=1.5,
    notes='Best liquidity and volatility'
)

# Normal weight for New York session
SessionRule.objects.create(
    user=user,
    session='New York',
    is_blocked=False,
    weight=1.0,
    notes='Overlap with London early, good volume'
)
```

### Via Django Admin

1. Log in to Django Admin: `http://localhost:8000/admin/`
2. Navigate to **Signals > Session Rules**
3. Click **Add Session Rule**
4. Select:
   - **User**: Your user account
   - **Session**: Asia, London, or New York
   - **Weight**: 0.0 - 10.0 (default 1.0)
   - **Is blocked**: Check to block this session
   - **Notes**: Optional description
5. Click **Save**

---

## Webhook Behavior

### When Session is NOT Blocked

```bash
curl -X POST "http://localhost:8000/signals/api/webhook/?api_key=YOUR_API_KEY" \
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

### When Session IS Blocked

Same request, but during blocked session:

**Response:**
```json
{
  "status": "received",
  "signal_id": 124,
  "allowed": false,
  "reason": "session_block: Asia session is blocked by user settings"
}
```

**Note:** Signal is still saved to database with `is_allowed=False`

---

## Dashboard View

### Session Column Display

Each signal row now includes a **Session** column with color-coded badges:

```
ID | Symbol | Side | Regime   | Session  | Confidence | ... | Status
---|--------|------|----------|----------|------------|-----|--------
12 | EURUSD | BUY  | Trend    | 🟢 London | 85%       | ... | ✅ Allowed
13 | GBPUSD | SELL | Breakout | 🟡 Asia   | 78%       | ... | ❌ Blocked
14 | USDJPY | BUY  | Squeeze  | 🔵 NY     | 92%       | ... | ✅ Allowed
```

### CSS Classes

- `.session-ny` - Blue badge for New York session
- `.session-london` - Green badge for London session
- `.session-asia` - Yellow badge for Asia session

---

## Testing Session Rules

### Test Script

```python
# Save as test_session_rules.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from signals.models import Signal, SessionRule
from accounts.models import CustomUser

# Get user
user = CustomUser.objects.get(email='admin@zenithedge.com')

# Check current session
from django.utils import timezone
current_time = timezone.now()
current_session = Signal.detect_session(current_time)
print(f'Current UTC time: {current_time.hour}:00')
print(f'Current session: {current_session}')

# Check session rules
rules = SessionRule.objects.filter(user=user)
print(f'\nSession Rules for {user.email}:')
for rule in rules:
    status = 'BLOCKED' if rule.is_blocked else f'Weight: {rule.weight}'
    print(f'  {rule.session}: {status}')

# Check recent signals
signals = Signal.objects.filter(user=user).order_by('-id')[:5]
print(f'\nLast 5 Signals:')
for sig in signals:
    status = '❌ BLOCKED' if not sig.is_allowed else '✅ ALLOWED'
    print(f'  #{sig.id} {sig.symbol} - {sig.session} - {status}')
```

Run: `python3 test_session_rules.py`

### Manual Testing Steps

1. **Create session rules** (via admin or shell)
2. **Check current UTC time** to know which session you're in
3. **Send test webhook** with appropriate API key
4. **Verify signal status** in database or dashboard
5. **Check rejection reason** matches session block

---

## Advanced Use Cases

### 1. Weight-Based Signal Ranking (Future Enhancement)

```python
# Pseudocode for future implementation
def rank_signals(signals):
    for signal in signals:
        session_rule = SessionRule.objects.get(
            user=signal.user,
            session=signal.session
        )
        
        # Apply weight multiplier to confidence
        weighted_confidence = signal.confidence * session_rule.weight
        
        # Use weighted_confidence for ranking
        signal.rank_score = weighted_confidence
    
    return sorted(signals, key=lambda s: s.rank_score, reverse=True)
```

### 2. Time-Based Session Override

```python
# Allow signals during specific hours within a session
class SessionRule(models.Model):
    # ... existing fields ...
    allowed_hours_start = models.TimeField(null=True, blank=True)
    allowed_hours_end = models.TimeField(null=True, blank=True)
```

### 3. Symbol-Specific Session Rules

```python
# Different session rules per symbol
class SessionRule(models.Model):
    # ... existing fields ...
    symbol = models.CharField(max_length=20, null=True, blank=True)
    # unique_together = [['user', 'session', 'symbol']]
```

---

## Admin Interface

### SessionRule Admin

**List Display:**
- Session
- User
- Weight
- Is Blocked
- Created At
- Updated At

**Filters:**
- Session (Asia/London/New York)
- Is Blocked (Yes/No)
- User

**Search:** User email, notes

**Permissions:**
- Admins see all session rules
- Traders see only their own rules

### Signal Admin (Updated)

**New Features:**
- Session field added to list display
- Session filter added to sidebar
- Session shown in signal detail view

---

## Migration Applied

**File:** `signals/migrations/0003_signal_session_sessionrule.py`

**Changes:**
1. Added `session` field to Signal model
2. Created SessionRule model with constraints

**Applied:** ✅ Successfully migrated

**Existing Data:** All 8 existing signals updated with session data

---

## API Response Updates

### Signal Webhook Response

```json
{
  "status": "received",
  "signal_id": 123,
  "allowed": true/false,
  "reason": "Signal passed all prop rules checks" 
            // OR "session_block: [Session] session is blocked by user settings"
}
```

### Signal.to_dict() Output

```json
{
  "id": 123,
  "symbol": "EURUSD",
  "timeframe": "1h",
  "side": "buy",
  "regime": "Trend",
  "session": "London",  // ← NEW FIELD
  "confidence": 85.5,
  "is_allowed": true,
  "rejection_reason": "",
  // ... other fields ...
}
```

---

## Troubleshooting

### Issue: All signals showing same session

**Cause:** Session detection uses `received_at` (server time), not `timestamp` field from webhook

**Solution:** Ensure server timezone is UTC, or adjust session time ranges for your timezone

### Issue: Session rules not applying

**Checks:**
1. Verify SessionRule exists for user and session
2. Check `is_blocked` flag is set correctly
3. Ensure user is authenticated via API key
4. Check Django logs for errors

```bash
# Check session rules
python3 manage.py shell
>>> from signals.models import SessionRule
>>> SessionRule.objects.all()
```

### Issue: Session column not showing on dashboard

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

- Session detection: No additional queries (computed from datetime)
- Session rule check: 1 query per authenticated webhook request
- Dashboard: Session field indexed for fast filtering

### Caching (Recommended for Production)

```python
# Cache session rules per user
from django.core.cache import cache

def get_session_rule(user, session):
    cache_key = f'session_rule_{user.id}_{session}'
    rule = cache.get(cache_key)
    
    if rule is None:
        try:
            rule = SessionRule.objects.get(user=user, session=session)
            cache.set(cache_key, rule, timeout=3600)  # 1 hour
        except SessionRule.DoesNotExist:
            rule = None
    
    return rule
```

---

## Future Enhancements

### Planned Features

1. **Weight-based signal ranking**
   - Use session weight to prioritize signals
   - Combine with confidence score for overall rank

2. **Session overlap handling**
   - Special rules for London/NY overlap (12:00-16:00 UTC)
   - Highest volatility period

3. **Historical session performance**
   - Track win rate per session
   - Auto-adjust weights based on performance

4. **Session-specific take profit/stop loss**
   - Different TP/SL ratios per session
   - Based on typical volatility

5. **Dashboard session filter**
   - Filter signals by session in dashboard
   - Session performance stats card

---

## Testing Checklist

- [x] Session field added to Signal model
- [x] SessionRule model created with constraints
- [x] Migration applied successfully
- [x] Existing signals updated with session data
- [x] Session auto-detection working (Asia/London/NY)
- [x] Session blocking logic implemented in webhook
- [x] Blocked signals marked with correct reason
- [x] SessionRule admin interface configured
- [x] Dashboard shows session column with colors
- [x] Webhook tests: blocked session returns allowed=false
- [x] Webhook tests: unblocked session returns allowed=true
- [x] Signal.to_dict() includes session field

---

## Quick Reference

### Session Times (UTC)

- **Asia**: 00:00 - 07:59
- **London**: 08:00 - 15:59
- **New York**: 16:00 - 23:59

### Session Colors

- **Asia**: 🟡 Yellow (#fbbf24)
- **London**: 🟢 Green (#10b981)
- **New York**: 🔵 Blue (#3b82f6)

### Key URLs

- Dashboard: `http://localhost:8000/signals/dashboard/`
- Admin: `http://localhost:8000/admin/signals/sessionrule/`
- Webhook: `http://localhost:8000/signals/api/webhook/?api_key=YOUR_KEY`

### Test Accounts

- **Admin**: admin@zenithedge.com / admin123
  - API Key: `_yHwEIMeW5srLawBzhqWuup2ZwI9rOukOy2IxtFm3FeMlGUuojUgQSPPMGd_6Jrz`
  - Session Rules: Asia (BLOCKED), London (Weight 1.5), NY (Weight 1.0)

- **Trader**: trader@zenithedge.com / trader123
  - API Key: Check profile or database

---

## Support

For issues or questions:
1. Check Django logs: Watch terminal where `runserver` is running
2. Check database: `python3 manage.py dbshell`
3. Review this guide's Troubleshooting section
4. Contact system administrator

---

**Last Updated:** November 9, 2025  
**Version:** 1.0.0  
**Author:** ZenithEdge Development Team
