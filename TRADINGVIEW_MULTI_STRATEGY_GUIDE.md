# ZenithEdge Unified Multi-Strategy TradingView Indicator

## 📋 Overview

This comprehensive TradingView Pine Script indicator detects trading setups across **10 major strategies** in real-time, triggering webhook alerts when valid conditions occur. All alerts use ZenithEdge's JSON webhook format for seamless integration with your trading platform.

---

## 🎯 Supported Strategies

### 1️⃣ **Smart Money Concepts (SMC)**
**Detection Logic:**
- Break of Structure (BOS) & Change of Character (CHoCH)
- Order Blocks (OB) - last engulfing candle before major moves
- Fair Value Gaps (FVG) - price gaps between candle bodies
- Liquidity Sweeps - wicks piercing highs/lows then reversing
- **Trigger:** CHoCH + OB + FVG confluence alignment

**Confidence Calculation:**
- Base: 50
- Order Block: +12
- Fair Value Gap: +10
- Liquidity Sweep: +8
- Multi-TF Alignment: +10
- Low ATR (< 0.5%): +8
- Session (London/NY): +5
- **Max: 100**

---

### 2️⃣ **ICT Timing**
**Detection Logic:**
- Liquidity grabs during London (07:00-10:00 UTC) and NY (13:00-16:00 UTC) killzones
- Wick rejections at session highs/lows (wick > 0.6 × ATR)
- **Trigger:** Wick rejection during active session

**Confidence Calculation:**
- Base: 55
- Wick Rejection: +20
- Multi-TF Alignment: +8
- **Max: 83**

---

### 3️⃣ **Trend-Following**
**Detection Logic:**
- Moving Average crossover (10/30 SMA)
- ADX > 25 confirms trend strength
- SuperTrend color flip (implicit in MA cross)
- Higher confidence with multi-timeframe alignment

**Confidence Calculation:**
- Base: 45
- ADX Strength: +0-20 (scaled: ADX ÷ 2, capped at 20)
- Multi-TF Alignment: +10
- Volume Spike: +8
- **Max: 100**

---

### 4️⃣ **Breakout**
**Detection Logic:**
- Detects 20-bar Donchian Channel range
- Breakout confirmed when candle closes outside range
- Volume spike required (> 1.5× 20-bar average)
- Optional: London Breakout using Asian session range

**Confidence Calculation:**
- Base: 40
- Volume Spike: +20
- Multi-TF Alignment: +10
- **Max: 70**

---

### 5️⃣ **Mean Reversion**
**Detection Logic:**
- RSI(14) < 30 → buy zone; RSI > 70 → sell zone
- Bollinger Band touches (price at BB upper/lower)
- VWAP rejection confirmation boosts confidence

**Confidence Calculation:**
- Base: 35
- Extreme RSI (<20 or >80): +15
- VWAP Rejection: +10
- **Max: 60**

---

### 6️⃣ **Squeeze**
**Detection Logic:**
- Bollinger Bands inside Keltner Channels (volatility contraction)
- **Trigger:** Breakout bar closes outside both envelopes
- Confidence scaled by breakout strength

**Confidence Calculation:**
- Base: 55
- **Max: 55** (fixed)

---

### 7️⃣ **Scalping / Intraday Momentum**
**Detection Logic:**
- **Timeframe:** 1-min or 5-min ONLY
- RSI-3 crossing 50 (fast momentum)
- EMA(5) × EMA(13) crossover
- Volume spike required
- **Exit:** Quick targets at 1R–1.5R

**Confidence Calculation:**
- Base: 45
- RSI-3 Cross: +15
- EMA Crossover: +10
- Volume Spike: +15
- **Max: 85**

---

### 8️⃣ **VWAP Reclaim**
**Detection Logic:**
- Price crosses VWAP after multiple touches
- **Long:** Reclaim above VWAP + higher lows (3 bars)
- **Short:** Reclaim below VWAP + lower highs (3 bars)

**Confidence Calculation:**
- Base: 50
- VWAP Presence: +5-20 (variable)
- **Max: 70**

---

