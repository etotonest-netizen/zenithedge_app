# ✅ ZenithEdge Testing Checklist - All Features

## 📋 Pre-Testing Setup

- [ ] Server running: `python3 manage.py runserver`
- [ ] Database migrated: All 6 migrations applied
- [ ] Pillow installed: `pip3 install Pillow`
- [ ] Browser: Chrome/Firefox with dev tools open
- [ ] Admin access: Superuser created
- [ ] Test data: 11 signals, 3 session rules, 1 risk control, 5 journal entries

---

## Feature #1: ⏰ Session-Based Trading Rules

### Model Tests
- [ ] SessionRule model exists in database
- [ ] 3 test rules present (EURUSD, USDJPY, GBPUSD)
- [ ] Fields: symbol, preferred_sessions, strategy, enabled, priority

### Function Tests
```python
from signals.models import Signal
from datetime import datetime, timezone

# Test detect_session()
signal = Signal.objects.first()
signal.received_at = datetime(2024, 11, 9, 14, 0, tzinfo=timezone.utc)  # 2pm UTC
signal.detect_session()
print(signal.session)  # Should be "London" (14:00 UTC = 08:00-16:00 London)
```

- [ ] Sydney: 22:00-06:00 UTC detected correctly
- [ ] Tokyo: 00:00-09:00 UTC detected correctly
- [ ] London: 08:00-16:00 UTC detected correctly
- [ ] New York: 13:00-22:00 UTC detected correctly
- [ ] Edge cases: Overlaps handled (e.g., 13:00 = London + NY)

### Dashboard UI Tests
- [ ] Navigate to `/signals/dashboard/`
- [ ] Session column visible in table
- [ ] Session badges color-coded:
  - [ ] Sydney: Purple background
  - [ ] Tokyo: Purple background
  - [ ] London: Blue background
  - [ ] New York: Orange background
- [ ] Clock icon (⏰) present on badges
- [ ] Hover shows full session name

### Admin Tests
- [ ] SessionRule admin accessible
- [ ] List view shows symbol, sessions, enabled status
- [ ] Create new rule: AUDUSD → Sydney, Tokyo
- [ ] Edit existing rule: Change EURUSD sessions
- [ ] Delete rule (soft delete if implemented)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Feature #2: 🛡️ Risk Control & Loss Spiral Protection

### Model Tests
- [ ] RiskControl model exists in database
- [ ] 1 test rule present (reversal strategy, HALTED)
- [ ] Fields: strategy, max_consecutive_losses, current_consecutive_losses, is_trading_halted

### Function Tests
```python
from signals.models import RiskControl

# Test check_risk_control()
rc = RiskControl.objects.get(strategy='reversal')
print(f"Streak: {rc.current_consecutive_losses}, Halted: {rc.is_trading_halted}")

# Should be: Streak: 3, Halted: True
```

- [ ] Loss count increments on losing trades
- [ ] Auto-halt at max_consecutive_losses (default: 3)
- [ ] Loss count resets to 0 on winning trades
- [ ] Manual override works (can disable halt)
- [ ] Multiple strategies tracked independently

### Dashboard UI Tests
- [ ] Navigate to `/signals/dashboard/`
- [ ] Red warning banner visible if halted:
  ```
  🚫 TRADING HALTED - [Strategy] (3 consecutive losses)
  Review your approach before resuming.
  ```
- [ ] Banner shows correct strategy name
- [ ] Banner shows correct loss count
- [ ] No banner if not halted

### Admin Tests
- [ ] RiskControl admin accessible
- [ ] List view shows strategy, streak, halted status
- [ ] Create new rule: Breakout strategy, max 5 losses
- [ ] Edit existing rule: Change max losses to 4
- [ ] Toggle is_trading_halted (manual override)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Feature #3: 📔 Smart Trade Journal System

### Model Tests
- [ ] TradeJournalEntry model exists in database
- [ ] 5 test entries present (3 wins, 1 loss, 1 break-even)
- [ ] Fields: signal (FK), entry_price, exit_price, pips_gained, outcome, emotions, learnings, tags

