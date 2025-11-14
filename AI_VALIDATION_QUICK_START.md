# AI Validation System - Quick Start Guide

## 🚀 What's New

ZenithEdge now features **AI-powered signal validation** with a multi-dimensional Truth Filter. Every trading signal is automatically evaluated and presented with clear context and recommendations.

---

## 📊 Key Features

### 1. Truth Index Scoring (0-100)
Every signal receives a composite quality score based on 6 criteria:

- ✅ **85-100**: High Confidence - Proceed with standard risk
- ✅ **75-84**: Solid Quality - Good to trade
- ⚠️ **65-74**: Moderate - Watch closely
- ⚠️ **60-64**: Conditional - Requires confirmation
- ❌ **<60**: Rejected - Signal not published

### 2. AI-Generated Narratives
Each validated signal includes a 3-part insight:

**📌 Example:**
```
📊 EURUSD LONG setup detected — 83/100 high-confidence (SMC)

CHoCH and Fair Value Gap alignment showing strong directional bias 
during London session with supportive news sentiment. Strategy has 
strong historical performance (>60% win rate). Low volatility 
environment favors controlled risk.

✅ Long bias validated above 1.0850. Consider scaling out: partials 
near 1.0900, final target 1.0950. Risk ~1.2% (standard). Watch for 
liquidity sweeps and order block reactions.
```

### 3. Transparency & Breakdown
Click **"Explain AI"** on any signal to see:
- Technical Integrity: 90%
- Volatility Filter: 85%
- Regime Alignment: 80%
- Sentiment Coherence: 75%
- Historical Reliability: 85%
- Psychological Safety: 90%

---

## 🎯 How to Use

### Dashboard Features

#### 1. **Validation Filters**
At the top of the dashboard, you'll see 3 filter buttons:

- **All Signals**: See everything (approved + conditional)
- **Validated (≥80)**: High-confidence signals only
- **Conditional (60-80)**: Signals needing confirmation

#### 2. **Show/Hide Narratives**
Toggle the switch to show or hide AI-generated context summaries.

#### 3. **Signal Cards**
Each card now displays:
- **Truth Index Badge**: Color-coded score (green/yellow)
- **AI Insight Section**: Full contextual narrative
- **Explain AI Button**: Detailed breakdown

### Track Record Page

Access via **Sidebar → Analytics & Transparency → AI Track Record**

View comprehensive system performance:
- System Health Grade (A/B/C/D)
- Total validations and approval rates
- Monthly trends chart
- Strategy-specific performance table
- Validation criteria breakdown

---

## 🔍 Understanding Validation Criteria

### Technical Integrity (25% weight)
- Risk-Reward ratio validation (minimum 1:1)
- Confidence score check (prefer >70)
- Strategy coherence

**What to look for**: R:R ≥ 2:1 and confidence ≥ 75 = excellent technical setup

### Volatility Filter (15% weight)
- ATR analysis
- 20-signal rolling volatility
- Standard deviation checks

**What to look for**: Score >85% = stable market conditions, ideal for tight stops

### Regime Alignment (20% weight)
- Matching signal type to market structure
- Trending vs ranging detection
- Breakout vs consolidation

**What to look for**: "Strong directional bias" = trending regime matched to buy/sell signal

### Sentiment Coherence (15% weight)
- News event alignment (12-hour window)
- Bullish news + buy signal = high score
- Bearish news + sell signal = high score
- Conflicting sentiment = warning

**What to look for**: "Supportive news sentiment" = ≥85% coherence

### Historical Reliability (15% weight)
- Strategy performance tracking (min 10 trades)
- Win rate analysis
- Symbol-strategy combination stats

**What to look for**: "Strong historical performance (>60% win rate)" = proven strategy

### Psychological Safety (10% weight)
- Overtrading detection (4-hour frequency)
- Risk control violations
- Session rule compliance

**What to look for**: "Trading frequency within healthy limits" = no overtrading

---

## 🎨 Visual Indicators

### Badge Colors
- 🟢 **Green (Success)**: Approved, Truth Index ≥80
- 🟡 **Yellow (Warning)**: Conditional, Truth Index 60-79
- 🔴 **Red (Danger)**: Rejected, Truth Index <60

### Icons
- ✅ **Check**: Passed validation
- ⚠️ **Warning**: Conditional approval
- ❌ **Cross**: Rejected/failed

### Progress Bars
In the breakdown view, color-coded bars show:
- Green: ≥80% (excellent)
- Yellow: 60-79% (acceptable)
- Red: <60% (concerning)

---

## 💡 Best Practices

### For Signal Evaluation

1. **Check Truth Index First**
   - ≥85: High confidence, proceed
   - 75-84: Good quality, standard approach
   - 65-74: Moderate, reduce size
   - <65: Skip or await confirmation

2. **Read the AI Narrative**
   - Header gives quick overview
   - Reasoning explains market context
   - Suggestion provides actionable guidance

3. **Review Breakdown When Unsure**
   - Identify weak criteria (red bars)
   - If sentiment low but technical high, consider conflicting news
   - If psychological low, you may be overtrading

