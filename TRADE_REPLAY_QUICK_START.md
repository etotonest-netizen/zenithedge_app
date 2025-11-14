# 🚀 Trade Replay Quick Start Guide

## 🎯 What Is It?

**Trade Replay Mode** lets you watch your trades unfold candle-by-candle, like rewatching a game film. See exactly when your stop loss or take profit was hit, and analyze the price action that led to the outcome.

---

## ⚡ Quick Access

### From Dashboard
1. Go to `/signals/dashboard/`
2. Find any signal in the table
3. Click **"🎬 Replay"** button in Actions column

### Direct URL
```
http://localhost:8000/signals/{SIGNAL_ID}/replay/
```

---

## 🎮 Controls Cheat Sheet

| Button | Action | Shortcut |
|--------|--------|----------|
| ⏮️ Reset | Jump to start | - |
| ⏪ Prev | Back 1 bar | - |
| ▶️ Play | Auto-advance | Space (planned) |
| ⏸️ Pause | Stop playback | Space (planned) |
| ⏩ Next | Forward 1 bar | → (planned) |
| ⏭️ End | Jump to last bar | - |
| 🎚️ Slider | Scrub to any bar | Drag |
| ⚡ Speed | Change playback rate | Dropdown |

---

## 📊 Stage Indicators

| Color | Icon | Meaning |
|-------|------|---------|
| 🟡 Yellow | ⏳ | Before signal entry |
| 🔵 Blue | 🚩 | **Signal Generated** - Entry point |
| 🟡 Yellow | 📈 | Trade active (no SL/TP hit yet) |
| 🟢 Green | ✅ | **Take Profit Hit** - WIN |
| 🔴 Red | ❌ | **Stop Loss Hit** - LOSS |

---

## 💡 Pro Tips

1. **Slow Mode** (2s): Best for detailed analysis around SL/TP levels
2. **Slider**: Fastest way to jump to specific bars
3. **Stage Indicator**: Pulses to show current trade phase
4. **Price Lines**: 
   - Blue solid = Entry
   - Red dashed = Stop Loss
   - Green dashed = Take Profit

---

## 🔧 Generate Replay Data Programmatically

### Single Signal
```python
from signals.models import Signal, fetch_chart_snapshot

signal = Signal.objects.get(id=1)
result = fetch_chart_snapshot(signal)
print(f"Generated {len(result['bars'])} bars, exit: {result['exit_reason']}")
```

### All Signals
```python
from signals.models import Signal, fetch_chart_snapshot

for signal in Signal.objects.filter(is_allowed=True):
    if not signal.replay_data:
        fetch_chart_snapshot(signal)
        print(f"✅ Signal #{signal.id} replayed")
```

### API Endpoint
```bash
curl -X POST http://localhost:8000/signals/1/generate-replay/
```

---

## 🐛 Common Issues

**"No replay data found"**  
→ Click Replay button again (auto-generates on first visit)

**Chart not loading**  
→ Check browser console for errors

**Bars not advancing**  
→ Ensure `replay_data` exists in database

---

## 📁 Key Files

```
signals/models.py          # fetch_chart_snapshot(), Signal.replay_data
signals/views.py           # TradeReplayView, generate_replay_data()
signals/urls.py            # /signals/<id>/replay/
templates/trade_replay.html # Interactive chart UI
```

---

## 🎓 Learning Use Cases

1. **Pattern Recognition**: Spot recurring setups before TP/SL
2. **Entry Timing**: Validate signal generation quality
3. **Stop Placement**: Check if SL too tight or too wide
4. **Target Setting**: Analyze if TP too conservative/aggressive
5. **Strategy Testing**: Replay 50+ trades to find issues

---

## 🚦 Status

✅ **Fully Implemented** - Ready for production use  
✅ All backend logic complete  
✅ Interactive chart working  
✅ Database migration applied  
✅ Dashboard integration done  

---

## 📞 Need Help?

See full documentation: `TRADE_REPLAY_IMPLEMENTATION.md`

---

**Happy Replaying! 🎬**