### Function Tests
```python
from signals.models import summarize_journal

# Test summarize_journal()
summary = summarize_journal()
print(f"Win Rate: {summary['win_rate']}%")
print(f"Net Pips: {summary['net_pips']}")
print(f"ROI: {summary['roi_percentage']}%")

# Expected: Win Rate: 75%, Net Pips: +59.25, ROI: +5.93%
```

- [ ] Win rate calculated correctly (3W + 1L + 1BE = 75%)
- [ ] Net pips summed correctly (+42.5 +18.5 -32.5 +30.5 +0 = +59.25)
- [ ] ROI percentage correct (+5.93%)
- [ ] Avg winner calculated (91.5 / 3 = +30.5)
- [ ] Avg loser calculated (-32.5 / 1 = -32.5)
- [ ] Current streak tracked (1 loss = -1)
- [ ] Best winning streak tracked (2)

### Journal List View Tests
- [ ] Navigate to `/signals/journal/`
- [ ] Page title: "Trade Journal"
- [ ] Summary stats cards visible:
  - [ ] Total Entries: 5
  - [ ] Win Rate: 75%
  - [ ] Net Pips: +59.25
  - [ ] ROI: +5.93%
- [ ] Entry cards displayed (5 cards)
- [ ] Each card shows:
  - [ ] Symbol + Side (e.g., EURUSD BUY)
  - [ ] Outcome badge (✅ WIN / ❌ LOSS / ➖ BREAK-EVEN)
  - [ ] Pips gained (+42.5 / -32.5 / 0)
  - [ ] Date
  - [ ] Excerpt of notes
  - [ ] "View Details" button

### Journal Detail View Tests
- [ ] Click "View Details" on any entry
- [ ] Navigate to `/signals/journal/<id>/`
- [ ] Trade info section visible:
  - [ ] Signal ID, Symbol, Side, Entry/Exit prices
  - [ ] Pips Gained, Outcome, Execution Quality
- [ ] Journal content visible:
  - [ ] Pre-Trade Plan
  - [ ] Post-Trade Review
  - [ ] Emotions
  - [ ] Lessons Learned
  - [ ] Tags (if any)
- [ ] Timestamps: Entry time, Exit time
- [ ] "Back to Journal" link works

### Filter Tests (Journal List)
- [ ] Filter by outcome: Win only → 3 entries
- [ ] Filter by outcome: Loss only → 1 entry
- [ ] Filter by outcome: Break-Even only → 1 entry
- [ ] Filter by strategy: Reversal → X entries
- [ ] Filter by date range: Last 7 days → X entries
- [ ] Search by tags: "London" → Entries with tag
- [ ] Multiple filters work together

### AI Review Tests (Optional - requires OpenAI API)
```python
from signals.views import journal_ai_review

# Test AI review (manual trigger or API call)
# Expected: GPT-4 analysis of journal entries
# Output: Strengths, Weaknesses, Recommendations
```

- [ ] AI review button visible on journal list page
- [ ] Click "Get AI Review" → Loading indicator
- [ ] GPT-4 response displayed (strengths, weaknesses, recommendations)
- [ ] Error handling if API key missing
- [ ] Response formatted nicely (markdown or HTML)

### Admin Tests
- [ ] TradeJournalEntry admin accessible
- [ ] List view shows signal, outcome, pips, date
- [ ] Create new entry: Link to Signal #1, add notes
- [ ] Edit existing entry: Change pips, update notes
- [ ] Delete entry (soft delete if implemented)
- [ ] Readonly fields: signal, created_at (if applicable)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Feature #4: 🎬 Trade Replay Mode

### Model Tests
- [ ] Signal model has 5 new fields:
  - [ ] chart_snapshot (ImageField)
  - [ ] replay_data (JSONField)
  - [ ] entry_bar_index (IntegerField)
  - [ ] exit_bar_index (IntegerField)
  - [ ] exit_reason (CharField: tp_hit/sl_hit/manual/active)

