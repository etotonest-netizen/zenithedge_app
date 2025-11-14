# TradingView Webhook Integration Guide

## 🎯 Quick Overview

Your ZenithEdge system requires specific fields from TradingView. This guide ensures 100% compatibility.

---

## ✅ System Requirements

Your webhook endpoint expects this JSON format:

```json
{
  "symbol": "EURUSD",           // Chart symbol
  "timeframe": "1H",            // Chart timeframe
  "side": "buy",                // Trade direction: "buy" or "sell"
  "sl": 1.0820,                 // Stop loss price
  "tp": 1.0920,                 // Take profit price
  "confidence": 85,             // Confidence score 0-100
  "strategy": "ZenithEdge",     // Strategy name
  "regime": "Trend",            // Market regime type
  "price": 1.0850,              // Current price (optional)
  "timestamp": "2025-11-09..."  // ISO timestamp (optional)
}
```

**Valid Regime Values:**
- `"Trend"`
- `"Breakout"`
- `"MeanReversion"`
- `"Squeeze"`

---

## 🔧 Step-by-Step Setup

### Step 1: Get Your Webhook URL

1. Login to your ZenithEdge dashboard
2. Navigate to: **Webhook Setup** (in navigation menu)
3. Copy your unique webhook URL:
   ```
   http://your-server.com/api/v1/signal/YOUR-UUID-HERE/
   ```

### Step 2: Add Indicator to TradingView

1. Use the provided `TRADINGVIEW_INDICATOR_TEMPLATE.pine` file
2. Open TradingView Pine Editor
3. Paste the code and click "Add to Chart"
4. The indicator will plot:
   - `plot_0` = Stop Loss
   - `plot_1` = Take Profit
   - `plot_2` = Confidence Score

### Step 3: Create Alert in TradingView

1. Right-click on chart → **"Add Alert"** (or press `Alt+A`)
2. Set these fields:
   - **Condition:** Select "Trend Long Signal" (or your alert type)
   - **Webhook URL:** Paste your URL from Step 1
   - **Message:** Use template below

### Step 4: Configure Alert Message

Copy and paste the appropriate JSON template:

#### For LONG Trend Signals:
```json
{
  "user_uuid": "YOUR-UUID-HERE",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Trend"
}
```

#### For SHORT Trend Signals:
```json
{
  "user_uuid": "YOUR-UUID-HERE",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "sell",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Trend"
}
```

#### For BREAKOUT Signals:
```json
{
  "user_uuid": "YOUR-UUID-HERE",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Breakout"
}
```

#### For MEAN REVERSION Signals:
```json
{
  "user_uuid": "YOUR-UUID-HERE",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "MeanReversion"
}
```

#### For SQUEEZE Signals:
```json
{
  "user_uuid": "YOUR-UUID-HERE",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Squeeze"
}
```

**Important:**
- Replace `YOUR-UUID-HERE` with your actual UUID from Step 1
- Change `"side"` to `"buy"` or `"sell"` based on signal direction
- Keep `{{ticker}}`, `{{interval}}`, `{{close}}`, `{{plot_0}}`, etc. as-is (TradingView replaces these)

### Step 5: Alert Settings

Configure these alert options:
- **Options:** Check "Webhook URL"
- **Expiration:** Set to your preference (recommend: Once per bar close)
- **Alert actions:** Webhook URL

Click **"Create"** to activate the alert.

---

## 🧪 Testing Your Setup

### Method 1: Manual Test with curl

```bash
curl -X POST "http://your-server.com/api/v1/signal/YOUR-UUID/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_uuid": "YOUR-UUID",
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0820,
    "tp": 1.0920,
    "confidence": 85,
    "strategy": "ZenithEdge",
    "regime": "Trend",
    "price": 1.0850
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "signal_id": 123,
  "message": "Signal received and processed",
  "evaluation": {
    "passed": true,
    "blocked_reason": "passed",
    "ai_score": 75,
    "checks": {
      "news": true,
      "prop": true,
      "score": true,
      "strategy": true
    }
  }
}
```

### Method 2: Check Dashboard

1. Login to your dashboard: `http://your-server.com/signals/dashboard/`
2. You should see your test signal appear
3. Verify all fields are populated correctly

---

## 🚨 Common Issues & Solutions

### Issue 1: Signals Not Arriving

**Symptoms:** Alert fires in TradingView but no signal in dashboard

**Solutions:**
- ✅ Check webhook is **Active** (green badge in webhook setup)
- ✅ Verify UUID in JSON matches your webhook URL
- ✅ Check TradingView alert is active (bell icon should be filled)
- ✅ Look at server logs: `tail -f zenithedge.log`

