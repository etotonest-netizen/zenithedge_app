# ZenBot AI Trade Score Predictor

## Overview
The AI Trade Score Predictor is an in-house, explainable scoring engine that evaluates trading signals with a 0-100 score. Unlike black-box machine learning models, this system uses transparent rule-based logic with weighted factors, making every score fully explainable.

## Features
- ✅ **Auto-Scoring**: New signals are automatically scored on creation
- 🎯 **Explainable AI**: Every score comes with a detailed breakdown
- ⚙️ **Configurable Weights**: Adjust factor importance via versioned configurations
- 📊 **Dashboard Integration**: View scores, badges, and key factors in the signal list
- 🤖 **ZenBot Commands**: Query scores conversationally via chatbot
- 🔄 **Self-Learning**: Optimize weights based on recent trading performance
- 📈 **Management Commands**: Bulk rescore and weight optimization tools

## Scoring Factors (Default Weights)

| Factor | Weight | Description |
|--------|--------|-------------|
| **Signal Confidence** | 32% | Pine script confidence level (0-100) |
| **ATR Safety** | 18% | Stop loss positioning vs volatility |
| **Strategy Bias** | 16% | Historical strategy performance |
| **Regime Fit** | 18% | Strategy-regime alignment |
| **Rolling Win Rate** | 16% | Recent success rate for similar signals |

**Total**: 100% (weights sum to 1.0)

## Score Ranges

| Score | Badge | Color | Interpretation |
|-------|-------|-------|----------------|
| **80-100** | ✅ Excellent | Green | High probability setup |
| **50-79** | 🟡 Medium | Yellow | Acceptable with caution |
| **0-49** | 🚫 Risky | Red | Avoid or reduce position size |

## Dashboard Features

### AI Score Column
- **Badge**: Color-coded score with emoji indicator
- **Label**: Excellent/Medium/Risky classification
- **Key Factors**: Standout factors (e.g., "High Confidence", "ATR Safe", "Trend Fit")

### Min Score Filter
- **Slider**: Filter signals by minimum AI score (0-100)
- **Real-time Update**: Value updates as you drag the slider
- **Persistent**: Filter persists in URL query params

## ZenBot Commands

### `/score <signal_id>`
Get friendly, human-readable score explanation.

**Example:**
```
/score 17
```

**Response:**
```
🟡 Signal #17 AI Score: 73/100 (Medium)

EURUSD BUY @ $1.0850
Strategy: Trend Following | Regime: Trending

Score Breakdown:
• Signal Confidence: 85/100 → +27 pts
• ATR Safety: 0.28% SL distance → +1 pts
• Strategy Bias: Trend Following → +11 pts
• Regime Fit: Trend Following × Trending → +17 pts
• Rolling Win Rate: 100% → +16 pts

✨ Standout Factors: High Confidence (85%), Trending Fit, WinRate 100%

_Scored with engine v1.0-default_
```

### `/score-why <signal_id>`
Get technical JSON breakdown for debugging.

**Example:**
```
/score-why 17
```

**Response:**
```json
{
  "signal_id": 17,
  "ai_score": 73,
  "version": "v1.0-default",
  "factors": {
    "confidence": 0.85,
    "atr_safety": 0.07,
    "strategy_bias": 0.70,
    "regime_fit": 0.95,
    "rolling_win_rate": 1.0
  },
  "breakdown": [
    {
      "factor": "Signal Confidence",
      "raw_value": "85/100",
      "normalized": 0.85,
      "weight": 0.32,
      "contribution": 0.272,
      "explanation": "Pine script confidence level"
    },
    ...
  ]
}
```

### `/score-weights`
Show current scoring weights configuration.

**Example:**
```
/score-weights
```

**Response:**
```
⚙️ Active Scoring Weights (v1.0-default)

• Signal Confidence: 32.00%
• Atr Safety: 18.00%
• Strategy Bias: 16.00%
• Regime Fit: 18.00%
• Rolling Win Rate: 16.00%

🎯 Minimum Score Threshold: 60

📝 Notes: Default scoring weights with balanced factor importance

_Last updated: 2025-11-09 11:26_
```

### `/score-optimize` (Admin Only)
Run weight optimization based on recent performance.

**Example:**
```
/score-optimize
```