### 9️⃣ **Supply & Demand Zones**
**Detection Logic:**
- Mark zones from strong displacement candles (> 1.5 × ATR)
- **Trigger:** Price retests zone and rejects (candle closes away from zone)

**Confidence Calculation:**
- Base: 55
- **Max: 55** (fixed)

---

### 🔟 **Multi-Timeframe Confluence**
**Detection Logic:**
- Uses `request.security()` to fetch 2 higher timeframe trends (default: 4H + 1H)
- **Trigger:** Current TF aligns with BOTH higher TFs
- Only fires when all 3 timeframes show same directional bias

**Confidence Calculation:**
- Base: 50
- HTF Trend Exists: +15
- HTF2 Aligns with HTF: +15
- Current TF Aligns: +10
- ADX Confirms: +10
- **Max: 100**

---

## 🔧 Configuration

### **User Inputs**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `mode` | "All" | Strategy filter: All, SMC, ICT, Trend, Breakout, MeanReversion, Squeeze, Scalp, VWAP, SupplyDemand, MultiTF |
| `user_uuid` | "" | Your ZenithEdge user UUID for webhook authentication |
| `min_confidence_alert` | 35 | Minimum confidence (0-100) to trigger alerts |
| `atrPeriod` | 14 | ATR calculation period |
| `atrMultSL` | 1.5 | Stop Loss multiplier (× ATR) |
| `atrMultTP` | 3.0 | Take Profit multiplier (× ATR) |
| `fastMA_len` | 10 | Fast moving average length |
| `slowMA_len` | 30 | Slow moving average length |
| `adx_len` | 14 | ADX period |
| `adx_threshold` | 25 | Minimum ADX for trend confirmation |
| `bbLen` | 20 | Bollinger Bands period |
| `bbMult` | 2.0 | Bollinger Bands standard deviation |
| `kcLen` | 20 | Keltner Channels period |
| `kcMult` | 1.5 | Keltner Channels ATR multiplier |
| `donchianLen` | 20 | Donchian Channel period (breakout range) |
| `searchLookback` | 80 | Max bars to search for OB/FVG |
| `rsi3_len` | 3 | RSI length for scalping |
| `ema_scalp_fast` | 5 | Fast EMA for scalping |
| `ema_scalp_slow` | 13 | Slow EMA for scalping |
| `scalp_rr_min` | 1.0 | Minimum R:R for scalp exits |
| `scalp_rr_max` | 1.5 | Maximum R:R for scalp exits |
| `htf_tf` | "240" | Primary higher timeframe (4H) |
| `htf_tf2` | "60" | Secondary higher timeframe (1H) |
| `show_debug` | false | Display JSON debug label on chart |
| `plot_shapes` | true | Show strategy markers on chart |
| `show_Zones` | true | Draw OB/FVG/SD zones |
| `show_BOS` | true | Show BOS/CHoCH labels |
| `show_Sessions` | true | Highlight London/NY sessions |

### **Session Timing (UTC)**

| Session | Start | End |
|---------|-------|-----|
| London | 07:00 | 10:00 |
| New York | 13:00 | 16:00 |

*Adjust `london_start_h`, `london_end_h`, `ny_start_h`, `ny_end_h` inputs for broker time offsets*

---

## 📊 Visual Elements

### **Chart Markers**
- **Strategy Labels:** Color-coded entry signals with confidence %
  - 🟢 Green: BUY signals
  - 🔴 Red: SELL signals
- **BOS/CHoCH Labels:** Blue (BOS) & Purple (CHoCH) markers
- **Zone Rectangles:**
  - Purple: Bullish Order Blocks
  - Orange: Bearish Order Blocks
  - Yellow: Fair Value Gaps
  - Teal: Supply/Demand Zones

### **Session Backgrounds**
- Light Blue: London session
- Light Orange: NY session

### **Plots (Hidden - for alerts)**
- `plot_0`: Stop Loss level
- `plot_1`: Take Profit level
- `plot_2`: Confidence score (0-100)

---

## 🚨 Alert Configuration

### **Webhook JSON Format**

