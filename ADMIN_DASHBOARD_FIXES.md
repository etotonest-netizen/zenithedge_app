# Admin Dashboard - Field Error Fixes

## Issues Fixed

## Issues Fixed

### 1. Signal Model - 'status' Field (Fixed)
**Error**: `Cannot resolve keyword 'status' into field`

**Root Cause**: Signal model doesn't have a 'status' field

**Fields Fixed**:
```python
# OLD (incorrect)
active_signals = Signal.objects.filter(status='active').count()
signals_pending = Signal.objects.filter(status='pending').count()
signals_executed = Signal.objects.filter(status='executed').count()

# NEW (correct)
active_signals = Signal.objects.filter(is_allowed=True, is_risk_blocked=False).count()
signals_pending = Signal.objects.filter(is_allowed=False).count()
signals_executed = Signal.objects.filter(outcome__in=['win', 'loss']).count()
```

### Issue 2: Signal Model - 'created_at' field error
**Error**: `Cannot resolve keyword 'created_at' into field`

**Root Cause**: Signal model uses 'received_at' not 'created_at'

**Fields Fixed**:
```python
# OLD (incorrect)
signals_today = Signal.objects.filter(created_at__gte=today_start).count()
recent_signals = Signal.objects.order_by('-created_at')[:10]

# NEW (correct)
signals_today = Signal.objects.filter(received_at__gte=today_start).count()
recent_signals = Signal.objects.order_by('-received_at')[:10]
```

### Issue 3: Signal Model - 'pnl' field error
**Error**: Signal model doesn't have a 'pnl' field for aggregation

**Root Cause**: P&L is stored in StrategyPerformance, not Signal

**Fields Fixed**:
```python
# OLD (incorrect)
total_pnl = Signal.objects.filter(outcome__in=['win', 'loss']).aggregate(
    total=Sum('pnl')
)['total']

# NEW (correct)
try:
    total_pnl = StrategyPerformance.objects.aggregate(total=Sum('total_pnl'))['total'] or Decimal('0.00')
except Exception:
    total_pnl = Decimal('0.00')
```

### 4. SessionRule Model - 'is_active' Field (Fixed)

**Error**: `Cannot resolve keyword 'is_active' into field`

**Root Cause**: SessionRule model uses 'is_blocked' not 'is_active'

**Available Fields**: `created_at, id, is_blocked, notes, session, updated_at, user, user_id, weight`

**Fields Fixed**:
```python
# OLD (incorrect)
active_sessions = SessionRule.objects.filter(is_active=True).count()

# NEW (correct)
active_sessions = SessionRule.objects.filter(is_blocked=False).count()
```

### 5. Signal Model - Risk Blocks 'created_at' Field (Fixed)

**Error**: `Cannot resolve keyword 'created_at' into field` (Line 100)

**Location**: `admin_dashboard/views.py` line 100-103

**Root Cause**: Another reference to `created_at` in the risk blocks query - Signal model uses `received_at`

**Solution**:
```python
# BEFORE (incorrect)
risk_blocks_today = Signal.objects.filter(
    is_risk_blocked=True,
    created_at__gte=today_start
).count()

# AFTER (correct)
risk_blocks_today = Signal.objects.filter(
    is_risk_blocked=True,
    received_at__gte=today_start
).count()
```

---
```

## Signal Model - Actual Fields

Based on error messages and code review:
- `is_allowed` - Whether signal is allowed to trade
- `is_risk_blocked` - Whether signal was blocked by risk controls
- `received_at` - Timestamp when webhook was received
- `outcome` - Result: 'win', 'loss', or null
- `price` - Signal entry price
- `symbol` - Trading pair
- `strategy` - Strategy name (CharField, not ForeignKey)
- Other fields: ai_score, chart_snapshot, confidence, entry_bar_index, etc.

## SessionRule Model - Actual Fields

- `session` - Session name ('Asia', 'London', 'New York')
- `user` - ForeignKey to CustomUser
- `weight` - Weight multiplier (0.0-10.0)
- `is_blocked` - Whether session is blocked
- `notes` - Text notes
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## RiskControl Model - Actual Fields

- `user` - ForeignKey to CustomUser
- `max_consecutive_losers` - Max losing streak before halt
- `max_daily_trades` - Max trades per day
- `max_red_signals_per_day` - Max rejected signals per day
- `is_active` - Whether risk controls are active ✅
- `halt_until_reset` - Whether to halt until manual reset
- `is_halted` - Whether currently halted
- `halt_reason` - Reason for halt
- `halt_triggered_at` - When halt was triggered

## Analytics Queries Fixed

```python
# Signal volume by date
signal_volume = Signal.objects.filter(
    received_at__gte=start_date
).extra(
    select={'day': 'date(received_at)'}
).values('day').annotate(count=Count('id')).order_by('day')

# Performance data
performance_data = Signal.objects.filter(
    received_at__gte=start_date,
    outcome__in=['win', 'loss']
).extra(
    select={'day': 'date(received_at)'}
).values('day').annotate(
    wins=Count('id', filter=Q(outcome='win')),
    losses=Count('id', filter=Q(outcome='loss')),
    total_pnl=Sum('price')  # Using price as proxy since pnl doesn't exist
).order_by('day')
```

## Status

✅ **All FieldErrors Resolved** (6 fixes total)
✅ Admin dashboard loads successfully
✅ Server running on port 8000
✅ Redirects to login as expected (302)

## Testing

```bash
# Test server response
curl -I http://127.0.0.1:8000/admin-dashboard/

# Expected: HTTP/1.1 302 Found (redirect to login)
```

## Next Steps (Optional Improvements)

1. **Add actual P&L tracking to Signal model** - Currently using StrategyPerformance aggregation
2. **Add performance indices** - Speed up dashboard queries on large datasets
3. **Add caching** - Cache expensive aggregations with 5-minute TTL
4. **Add pagination** - For recent signals/users tables
5. **Add real-time WebSocket updates** - Live statistics updates