**Response:**
```
✅ Scoring weights optimized!

Analyzed: 47 signals
Win Rate: 68.1%

Weight Changes:
📈 signal_confidence: 32.00% → 35.20%
📉 atr_safety: 18.00% → 15.80%
➡️ strategy_bias: 16.00% → 16.00%
📈 regime_fit: 18.00% → 19.50%
📉 rolling_win_rate: 16.00% → 13.50%

_New version: v20251109-1456_
```

## Management Commands

### `zenbot_recompute_scores`
Recompute AI scores for existing signals.

**Usage:**
```bash
# Rescore only unscored signals (default)
python manage.py zenbot_recompute_scores

# Rescore all signals
python manage.py zenbot_recompute_scores --all

# Rescore signals since specific date
python manage.py zenbot_recompute_scores --since-date 2024-01-01

# Rescore signals with ID >= 100
python manage.py zenbot_recompute_scores --min-id 100

# Dry run (preview without changes)
python manage.py zenbot_recompute_scores --all --dry-run
```

**Example Output:**
```
Found 15 signals to rescore

Using weights: v1.0-default

Rescoring signals...

✅ Successfully rescored 15/15 signals
   Version: v1.0-default
```

### `zenbot_optimize_scoring`
Optimize scoring weights based on recent performance.

**Usage:**
```bash
# Optimize using last 30 days (default)
python manage.py zenbot_optimize_scoring

# Custom lookback window
python manage.py zenbot_optimize_scoring --window-days 60

# Adjust learning rate (0-1, default: 0.1)
python manage.py zenbot_optimize_scoring --learning-rate 0.15

# Dry run (preview without applying)
python manage.py zenbot_optimize_scoring --dry-run
```

**Example Output:**
```
🔬 Analyzing last 30 days of trading performance...

✅ Analysis complete: 47 signals, 68.1% win rate

📊 Factor Correlations:
   📈 confidence_factor: +0.1250
   📉 atr_safety_factor: -0.0320
   ➡️ strategy_bias_factor: +0.0010
   📈 regime_fit_factor: +0.0850
   📉 rolling_win_rate: -0.0450

⚖️ Proposed Weight Changes:
   📈 signal_confidence: 32.00% → 35.20% (+3.20%)
   📉 atr_safety: 18.00% → 15.80% (-2.20%)
   ➡️ strategy_bias: 16.00% → 16.00% (+0.00%)
   📈 regime_fit: 18.00% → 19.50% (+1.50%)
   📉 rolling_win_rate: 16.00% → 13.50% (-2.50%)

 Apply these weights? [y/N]: y

✅ New weights activated: v20251109-1456
   Future signals will be scored with the updated weights.
   Run 'zenbot_recompute_scores --all' to rescore existing signals.
```

## Database Models

### `ScoringWeights`
Versioned configuration for scoring factor weights.

**Fields:**
- `version` (str, unique): Version identifier (e.g., "v1.0-default", "v20251109-1456")
- `weights` (JSON): Dict of factor weights (keys: signal_confidence, atr_safety, strategy_bias, regime_fit, rolling_win_rate)
- `min_score_threshold` (int, 0-100): Minimum acceptable score (default: 60)
- `is_active` (bool): Only one version can be active (singleton pattern)
- `notes` (text): Description of weight changes
- `created_at`, `updated_at`: Timestamps

**Methods:**
- `get_active_weights()` (class method): Returns active version or creates default
- `save()`: Ensures only one active version (deactivates others)

### `TradeScore`
AI score for a trading signal with detailed breakdown.

**Fields:**
- `signal` (OneToOne FK): Related signal (primary key)
- `ai_score` (int, 0-100, indexed): Final computed score
- `score_breakdown` (JSON): List of factor dicts with raw_value, weight, contribution, explanation
- `version` (str): ScoringWeights version used
- `confidence_factor`, `atr_safety_factor`, `strategy_bias_factor`, `regime_fit_factor`, `rolling_win_rate` (float, 0-1): Cached normalized factors for filtering
- `created_at`: Timestamp

**Methods:**
- `get_score_badge()`: Returns dict with color, icon, label (for UI display)
- `get_key_factors()`: Returns list of standout factors (e.g., ["High Confidence (85%)", "ATR Safe"])
- `get_explanation_text()`: Generates human-readable explanation

## Scoring Algorithm