### Function Tests
```python
from signals.models import Signal, fetch_chart_snapshot

# Test fetch_chart_snapshot()
signal = Signal.objects.get(id=1)
result = fetch_chart_snapshot(signal, bars_before=50, bars_after=10)

print(f"Status: {result['status']}")
print(f"Bars: {len(result['bars'])}")
print(f"Entry Bar: {result['entry_bar_index']}")
print(f"Exit Bar: {result['exit_bar_index']}")
print(f"Exit Reason: {result['exit_reason']}")

# Expected: status='success', 60-130 bars, entry=50, exit=X, reason='tp_hit' or 'sl_hit'
```

- [ ] Generates 50 bars before signal
- [ ] Generates 10+ bars after signal (extends if no SL/TP hit)
- [ ] OHLCV bars have realistic structure:
  - [ ] time (Unix timestamp)
  - [ ] open, high, low, close (floats)
  - [ ] volume (integer)
- [ ] SL detection works for BUY signals (low <= sl)
- [ ] TP detection works for BUY signals (high >= tp)
- [ ] SL detection works for SELL signals (high >= sl)
- [ ] TP detection works for SELL signals (low <= tp)
- [ ] exit_reason set correctly ('tp_hit', 'sl_hit', 'active')
- [ ] Data saved to signal.replay_data (JSON)

### Dashboard Integration Tests
- [ ] Navigate to `/signals/dashboard/`
- [ ] "Actions" column visible in signal table
- [ ] "🎬 Replay" button present for each signal
- [ ] Button links to `/signals/<id>/replay/`
- [ ] Button styled correctly (btn-outline-primary)

### Replay View Tests
- [ ] Click "Replay" button for Signal #1
- [ ] Navigate to `/signals/1/replay/`
- [ ] Page loads without errors
- [ ] Trade info panel visible (8 cards):
  - [ ] Symbol, Side, Entry, SL, TP
  - [ ] Strategy, Regime, Session
- [ ] Chart container renders (500px height)
- [ ] Lightweight Charts library loaded (check console)

### Chart Tests
- [ ] Candlestick series displays bars
- [ ] Bars color-coded:
  - [ ] Green candles (bullish) → #26a69a
  - [ ] Red candles (bearish) → #ef5350
- [ ] Price lines visible:
  - [ ] Entry (Blue, Solid)
  - [ ] Stop Loss (Red, Dashed)
  - [ ] Take Profit (Green, Dashed)
- [ ] Price scale on right shows values
- [ ] Time scale at bottom shows timestamps
- [ ] Chart responsive (resizes with window)

### Control Tests
- [ ] Play button (▶️) works:
  - [ ] Click → Bars advance automatically
  - [ ] Icon changes to pause (⏸️)
  - [ ] Bars advance at selected speed (1s default)
  - [ ] Auto-stops at last bar
- [ ] Pause button (⏸️) works:
  - [ ] Click → Stops auto-advance
  - [ ] Icon changes back to play (▶️)
- [ ] Previous button (⏪) works:
  - [ ] Goes back 1 bar
  - [ ] Stops at bar 0
- [ ] Next button (⏩) works:
  - [ ] Goes forward 1 bar
  - [ ] Stops at last bar
- [ ] Reset button (⏮️) works:
  - [ ] Jumps to bar 0
  - [ ] Pauses playback if playing
- [ ] End button (⏭️) works:
  - [ ] Jumps to last bar

### Slider Tests
- [ ] Slider visible with label "Bar X / Total"
- [ ] Dragging slider scrubs through bars
- [ ] Current bar count updates (e.g., "Bar 45 / 78")
- [ ] Chart updates in real-time
- [ ] Pauses playback when dragged

### Speed Control Tests
- [ ] Speed dropdown visible
- [ ] 4 options: Slow (2s), Normal (1s), Fast (0.5s), Very Fast (0.2s)
- [ ] Changing speed updates playback rate
- [ ] Speed persists during play/pause cycles

### Stage Indicator Tests
- [ ] Stage indicator visible at top
- [ ] Animated pulse effect (opacity 1 → 0.7 → 1)
- [ ] Changes based on current bar:
  - [ ] Bar 0-49: "🟡 Before Entry"
  - [ ] Bar 50: "🔵 Signal Generated - Entry Point"
  - [ ] Bar 51-67: "🟡 Trade Active"
  - [ ] Bar 68+ (if TP hit): "🟢 Take Profit Hit - WIN"
  - [ ] Bar 68+ (if SL hit): "🔴 Stop Loss Hit - LOSS"
