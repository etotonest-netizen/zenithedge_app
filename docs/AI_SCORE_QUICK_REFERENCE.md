# AI Trade Score - Quick Reference

## 🎯 What is AI Trade Score?

Every trading signal gets an AI score from **0-100** that tells you how good the setup is:

- ✅ **80-100 (Excellent)**: High-probability setup, full confidence
- 🟡 **50-79 (Medium)**: Acceptable trade, use caution
- 🚫 **0-49 (Risky)**: Avoid or reduce position size

---

## 📊 Score Factors (What Goes Into It)

| Factor | Weight | What It Means |
|--------|--------|---------------|
| **Signal Confidence** | 32% | Pine script confidence (0-100) |
| **ATR Safety** | 18% | How tight is your stop loss? |
| **Strategy Bias** | 16% | Does this strategy usually win? |
| **Regime Fit** | 18% | Does strategy match market regime? |
| **Rolling Win Rate** | 16% | Recent success on this pair/strategy |

---

## 💬 Ask ZenBot About Scores

### Get a friendly explanation:
```
/score 17
```
**Response**: Full breakdown with emoji, points, and key factors

### Get technical details (for nerds):
```
/score-why 17
```
**Response**: JSON with raw factors and calculations

### Check current weights:
```
/score-weights
```
**Response**: Active weight configuration

### Optimize weights (admin only):
```
/score-optimize
```
**Response**: Analyzes recent trades and adjusts weights

---

## 🎛️ Dashboard Features

### AI Score Column
- **Color Badge**: Green (Excellent) / Yellow (Medium) / Red (Risky)
- **Emoji**: ✅ / 🟡 / 🚫
- **Key Factors**: Pills showing standout strengths (e.g., "High Confidence", "ATR Safe")

### Min Score Filter
- **Slider**: Set minimum acceptable score (0-100)
- **Use Case**: Filter out low-quality signals

**Example**: Set slider to 70 → Only show Medium+ and Excellent signals

---

## 🔧 Management Commands (For Admins)

### Rescore all signals:
```bash
python manage.py zenbot_recompute_scores --all
```

### Rescore only recent signals:
```bash
python manage.py zenbot_recompute_scores --since-date 2024-01-01
```

### Optimize weights based on performance:
```bash
python manage.py zenbot_optimize_scoring
```

### Preview without applying:
```bash
python manage.py zenbot_recompute_scores --all --dry-run
python manage.py zenbot_optimize_scoring --dry-run
```

---

## 🧠 How It Works (Simple Version)

1. **New signal arrives** from TradingView
2. **AI analyzes 5 factors**:
   - Confidence from Pine script
   - Stop loss tightness (ATR)
   - Strategy historical performance
   - Does strategy fit current market regime?
   - Recent win rate on this pair
3. **Weights each factor** (32% + 18% + 16% + 18% + 16% = 100%)
4. **Computes final score** (0-100)
5. **Saves score with breakdown** (so you can see why)

**Example**:
- Confidence: 85/100 → +27 points
- ATR Safe: Tight SL → +12 points
- Strategy: Trend works → +11 points
- Regime: Trending market → +17 points
- Win Rate: 75% recent → +12 points
- **Total: 79/100 (Medium)** 🟡

---

## 📈 Interpreting Scores

### ✅ Excellent (80-100)
- **Action**: Trade with full confidence
- **Position Size**: Full size (per risk rules)
- **Rationale**: All factors align, high probability

### 🟡 Medium (50-79)
- **Action**: Trade with caution OR wait for confirmation
- **Position Size**: Reduce by 30-50% OR wait for better setup
- **Rationale**: Some factors align, acceptable risk-reward

### 🚫 Risky (0-49)
- **Action**: Avoid OR paper trade only
- **Position Size**: Minimal OR skip
- **Rationale**: Too many red flags, low probability

---

## 🎓 Tips for Using Scores

### DO:
- ✅ Use scores as **one input** in your decision (not the only input)
- ✅ Compare scores across similar signals (EURUSD Trend vs GBPUSD Trend)
- ✅ Track which score ranges work best for you
- ✅ Adjust weights if scores don't match your experience (admin only)

### DON'T:
- ❌ Blindly follow scores (always check chart yourself)
- ❌ Ignore low scores without reason (sometimes they're right)
- ❌ Expect 100% accuracy (it's AI-assisted, not AI-dictated)
- ❌ Change weights too frequently (let data accumulate first)

---

## 🔍 When Scores Might Be Wrong

1. **Not enough historical data** (new strategy/pair)
   - Rolling win rate will be 50% (neutral)
   - Wait for 20+ trades to stabilize

2. **Market conditions changed** (volatility spike, news event)
   - ATR Safety might be off
   - Use your judgment

3. **Weights not optimized** (default settings)
   - Run `/score-optimize` after 50+ trades
   - Weights will adapt to your trading style

4. **Pine script confidence misleading** (over/under confident)
   - Signal shows 95% but loses → lowers future scores
   - Self-corrects over time via weight optimization

---

## 📞 Need Help?

### Ask ZenBot:
```
How do I interpret AI scores?
What factors affect AI scores?
Why did my signal get a low score?
```

### Check Docs:
- Full Guide: `docs/AI_TRADE_SCORE_PREDICTOR.md`
- Implementation: `docs/AI_SCORE_IMPLEMENTATION_SUMMARY.md`

### Admin Support:
- Check logs: Django logs for scoring errors
- Test scoring: Create test signal and verify score
- Rescore: Use management commands to refresh scores

---

## 🚀 Pro Tips

### 1. Combine with Confidence
High AI Score + High Pine Confidence = 💪 Strong setup

### 2. Use Min Score Filter
Set your personal threshold (e.g., 65+) to see only quality signals

### 3. Watch Key Factors
Pay attention to standout factors like:
- "High Confidence (90%)"
- "ATR Safe"
- "Trend Fit"
- "WinRate 75%"

### 4. Optimize Regularly
Run `/score-optimize` monthly to keep weights aligned with your performance

### 5. Compare Across Sessions
London signals scoring higher? → Focus on London session

---

**Remember**: AI scores are a **tool**, not a crystal ball. Use them to **enhance** your decision-making, not replace it. Your experience + AI analysis = Best results! 🎯
