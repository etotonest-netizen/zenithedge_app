# TradingView Webhook Alert Message Templates

## 📋 Alert Message Template for TradingView

When creating an alert in TradingView, use this JSON message in the "Message" field:

### Standard Template (Copy & Paste)

```json
{
  "user_uuid": "{{user_uuid}}",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "strategy": "{{strategy}}",
  "regime": "{{regime}}",
  "structure": "{{structure}}",
  "side": "{{side}}",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "extra": {
    "session": "{{session}}",
    "multi_tf": {{multi_tf}},
    "explain": "{{explain}}"
  }
}
```

**Note:** TradingView will replace `{{variable}}` with actual values when the alert fires.

---

## 🧪 Test JSON Examples

### Example 1: SMC Long Signal (EURUSD)
```json
{
  "user_uuid": "test-user-12345",
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
    "explain": "SMC base +OB:12+FVG:10+LS:0+MTF:10+ATR:8+Sess:5"
  }
}
```

### Example 2: ICT Short Signal (XAUUSD)
```json
{
  "user_uuid": "test-user-12345",
  "symbol": "XAUUSD",
  "timeframe": "5",
  "strategy": "ICT",
  "regime": "Volatile",
  "structure": "ICT-Grab",
  "side": "sell",
  "price": 2650.50,
  "sl": 2658.00,
  "tp": 2635.00,
  "confidence": 75,
  "extra": {
    "session": "NY",
    "multi_tf": {"4H":"bear","1H":"bear"},
    "explain": "ICT base +WickRej +MTF"
  }
}
```

### Example 3: Scalping Long (BTCUSD)
```json
{
  "user_uuid": "test-user-12345",
  "symbol": "BTCUSD",
  "timeframe": "1",
  "strategy": "Scalp",
  "regime": "Ranging",
  "structure": "Scalp",
  "side": "buy",
  "price": 35420.00,
  "sl": 35380.00,
  "tp": 35480.00,
  "confidence": 70,
  "extra": {
    "session": "Other",
    "multi_tf": {"4H":"flat","1H":"flat"},
    "explain": "Scalp +RSI3:15+EMA:10+Vol:15"
  }
}
```

### Example 4: Breakout Long (SPX500)
```json
{
  "user_uuid": "test-user-12345",
  "symbol": "SPX500",
  "timeframe": "60",
  "strategy": "Breakout",
  "regime": "Consolidation",
  "structure": "Breakout",
  "side": "buy",
  "price": 4520.00,
  "sl": 4495.00,
  "tp": 4570.00,
  "confidence": 65,
  "extra": {
    "session": "NY",
    "multi_tf": {"4H":"bull","1H":"bull"},
    "explain": "Breakout +Vol:20+MTF:10"
  }
}
```

### Example 5: Multi-TF Confluence (GBPJPY)
```json
{
  "user_uuid": "test-user-12345",
  "symbol": "GBPJPY",
  "timeframe": "15",
  "strategy": "MultiTF",
  "regime": "Trending",
  "structure": "MultiTF",
  "side": "buy",
  "price": 189.50,
  "sl": 189.20,
  "tp": 190.20,
  "confidence": 85,
  "extra": {
    "session": "London",
    "multi_tf": {"240":"bull","60":"bull"},
    "explain": "MultiTF +HTF:15+HTF2:15+Trend:10+ADX:10"
  }
}
```

---

## 🔧 Testing Webhooks

### Method 1: RequestBin (Quick Test)
1. Go to https://requestbin.com/
2. Click "Create a RequestBin"
3. Copy the URL (e.g., `https://requestbin.com/r/abc123`)
4. Use as webhook URL in TradingView alert
5. View received webhooks in RequestBin dashboard

### Method 2: cURL Command (Test ZenithEdge Endpoint)
```bash
curl -X POST https://your-zenithedge-domain.com/signals/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_uuid": "test-user-12345",
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
      "explain": "SMC base +OB:12+FVG:10"
    }
  }'
```