```json
{
  "user_uuid": "USER_UUID",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "strategy": "STRATEGY_NAME",
  "regime": "REGIME_NAME",
  "structure": "BOS/CHOCH/OB/FVG/etc",
  "side": "buy|sell",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "extra": {
    "session": "London|NY|Other",
    "multi_tf": {
      "4H": "bull|bear|flat",
      "1H": "bull|bear|flat"
    },
    "explain": "Confidence breakdown details"
  }
}
```

### **Setting Up Alerts in TradingView**

1. **Add Indicator to Chart**
   - Open TradingView chart
   - Click "Indicators" → Search "ZenithEdge Pro"
   - Add to chart

2. **Configure Alert**
   - Click "Alert" button (clock icon)
   - **Condition:** Select "ZenithEdge PRO Signal (static)"
   - **Alert Name:** ZenithEdge Multi-Strategy
   - **Message:** Use webhook JSON template above
   - **Webhook URL:** `https://your-zenithedge-domain.com/signals/webhook/`
   - **Options:** 
     - ✅ Once Per Bar Close
     - ✅ Webhook URL

3. **Test Alerts**
   - Enable `show_debug = true` in indicator settings
   - View JSON output on chart when signals fire
   - Copy JSON and test with ZenithEdge webhook endpoint

---

## 🎨 Regime Classification

The indicator automatically classifies market regime:

| Regime | Conditions |
|--------|-----------|
| **Trending** | ADX > 25 |
| **Ranging** | ADX < 20 AND ATR < 1.5% |
| **Volatile** | ATR > 1.5% |
| **Consolidation** | Squeeze active OR ATR < 0.5% |
| **Neutral** | None of the above |

---

## ⚙️ Tuning Confidence Calculations

All confidence functions are modular and clearly marked with `⚙️ Adjust` comments. To customize:

1. **Open Pine Script Editor**
2. **Search for `⚙️ Adjust`** - finds all tunable parameters
3. **Modify weights** (examples):

```pine
// Example: Increase SMC Order Block importance
ob_bonus = not na(lastBullOB_bar) or not na(lastBearOB_bar) ? 15.0 : 0.0  // Changed from 12.0

// Example: Lower minimum confidence for scalping
base = 40.0  // Changed from 45.0

// Example: Require stronger ADX for trends
adx_bonus = math.min(25.0, adx_val / 1.5)  // Increased from 20.0 max
```

---

## 🧪 Testing & Validation

### **Recommended Instruments**
- **Forex:** EURUSD, GBPJPY, XAUUSD
- **Crypto:** BTCUSD, ETHUSD
- **Indices:** SPX500, NAS100, US30

### **Validation Checklist**
- ✅ Signals fire once per valid setup (no spam)
- ✅ Stop Loss & Take Profit levels are logical
- ✅ Confidence scores correlate with visual quality
- ✅ JSON debug output matches plot values
- ✅ Webhook delivers successfully to ZenithEdge
- ✅ No repainting (all signals on confirmed close)

### **Performance Expectations**

| Strategy | Avg. Signals/Day | Win Rate Target | Best Timeframes |
|----------|------------------|-----------------|-----------------|
| SMC | 2-5 | 60-70% | 15m, 1H, 4H |
| ICT | 1-3 | 65-75% | 5m, 15m |
| Trend | 1-2 | 55-65% | 1H, 4H, D |
| Breakout | 1-4 | 50-60% | 15m, 1H |
| Mean Reversion | 3-8 | 60-70% | 5m, 15m, 1H |
| Squeeze | 0-2 | 55-65% | 1H, 4H |
| Scalp | 10-30 | 55-60% | 1m, 5m |
| VWAP | 2-6 | 60-70% | 5m, 15m |
| Supply/Demand | 1-3 | 60-70% | 15m, 1H, 4H |
| Multi-TF | 1-3 | 70-80% | 15m, 1H |

---

## 🚀 Deployment Steps

### **Phase 1: Installation**
1. Copy `TRADINGVIEW_INDICATOR_TEMPLATE.pine` content
2. Open TradingView Pine Editor
3. Paste code and click "Save"
4. Name: "ZenithEdge Pro Multi-Strategy"
5. Add to chart