4. **Use Filters Strategically**
   - New traders: Use "Validated (≥80)" filter only
   - Experienced traders: Review "Conditional" signals with manual confirmation
   - Developers: Use "All Signals" to see full pipeline

### For Risk Management

**Truth Index-Based Position Sizing**:
- 85-100: Standard position size (1-2% risk)
- 75-84: Standard position size
- 65-74: Reduce to 0.5-1% risk
- 60-64: Micro positions (0.25% risk) or skip

**When to Override Conditional Signals**:
✅ You have additional confluence (price action, support/resistance)  
✅ You understand the specific weakness (e.g., low sentiment but you disagree)  
✅ You're an experienced trader with strong risk management  

❌ Never override if Technical Integrity <60%  
❌ Never override if multiple criteria are red  

---

## 📈 Track Record Interpretation

### System Health Grades

**Grade A (Excellent)**:
- Approval rate ≥70%
- Avg Truth Index ≥75
- System performing optimally

**Grade B (Good)**:
- Approval rate ≥60%
- Avg Truth Index ≥70
- System healthy

**Grade C (Fair)**:
- Approval rate ≥50%
- Avg Truth Index ≥65
- Review strategy mix

**Grade D (Needs Improvement)**:
- Approval rate <50%
- Avg Truth Index <65
- Contact support for analysis

### Monthly Trends

**Improving Trend** (approval rate increasing):
- System learning from outcomes
- Strategy mix optimizing
- Good sign for platform health

**Declining Trend** (approval rate decreasing):
- Market regime shift
- Strategy recalibration needed
- Review strategy-specific stats

---

## 🛠️ Troubleshooting

### "Why was my signal rejected?"

Check the rejection response in webhook logs:
```json
{
  "status": "rejected",
  "reason": "ai_validation_failed",
  "truth_index": 45.5,
  "validation_notes": [
    "❌ Technical Integrity: Poor (40%) - Low R:R ratio",
    "⚠ Volatility Filter: Fair (60%) - High recent volatility",
    "✓ Regime Alignment: Good (80%)",
    "❌ Sentiment Coherence: Poor (30%) - Conflicting news",
    "N/A Historical Reliability: Insufficient data",
    "✓ Psychological Safety: Good (85%)"
  ]
}
```

**Common Causes**:
1. **Low R:R ratio**: TP too close to entry, SL too far
2. **Low confidence**: Signal confidence <50
3. **Conflicting sentiment**: Buy signal with bearish news
4. **High volatility**: Market too unstable for this setup
5. **Overtrading**: Too many signals in short period

### "Narrative section not showing"

1. Ensure you're viewing validated signals (check Truth Index badge)
2. Toggle "Show AI Narratives" switch ON
3. Refresh the page
4. If still missing, signal may have been created before AI validation was enabled

### "Track Record page is empty"

- Wait for signals to accumulate (need at least 1 validation)
- Check date filter: increase `?months=12` in URL
- New accounts won't have historical data yet

---

## 🔄 Webhook Integration

### Testing the AI Validation

Send a test webhook with high-quality parameters:

```bash
curl -X POST http://127.0.0.1:8000/api/signals/api/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0750,
    "tp": 1.0950,
    "confidence": 85.0,
    "strategy": "smc",
    "regime": "Trend",
    "price": 1.0800
  }'
```

**Expected Response**:
```json
{
  "status": "received",
  "signal_id": 123,
  "allowed": true,
  "reason": null,
  "ai_validation": {
    "truth_index": 83.5,
    "status": "approved",
    "quality_label": "High Confidence",
    "context_summary": "📊 EURUSD LONG setup detected — 83/100..."
  }
}
```

### TradingView Alert Setup

No changes needed! Your existing TradingView alerts continue to work. The AI validation happens automatically in the background.

---

## 📚 Additional Resources

- **Full Implementation Doc**: `/AI_VALIDATION_IMPLEMENTATION.md`
- **System Architecture**: See implementation doc section "System Architecture"
- **API Documentation**: See implementation doc section "Webhook Pipeline Integration"
- **Support**: Contact admin dashboard or support ticket system

---

## 🎓 Learning Path

### Week 1: Familiarization
- Review 20-30 validated signals
- Read AI narratives carefully
- Click "Explain AI" on diverse signals
- Understand what makes Truth Index high/low

### Week 2: Pattern Recognition
- Compare high-confidence (≥85) vs moderate (65-74) signals
- Identify common traits in rejected signals
- Notice strategy-specific patterns (SMC vs ICT)
- Observe session timing impact

### Week 3: Application
- Start using "Validated (≥80)" filter only
- Take trades based on AI recommendations
- Track your outcomes vs Truth Index
- Provide feedback for improvement

---

## ✅ Quick Checklist

Before taking any trade:

- [ ] Truth Index ≥75 (minimum)
- [ ] AI narrative reviewed (all 3 parts)
- [ ] No red flags in breakdown (all criteria >60%)
- [ ] R:R ratio ≥1.5:1
- [ ] Risk percentage matches Truth Index (higher = standard, lower = reduced)
- [ ] Conflicting sentiment addressed (if present)
- [ ] Session timing favorable (London/NY preferred)

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Maintained By**: ZenithEdge Development Team

For questions or feedback, visit the AI Track Record page and review the System Insights section.