### Method 3: Python Test Script
```python
import requests
import json

webhook_url = "https://your-zenithedge-domain.com/signals/webhook/"

payload = {
    "user_uuid": "test-user-12345",
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
        "multi_tf": {"4H": "bull", "1H": "bull"},
        "explain": "SMC base +OB:12+FVG:10"
    }
}

response = requests.post(webhook_url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

---

## 📊 Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `user_uuid` | string | ZenithEdge user identifier | "abc-123-def" |
| `symbol` | string | Trading instrument | "EURUSD" |
| `timeframe` | string | Chart timeframe (minutes) | "15" (15m), "60" (1H), "240" (4H) |
| `strategy` | string | Detected strategy name | "SMC", "ICT", "Trend", etc. |
| `regime` | string | Market regime | "Trending", "Ranging", "Volatile", "Consolidation" |
| `structure` | string | Setup structure | "CHOCH/OB/FVG", "Breakout", "Scalp" |
| `side` | string | Trade direction | "buy" or "sell" |
| `price` | float | Entry price | 1.0850 |
| `sl` | float | Stop Loss level | 1.0820 |
| `tp` | float | Take Profit level | 1.0910 |
| `confidence` | float | Signal confidence (0-100) | 78.5 |
| `extra.session` | string | Trading session | "London", "NY", "Other" |
| `extra.multi_tf` | object | Higher timeframe trends | {"4H":"bull","1H":"bull"} |
| `extra.explain` | string | Confidence breakdown | "SMC base +OB:12+FVG:10..." |

---

## 🚨 Alert Creation Steps (Detailed)

### Step 1: Add Indicator
1. Open TradingView chart
2. Click "Indicators" button (top menu)
3. Search for "ZenithEdge Pro"
4. Click to add to chart

### Step 2: Configure Indicator
1. Click gear icon on indicator name
2. Set **USER_UUID** to your ZenithEdge user ID
3. Adjust `min_confidence_alert` (recommended: 35-40)
4. Set `mode` to "All" or specific strategy
5. Click "OK"

### Step 3: Create Alert
1. Click clock icon (Alerts) or press `Alt+A`
2. **Condition:** Select "ZenithEdge Pro — Multi-Strategy + SMC/ICT (Pro)"
3. Select **"ZenithEdge PRO Signal (static)"** from dropdown
4. **Alert Name:** "ZenithEdge Multi-Strategy - {{ticker}} {{interval}}"
5. **Message:** Paste JSON template from above
6. **Webhook URL:** `https://your-domain.com/signals/webhook/`

### Step 4: Configure Options
- [x] **Once Per Bar Close** (recommended)
- [ ] Once Per Bar (can fire mid-bar, may repaint)
- [ ] Only Once (alert expires after first trigger)

### Step 5: Notifications (Optional)
- [ ] Notify on App
- [ ] Show Popup
- [ ] Send Email
- [x] **Webhook URL** (primary method)
- [ ] Play Sound

### Step 6: Expiration
- **Open-ended** (alert never expires)
- Or set custom date

### Step 7: Save
Click "Create" to activate alert

---

## 🔍 Debugging Webhooks

### Check 1: Verify JSON Syntax
Use https://jsonlint.com/ to validate JSON structure

### Check 2: Enable Debug Mode
```pine
show_debug = true  // Shows JSON label on chart
```

### Check 3: Check ZenithEdge Logs
```bash
# In terminal
cd ~/zenithedge_trading_hub
python3 manage.py shell

# In Django shell
from signals.models import Signal
recent_signals = Signal.objects.all().order_by('-created_at')[:5]
for sig in recent_signals:
    print(f"{sig.symbol} | {sig.strategy} | {sig.confidence} | {sig.created_at}")
```

### Check 4: Test Webhook Endpoint
```bash
# Simple connectivity test
curl -I https://your-zenithedge-domain.com/signals/webhook/

# Should return: HTTP/1.1 200 OK or 405 Method Not Allowed (normal for GET)
```

---

## ⚠️ Common Issues

### Issue 1: "Webhook URL is invalid"
**Solution:** Ensure URL starts with `https://` (not `http://`)

### Issue 2: "Alert not firing"
**Possible causes:**
- `min_confidence_alert` too high → Lower to 30
- No valid setups on chart → Test on different instrument
- Timeframe mismatch (Scalp requires 1m/5m)

### Issue 3: "JSON parsing error on ZenithEdge"
**Solution:** Check TradingView message template syntax:
- All strings must use double quotes `"`
- Numbers don't need quotes
- Use `{{close}}` not `"{{close}}"` for numbers

### Issue 4: "Multiple alerts firing per bar"
**Solution:** Ensure alert is set to **"Once Per Bar Close"** not "Once Per Bar"

---

## 📈 Expected Webhook Frequency

| Timeframe | Avg. Alerts/Day (All Strategies) |
|-----------|----------------------------------|
| 1m | 50-150 (mostly Scalp) |
| 5m | 20-60 (Scalp + Mean Rev) |
| 15m | 8-25 (mixed) |
| 1H | 3-10 (Trend + Multi-TF) |
| 4H | 1-4 (Trend + SMC) |
| Daily | 0-2 (Trend only) |

*Frequency varies by instrument volatility and mode setting*

---

## 🎯 Production Checklist

Before going live with webhook alerts:

- [ ] `user_uuid` set correctly
- [ ] Webhook URL points to production ZenithEdge
- [ ] `show_debug = false` (reduce chart clutter)
- [ ] `min_confidence_alert` calibrated (30-50 range)
- [ ] Alert frequency: "Once Per Bar Close"
- [ ] Tested on 3+ instruments
- [ ] Verified signals appear in ZenithEdge dashboard
- [ ] Paper traded for 1+ week
- [ ] Risk management rules defined

---

## 📞 Support

If webhooks aren't working:
1. Test with RequestBin first (isolate TradingView vs ZenithEdge issue)
2. Check ZenithEdge server logs for errors
3. Verify `user_uuid` matches your account
4. Ensure firewall allows incoming webhooks
5. Test with cURL command above

---

**Ready to receive live signals! 🎉**