### **Phase 2: Configuration**
1. Set `user_uuid` to your ZenithEdge user UUID
2. Adjust `min_confidence_alert` (start with 40)
3. Enable `show_debug` for testing
4. Configure visual toggles as preferred

### **Phase 3: Testing**
1. Run on multiple instruments (EURUSD, XAUUSD, BTCUSD)
2. Verify signals on historical data (replay mode)
3. Check JSON output format
4. Test webhook with dummy endpoint (requestbin.com)

### **Phase 4: Production**
1. Disable `show_debug` (reduce chart clutter)
2. Set up TradingView alerts with webhook URL
3. Configure alert frequency: "Once Per Bar Close"
4. Monitor ZenithEdge dashboard for incoming signals
5. Start with paper trading / demo account

---

## 🔥 Advanced Features

### **Strategy Priority**
Signals are detected in priority order:
1. SMC (highest confidence potential)
2. ICT
3. Trend
4. Breakout
5. Mean Reversion
6. Squeeze
7. VWAP
8. Supply/Demand
9. Scalp
10. Multi-TF

Only ONE strategy fires per bar (first match wins).

### **Anti-Repainting**
- All signals use `barstate.isconfirmed` or historical data
- `request.security()` uses `lookahead=barmerge.lookahead_off`
- Zone drawings limited to confirmed bars

### **Performance Optimization**
- Zone boxes limited to last 100 bars
- FVG search capped at 30 bars
- OB/SD search configurable (default 80 bars)
- Labels auto-managed by TradingView (max 1000)

---

## 📝 Maintenance & Updates

### **Version Control**
- Current Version: **v1.0 (November 2025)**
- Update frequency: Monthly (or as needed)

### **Common Adjustments**
1. **Too many signals:** Increase `min_confidence_alert`
2. **Missing signals:** Lower base confidence values
3. **False breakouts:** Increase `vol_spike` threshold
4. **Scalping too aggressive:** Tighten `scalp_rr_max`

### **Logging Changes**
When adjusting confidence weights, document in Pine comments:
```pine
// 2025-11-10: Increased SMC OB weight from 12 to 15 for XAUUSD
ob_bonus = not na(lastBullOB_bar) or not na(lastBearOB_bar) ? 15.0 : 0.0
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| No signals firing | Lower `min_confidence_alert` to 30 |
| Too many signals | Increase to 50+ |
| Zones not showing | Enable `show_Zones = true` |
| Webhook not delivering | Verify `user_uuid` matches ZenithEdge account |
| JSON format errors | Enable `show_debug` to inspect output |
| Scalping not working | Confirm timeframe is 1m or 5m |
| Multi-TF always neutral | Check HTF timeframes are higher than current |

---

## 📞 Support

- **Documentation:** See `TRADINGVIEW_SETUP_GUIDE.md`
- **ZenithEdge Dashboard:** Monitor signal performance
- **Webhook Endpoint:** `/signals/webhook/`
- **Test Signals:** Use replay mode in TradingView

---

## 🎓 Best Practices

1. **Start with one strategy** (set `mode = "SMC"`) before using "All"
2. **Backtest thoroughly** using TradingView's Strategy Tester
3. **Paper trade first** - verify signal quality before live trading
4. **Monitor confidence distribution** - adjust weights if most signals are 35-40
5. **Use higher timeframes** (1H+) for swing trading, lower (5m-15m) for intraday
6. **Combine with manual analysis** - indicator is a tool, not a replacement for judgment
7. **Review rejected signals** - low confidence can still be valid in right context

---

## ✅ Completion Checklist

Before going live:
- [ ] `user_uuid` configured
- [ ] Tested on 3+ instruments
- [ ] Webhook delivers successfully
- [ ] Confidence scores validate visually
- [ ] No repainting observed
- [ ] Alert frequency set correctly
- [ ] Paper trading results reviewed
- [ ] Risk management rules defined
- [ ] Dashboard monitoring active

---

**🚀 Ready to deploy! Monitor performance and adjust weights as needed.**