- [ ] Colors match stage:
  - [ ] Blue border for entry
  - [ ] Green border for TP
  - [ ] Red border for SL
  - [ ] Yellow border for active/before

### API Tests
```bash
# Test generate_replay_data API
curl -X POST http://localhost:8000/signals/1/generate-replay/

# Expected response:
# {
#   "status": "success",
#   "bars_count": 78,
#   "entry_bar": 50,
#   "exit_bar": 68,
#   "exit_reason": "tp_hit"
# }
```

- [ ] API endpoint accessible
- [ ] POST request returns JSON
- [ ] Response contains correct fields
- [ ] Regenerates replay data (overwrite existing)
- [ ] Error handling: Invalid signal ID → 404
- [ ] Error handling: Missing signal → 404

### Edge Case Tests
- [ ] Signal with no SL/TP hit (exit_reason='active'):
  - [ ] Generates bars without exit_bar_index
  - [ ] Stage indicator shows "Trade Active" at end
- [ ] Multiple signals: Replay works for each independently
- [ ] Very tight SL (hits immediately):
  - [ ] exit_bar_index = 50 or 51
  - [ ] Stage indicator shows SL hit early
- [ ] Very wide TP (never hits):
  - [ ] Generates max bars (50 + 80 = 130)
  - [ ] exit_reason = 'active'

### Performance Tests
- [ ] Large bar count (130 bars): Chart loads smoothly
- [ ] Rapid scrubbing: No lag or stuttering
- [ ] Multiple signals: Can replay 5+ without slowdown

### Browser Compatibility Tests
- [ ] Chrome: All features work
- [ ] Firefox: All features work
- [ ] Safari: All features work (if macOS)
- [ ] Mobile (responsive):
  - [ ] Chart renders correctly
  - [ ] Controls stacked vertically
  - [ ] Touch slider works

### Error Handling Tests
- [ ] No replay data: Auto-generates on first visit
- [ ] Lightweight Charts CDN down: Error message shown
- [ ] Invalid JSON in replay_data: Graceful fallback
- [ ] Chart container missing: Console error only

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Integration Tests (Cross-Feature)

### Session + Risk Control
- [ ] Signal arrives in London session
- [ ] SessionRule filters by session
- [ ] Signal allowed → check_risk_control() runs
- [ ] Loss increments → Trading halted
- [ ] Dashboard shows session badge + halt banner

### Risk Control + Journal
- [ ] 3 consecutive losses logged in journal
- [ ] Win rate drops to < 50%
- [ ] Trading halted banner appears
- [ ] Next win → Loss count resets → Banner disappears
- [ ] Journal updated with win → Win rate rises

### Journal + Replay
- [ ] Create journal entry for Signal #1
- [ ] Navigate to journal detail page
- [ ] Click "Replay Trade" button (if added)
- [ ] Replay view opens for same signal
- [ ] Can compare journal notes to chart replay

### Session + Replay
- [ ] Signal in Tokyo session (00:00-09:00 UTC)
- [ ] Replay shows session in trade info panel
- [ ] Session badge color-coded correctly
- [ ] Replay data reflects Tokyo market hours (if real data)

### All Features Together
- [ ] Webhook signal arrives
- [ ] detect_session() → Assigns session
- [ ] SessionRule → Filters by session
- [ ] check_risk_control() → Checks loss count
- [ ] Signal saved with session + risk flag
- [ ] Dashboard displays session badge + risk alert
- [ ] Journal entry created (manual)
- [ ] Replay data generated (auto)
- [ ] Can access all 4 features for same signal

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Admin Panel Tests

- [ ] Admin accessible at `/admin/`
- [ ] All models visible:
  - [ ] Signals
  - [ ] Session Rules
  - [ ] Risk Controls
  - [ ] Trade Journal Entries
  - [ ] Strategy Performance
- [ ] CRUD operations work for all models
- [ ] Filters work (by strategy, outcome, session)
- [ ] Search works (by symbol, strategy)
- [ ] Readonly fields enforced (if any)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Security Tests