### 1. Feature Extraction (`extract_features`)
```python
features = {
    'signal_confidence': 85,  # From Pine script (0-100)
    'sl_pct': 0.28,  # SL distance as % of price
    'atr_percentile': 0.3,  # 0-1 (lower = tighter stop)
    'strategy_type': 'Trend Following',
    'regime_type': 'Trending',
    'session_type': 'London',
    'symbol': 'EURUSD',
    'timeframe': '1H'
}
```

### 2. Factorization (`factorize`)
Normalize raw features to 0-1 scale:

```python
factors = {
    'conf_norm': 0.85,  # confidence / 100
    'atr_safety': 0.70,  # 1 - atr_percentile
    'strategy_bias': 0.70,  # Lookup: STRATEGY_BIAS['Trend Following']
    'regime_fit': 0.95,  # Lookup: REGIME_FIT['Trend Following']['Trending']
    'rolling_win_rate': 1.0  # Recent win rate for Trend Following on EURUSD
}
```

### 3. Weighted Sum (`score_signal`)
Compute final score:

```python
score = (
    0.32 * 0.85 +  # Confidence
    0.18 * 0.70 +  # ATR Safety
    0.16 * 0.70 +  # Strategy Bias
    0.18 * 0.95 +  # Regime Fit
    0.16 * 1.00    # Rolling Win Rate
) * 100 = 73
```

### 4. Breakdown Generation
Each factor contribution:
```python
breakdown = [
    {
        'factor': 'Signal Confidence',
        'raw_value': '85/100',
        'normalized': 0.85,
        'weight': 0.32,
        'contribution': 0.272,  # 0.85 * 0.32
        'explanation': 'Pine script confidence level'
    },
    # ... 4 more factors
]
```

## Strategy & Regime Lookup Tables

### Strategy Bias
Historical baseline performance for each strategy type:

| Strategy | Bias Score |
|----------|------------|
| Trend Following | 0.70 |
| Breakout | 0.65 |
| Mean Reversion | 0.55 |
| Range Trading | 0.55 |
| Squeeze | 0.50 |

### Regime Fit Matrix
Strategy-regime alignment scores (sample):

|  | Trend | Breakout | Mean Reversion | Squeeze |
|---|---|---|---|---|
| **Trend Following** | 0.95 | 0.70 | 0.30 | 0.40 |
| **Breakout** | 0.75 | 0.95 | 0.35 | 0.80 |
| **Mean Reversion** | 0.25 | 0.35 | 0.90 | 0.60 |
| **Range Trading** | 0.30 | 0.40 | 0.85 | 0.55 |

## Weight Optimization Algorithm

### Correlation Analysis
For each factor, compare average normalized value for winning vs losing trades:

```python
avg_green = winning_trades.aggregate(avg=Avg('ai_score__confidence_factor'))['avg']
avg_red = losing_trades.aggregate(avg=Avg('ai_score__confidence_factor'))['avg']
correlation = avg_green - avg_red  # Positive = predictive of success
```

### Weight Adjustment
Nudge weights based on correlations:

```python
adjustment = correlation * learning_rate  # e.g., 0.125 * 0.1 = 0.0125
new_weight = max(0.05, min(0.50, old_weight + adjustment))  # Clamp to bounds
```

### Normalization
Ensure weights sum to 1.0:

```python
total = sum(new_weights.values())
new_weights = {k: v/total for k, v in new_weights.items()}
```

## Auto-Scoring Integration

Signals are automatically scored on creation via Django signal handler:

```python
@receiver(post_save, sender=Signal)
def auto_score_signal(sender, instance, created, **kwargs):
    if created:
        try:
            from bot.score_engine import score_signal
            score_signal(instance)
        except Exception as e:
            logger.error(f"Failed to auto-score signal {instance.id}: {e}")
```

**Note**: For production with high-volume webhooks, consider moving to Celery task:
```python
@shared_task
def async_score_signal(signal_id):
    signal = Signal.objects.get(id=signal_id)
    score_signal(signal)
```

## API Reference

### `bot/score_engine.py`

#### `TradeScorer(weights=None)`
Main scoring engine class.

**Methods:**
- `extract_features(signal)`: Extract raw features from signal
- `factorize(features, signal=None)`: Normalize features to 0-1
- `score_signal(signal)`: Compute final score and breakdown
- `_compute_rolling_win_rate(signal, strategy, symbol, timeframe, window_days=30)`: Calculate recent win rate

