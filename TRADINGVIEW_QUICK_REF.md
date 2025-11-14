# ZenithEdge Multi-Strategy Indicator - Quick Reference Card

## 🎯 10 Strategies at a Glance

| # | Strategy | Trigger | Timeframe | Base Conf. | Max Conf. |
|---|----------|---------|-----------|------------|-----------|
| 1 | **SMC** | CHoCH + OB + FVG | Any | 50 | 100 |
| 2 | **ICT** | Wick rejection @ killzone | Any | 55 | 83 |
| 3 | **Trend** | MA cross + ADX > 25 | 1H-D | 45 | 100 |
| 4 | **Breakout** | Close outside range + volume | 15m-4H | 40 | 70 |
| 5 | **Mean Rev** | RSI < 30 or > 70 + BB touch | 5m-1H | 35 | 60 |
| 6 | **Squeeze** | BB inside KC, breakout | 1H-4H | 55 | 55 |
| 7 | **Scalp** | RSI-3 cross 50 + EMA cross | 1m-5m | 45 | 85 |
| 8 | **VWAP** | Reclaim + higher lows/lower highs | 5m-1H | 50 | 70 |
| 9 | **S/D** | Zone retest + rejection | 15m-4H | 55 | 55 |
| 10 | **Multi-TF** | 3 timeframes aligned | Any | 50 | 100 |

---

## ⚙️ Essential Settings

```pine
user_uuid = "YOUR_UUID_HERE"          // ← SET THIS FIRST!
min_confidence_alert = 35              // Minimum to trigger alerts
mode = "All"                           // Or: SMC, ICT, Trend, etc.
```

**Visual Toggles:**
```pine
show_Zones = true      // OB/FVG/SD rectangles
show_BOS = true        // BOS/CHoCH labels
show_Sessions = true   // London/NY backgrounds
show_debug = false     // JSON output (testing only)
```

---

## 📊 Confidence Modifiers

### 🔥 High Impact (+15-20)
- Volume spike (Breakout, Scalp)
- Multi-TF alignment (all strategies)
- HTF2 alignment (Multi-TF)
- Extreme RSI (Mean Rev)

### ⚡ Medium Impact (+10-12)
- Order Block presence (SMC)
- Fair Value Gap (SMC)
- ADX strength (Trend)
- Current TF alignment (Multi-TF)

### 💡 Low Impact (+5-8)
- Session timing (London/NY)
- Low ATR (< 0.5%)
- VWAP rejection
- Liquidity sweep

---

## 🚨 Alert Setup (1 minute)

1. **Add indicator to chart**
2. **Set `user_uuid`** in settings
3. **Create alert:**
   - Condition: "ZenithEdge PRO Signal (static)"
   - Webhook URL: `https://your-domain.com/signals/webhook/`
   - Message: *(leave default or use JSON template)*
   - Frequency: **Once Per Bar Close** ✅

4. **Done!** Signals will flow to ZenithEdge dashboard

---

## 🎨 Chart Markers

| Color | Meaning |
|-------|---------|
| 🟢 Green Label | BUY signal |
| 🔴 Red Label | SELL signal |
| 🟣 Purple Box | Bullish Order Block |
| 🟠 Orange Box | Bearish Order Block |
| 🟡 Yellow Box | Fair Value Gap |
| 🔵 Blue Label | BOS (Break of Structure) |
| 🟣 Purple Label | CHoCH (Change of Character) |
| Light Blue BG | London Session |
| Light Orange BG | NY Session |

---

## 📈 Regime Detection

```
Trending:      ADX > 25
Ranging:       ADX < 20 AND ATR < 1.5%
Volatile:      ATR > 1.5%
Consolidation: Squeeze ON or ATR < 0.5%
```

---

## 🛠️ Quick Tuning

**Too many signals?**
```pine
min_confidence_alert = 50  // Increase from 35
```

**Not enough signals?**
```pine
min_confidence_alert = 30  // Decrease from 35
```

**Focus on one strategy:**
```pine
mode = "SMC"  // Options: SMC, ICT, Trend, Breakout, 
               //          MeanReversion, Squeeze, Scalp, 
               //          VWAP, SupplyDemand, MultiTF, All
```

**Scalping too aggressive?**
```pine
scalp_rr_max = 1.2  // Tighter exits (from 1.5)
```

**Adjust stop loss:**
```pine
atrMultSL = 2.0  // Wider stops (from 1.5)
```

---

## 🔍 Testing Checklist

- [ ] Signals fire once per setup (not every bar)
- [ ] SL/TP levels are reasonable
- [ ] Confidence matches visual quality
- [ ] No repainting on closed bars
- [ ] JSON format valid (check with `show_debug = true`)
- [ ] Webhook delivers to ZenithEdge
- [ ] Tested on: EURUSD, XAUUSD, BTCUSD

---

## 📞 Troubleshooting One-Liners

| Problem | Fix |
|---------|-----|
| No signals | Lower `min_confidence_alert` to 25 |
| Webhook fails | Verify `user_uuid` matches account |
| Zones not showing | `show_Zones = true` |
| Scalp not working | Check timeframe is 1m or 5m |
| Multi-TF neutral | Verify HTF > current TF |

---

## 🎯 Confidence Weight Locations

Search for `⚙️ Adjust` in Pine Editor to find ALL tunable weights.

**Example locations:**
- Line ~118: `f_calc_smc_confidence()` - SMC weights
- Line ~145: `f_calc_trend_confidence()` - Trend weights  
- Line ~165: `f_calc_breakout_confidence()` - Breakout weights
- Line ~180: `f_calc_meanrev_confidence()` - Mean reversion weights
- Line ~195: `f_calc_scalp_confidence()` - Scalping weights
- Line ~215: `f_calc_multitf_confidence()` - Multi-TF weights

---

## 🚀 Quick Start (3 steps)

1. **Copy** `TRADINGVIEW_INDICATOR_TEMPLATE.pine` to Pine Editor
2. **Set** `user_uuid = "YOUR_UUID"`
3. **Create Alert** → Webhook URL → Done!

---

## 📊 Webhook JSON Structure

```json
{
  "user_uuid": "abc123...",
  "symbol": "EURUSD",
  "timeframe": "15",
  "strategy": "SMC",
  "regime": "Trending",
  "structure": "CHOCH/OB/FVG",
  "side": "buy",
  "price": 1.0850,
  "sl": 1.0820,
  "tp": 1.0910,
  "confidence": 78,
  "extra": {
    "session": "London",
    "multi_tf": {"4H":"bull","1H":"bull"},
    "explain": "SMC base +OB:12+FVG:10+..."
  }
}
```

---

## 💪 Best Practices

✅ **DO:**
- Start with `mode = "SMC"` or `mode = "Trend"` (single strategy)
- Use higher timeframes (1H+) for swing trading
- Enable `show_debug` during testing
- Paper trade first
- Review signals manually before live trading

❌ **DON'T:**
- Set `min_confidence_alert` below 25 (noise)
- Use scalping on timeframes > 5m
- Trust every signal blindly
- Disable `barstate.isconfirmed` checks (causes repainting)

---

## 📖 Full Documentation

See `TRADINGVIEW_MULTI_STRATEGY_GUIDE.md` for complete details.

---

**Ready to trade smarter? 🚀**