### Issue 2: Invalid JSON Error

**Symptoms:** `400 Bad Request` or "Invalid JSON" error

**Solutions:**
- ✅ Check for typos in JSON template
- ✅ Ensure all TradingView variables are correct: `{{ticker}}`, `{{interval}}`, `{{close}}`, `{{plot_0}}`, `{{plot_1}}`, `{{plot_2}}`
- ✅ Verify your Pine Script plots values (check with `pine.label`)
- ✅ Don't use trailing commas in JSON
- ✅ Use double quotes `"` not single quotes `'`

### Issue 3: Wrong Data in Signals

**Symptoms:** Signal appears but with incorrect values

**Solutions:**
- ✅ Verify `plot_0` = Stop Loss in your indicator
- ✅ Verify `plot_1` = Take Profit in your indicator
- ✅ Verify `plot_2` = Confidence (0-100) in your indicator
- ✅ Check plot order matches (first plot() is plot_0, second is plot_1, etc.)
- ✅ Ensure confidence is between 0-100

### Issue 4: Side Field Always Wrong

**Symptoms:** All signals show same direction

**Solutions:**
- ✅ Create **separate alerts** for long and short signals
- ✅ Long alert uses `"side": "buy"`
- ✅ Short alert uses `"side": "sell"`
- ✅ Can't use `{{strategy.order.action}}` with indicators (only strategies)

### Issue 5: Signal Blocked by Validation

**Symptoms:** Signal received but marked as blocked

**Solutions:**
- ✅ Check AI score meets minimum threshold (default: 30)
- ✅ Verify no high-impact news events (if news filter enabled)
- ✅ Check prop challenge limits not exceeded
- ✅ Ensure regime is valid: "Trend", "Breakout", "MeanReversion", or "Squeeze"
- ✅ Verify strategy field is not empty

---

## 📊 Pine Script Requirements

Your indicator MUST include these plots:

```pinescript
plot(stopLoss, "Stop Loss", display=display.none)      // plot_0
plot(takeProfit, "Take Profit", display=display.none)  // plot_1
plot(confidence, "Confidence", display=display.none)   // plot_2
```

**Important Rules:**
- Plots must be in this order
- Values must not be `na` when alert fires
- Confidence must be 0-100
- SL and TP must be positive numbers

---

## 🎨 Customizing for Your Strategy

### Change Strategy Name
In alert JSON, modify:
```json
"strategy": "YourStrategyName"
```

### Multiple Regime Types
Create separate alerts for each regime:
- Alert 1: Trend → `"regime": "Trend"`
- Alert 2: Breakout → `"regime": "Breakout"`
- Alert 3: Mean Reversion → `"regime": "MeanReversion"`
- Alert 4: Squeeze → `"regime": "Squeeze"`

### Dynamic Confidence Scoring
In your Pine Script:
```pinescript
// Example: Base confidence on multiple factors
trendStrength = math.abs(fastMA - slowMA) / slowMA * 100
volumeConfidence = volume > ta.sma(volume, 20) ? 20 : 0
confidence = math.min(trendStrength + volumeConfidence, 100)
```

---

## ✅ Verification Checklist

Before going live, verify:

- [ ] Webhook URL is correct and active
- [ ] UUID in JSON matches webhook URL
- [ ] Pine Script plots SL, TP, Confidence in order
- [ ] Alert message JSON is valid (no syntax errors)
- [ ] `"side"` is "buy" or "sell" (lowercase)
- [ ] `"regime"` is one of: "Trend", "Breakout", "MeanReversion", "Squeeze"
- [ ] `"strategy"` field has a value
- [ ] Tested with curl and received success response
- [ ] Signal appears in dashboard with correct data
- [ ] Created separate alerts for long/short signals
- [ ] Alert expiration set appropriately

---

## 📚 Additional Resources

- **Webhook Setup UI:** `/signals/webhook-setup/`
- **Dashboard:** `/signals/dashboard/`
- **API Documentation:** `QUICK_REFERENCE.md`
- **Full Guide:** `docs/WEBHOOK_WIZARD.md`

---

## 🆘 Need Help?

1. Check server logs: `tail -f zenithedge.log`
2. Test with curl first before TradingView
3. Use ZenBot for troubleshooting: Ask "Why isn't my webhook working?"
4. Verify webhook status in webhook setup page

---

**Last Updated:** November 9, 2025
**Compatibility:** ZenithEdge Trading Hub v1.0+
**TradingView:** Pine Script v5