#### `score_signal(signal)`
Convenience function to score a signal and save TradeScore to DB.

**Args:**
- `signal`: Signal model instance

**Returns:**
- `TradeScore` instance (saved)

#### `bulk_rescore_signals(signal_queryset)`
Rescore multiple signals efficiently.

**Args:**
- `signal_queryset`: QuerySet of Signal objects

**Returns:**
- Dict with `total`, `scored`, `version`

#### `update_weights_from_journal(window_days=30, learning_rate=0.1)`
Analyze recent performance and propose new weights.

**Args:**
- `window_days`: Lookback period for analysis
- `learning_rate`: Adjustment magnitude (0-1, typically 0.05-0.2)

**Returns:**
- Dict with `status`, `old_weights`, `new_weights`, `correlations`, `analyzed_signals`, `win_rate`

## Testing

### Create Test Signal
```python
from signals.models import Signal
from accounts.models import CustomUser

user = CustomUser.objects.get(email='admin@zenithedge.com')

signal = Signal.objects.create(
    user=user,
    symbol='EURUSD',
    timeframe='1H',
    side='buy',
    price=1.0850,
    sl=1.0820,
    tp=1.0920,
    confidence=85,
    strategy='Trend Following',
    regime='Trending',
    session='London'
)

# Check auto-scoring
print(f"Score: {signal.ai_score.ai_score}/100")
print(f"Badge: {signal.ai_score.get_score_badge()}")
print(f"Key Factors: {signal.ai_score.get_key_factors()}")
```

### Test ZenBot Commands
```python
from bot.logic import ZenBotEngine

bot = ZenBotEngine(user=user)
result = bot.process_query('/score 17', session_id='test-123')
print(result['response'])
```

### Test Management Commands
```bash
# Dry run rescore
python manage.py zenbot_recompute_scores --all --dry-run

# Dry run optimize
python manage.py zenbot_optimize_scoring --dry-run
```

## Performance Considerations

### Scoring Performance
- **Auto-scoring**: ~50-100ms per signal (synchronous)
- **Bulk rescoring**: ~5-10 signals/second
- **Database impact**: Minimal (simple queries with indexes)

### Optimization
- ✅ Indexes on `ai_score`, `version`, `created_at`
- ✅ Cached factor fields for fast filtering
- ✅ OneToOne relationship (no N+1 queries)
- ⚠️ For high-volume webhooks (>10/sec), use Celery async tasks

### Scalability
- **Database**: SQLite OK for <100k signals, PostgreSQL recommended for production
- **Caching**: Consider caching ScoringWeights.get_active_weights() with Redis
- **Async**: Move to Celery for webhook volumes >100/min

## Future Enhancements

### Phase 2 (Planned)
- [ ] Real-time ATR calculation (currently using SL distance proxy)
- [ ] Session-specific win rate analysis
- [ ] Timeframe-specific factor weights
- [ ] Symbol-specific bias scores
- [ ] Multi-strategy ensemble scoring

### Phase 3 (Advanced)
- [ ] Bayesian weight optimization
- [ ] A/B testing framework for weight versions
- [ ] ML-assisted factor engineering (while maintaining explainability)
- [ ] Real-time score updates on signal outcome changes
- [ ] Score prediction API for pre-webhook validation

## Troubleshooting

### "No score found for signal"
**Cause**: Signal created before auto-scoring was implemented.  
**Fix**: Run `python manage.py zenbot_recompute_scores --all`

### "AttributeError: 'Signal' object has no attribute 'ai_score'"
**Cause**: OneToOne relationship not loaded.  
**Fix**: Use `Signal.objects.select_related('ai_score')` or check `hasattr(signal, 'ai_score')`

### Scores seem inaccurate
**Cause**: Weights may not align with current market conditions.  
**Fix**: Run `python manage.py zenbot_optimize_scoring` with sufficient historical data (30+ completed signals)

### Auto-scoring not working
**Cause**: Signal handler not triggered or error in score_engine.py.  
**Check**: Django logs for errors, verify `post_save` signal is registered

## Credits
- **Design**: In-house explainable AI approach (no external ML dependencies)
- **Implementation**: ZenithEdge development team
- **Inspiration**: Prop trading challenge scoring systems, transparency-first AI

## License
Proprietary - ZenithEdge Platform

---

**Last Updated**: November 2024  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