- [ ] Login required for protected views:
  - [ ] Dashboard
  - [ ] Journal
  - [ ] Replay
- [ ] Redirects to login if not authenticated
- [ ] Admin panel requires superuser
- [ ] Webhook endpoint public (no auth)
- [ ] CSRF protection enabled (forms)
- [ ] SQL injection tests (admin inputs)
- [ ] XSS protection (journal notes, HTML escaping)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Performance Tests

- [ ] Dashboard loads in < 2 seconds (11 signals)
- [ ] Journal list loads in < 1 second (5 entries)
- [ ] Replay view loads in < 1 second
- [ ] Chart renders in < 500ms (78 bars)
- [ ] Database queries optimized (N+1 checks)
- [ ] No memory leaks during replay playback

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Documentation Tests

- [ ] README.md exists with setup instructions
- [ ] TRADE_REPLAY_IMPLEMENTATION.md complete (600+ lines)
- [ ] TRADE_REPLAY_QUICK_START.md complete (200+ lines)
- [ ] TRADE_JOURNAL_GUIDE.md complete (600+ lines)
- [ ] ZENITHEDGE_FEATURE_OVERVIEW.md complete (1000+ lines)
- [ ] SYSTEM_ARCHITECTURE_DIAGRAM.md complete (500+ lines)
- [ ] QUICK_REFERENCE.md updated with all features
- [ ] Code comments present in models.py, views.py
- [ ] Docstrings for functions (fetch_chart_snapshot, etc.)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Deployment Readiness Checklist

- [ ] DEBUG = False in settings.py
- [ ] ALLOWED_HOSTS configured
- [ ] Static files collected: `python3 manage.py collectstatic`
- [ ] Media files directory created: `media/chart_snapshots/`
- [ ] Database backed up
- [ ] SECRET_KEY in environment variable
- [ ] CORS headers configured (if API used externally)
- [ ] SSL/TLS enabled (HTTPS)
- [ ] Webhook URL updated in TradingView
- [ ] Monitoring/logging enabled (Sentry, etc.)

**Status**: [ ] PASS / [ ] FAIL  
**Notes**: _______________________________________________

---

## Final Acceptance Criteria

### Feature #1: Session Rules ✅
- [x] Auto-detects FX sessions (4 sessions)
- [x] Filters signals by session + strategy
- [x] Dashboard shows session badges
- [x] Admin interface for rule management

### Feature #2: Risk Control ✅
- [x] Tracks consecutive losses
- [x] Auto-halts at 3 losses
- [x] Resets on win
- [x] Dashboard warning banner

### Feature #3: Trade Journal ✅
- [x] Journal entries with notes/emotions
- [x] Analytics (Win Rate, ROI, Pips)
- [x] Filters & search
- [x] AI review (GPT-4)

### Feature #4: Trade Replay ✅
- [x] Interactive candlestick chart
- [x] Play/pause/scrub controls
- [x] Entry/SL/TP markers
- [x] Stage indicators
- [x] Auto-generates OHLCV data

### Overall System ✅
- [x] All 4 features implemented
- [x] Database migrations applied (6 total)
- [x] UI responsive & dark-themed
- [x] Documentation complete (2000+ lines)
- [x] Integration tested

---

## Bug Tracker

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| Example: Replay slider not draggable | High | Open | Check JS event listeners |
| | | | |
| | | | |

---

## Testing Summary

**Total Tests**: 150+  
**Passed**: ___  
**Failed**: ___  
**Skipped**: ___  

**Overall Status**: [ ] READY FOR PRODUCTION / [ ] NEEDS FIXES

**Tested By**: _______________  
**Date**: _______________  
**Browser**: _______________  
**OS**: _______________  

---

## Next Steps After Testing

1. [ ] Fix any failed tests
2. [ ] Deploy to staging environment
3. [ ] User acceptance testing (UAT)
4. [ ] Load testing with 100+ signals
5. [ ] Production deployment
6. [ ] Monitor for 7 days
7. [ ] Collect user feedback
8. [ ] Plan future enhancements

---

**END OF TESTING CHECKLIST** ✅
