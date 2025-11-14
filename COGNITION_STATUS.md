# 🧠 Cognition Module - Context-Aware Trading Intelligence

## ✅ Core System Built and Operational

The **Cognition** module adds psychological intelligence, market awareness, and adaptive learning to ZenithEdge. The system now understands traders, market conditions, and makes context-aware decisions.

---

## 📊 What's Been Implemented

### 1. **Database Models** (5 Models Created)

#### ✅ TraderPsychology
- Analyzes trader emotional state from journal entries, chat, feedback
- Tracks sentiment (-1 to +1), confidence (0-1), emotional tone
- Detects cognitive biases (overconfidence, revenge trading, FOMO, etc.)
- Measures risk tolerance, patience, discipline
- Generates psychological_bias_score for AI adjustment

#### ✅ MarketRegime  
- Classifies market state: strong_trend, weak_trend, choppy, squeeze, volatile, quiet
- Calculates trend strength (ADX-based), volatility percentile, volume profile
- Detects patterns (higher_highs, lower_lows, range_bound, squeeze)
- Provides regime_bias_score for trading appropriateness

#### ✅ SignalCluster
- Groups similar trading signals using ML clustering
- Tracks performance by cluster (win_rate, profit_factor, sharpe_ratio)
- Calculates reliability_score for each cluster
- Identifies preferred market regimes per cluster

#### ✅ PropFirmPrediction
- Predicts probability of passing prop firm challenges
- Estimates completion days and risk of failure
- Generates actionable recommendations
- Integrates psychological and performance metrics

#### ✅ CognitionInsight
- Stores generated insights and alerts
- Types: daily_summary, psychology_alert, regime_change, cluster_insight, prop_warning
- Severity levels with actionable flags

---

### 2. **NLP Psychology Analyzer** (psychology_analyzer.py)

**Libraries**: spaCy, TextBlob, VADER, NLTK

**Capabilities**:
- ✅ Sentiment analysis (VADER + TextBlob + keyword fallback)
- ✅ Confidence level detection (0-1 scale)
- ✅ Emotional tone classification (fearful, anxious, confident, overconfident, greedy, disciplined, neutral)
- ✅ Entity extraction (trading symbols, strategies, indicators)
- ✅ Key phrase extraction from trader text
- ✅ Cognitive bias detection:
  - Overconfidence bias
  - Revenge trading patterns
  - FOMO (Fear of Missing Out)
  - Anchoring bias
  - Confirmation bias
  - Recency bias
- ✅ Risk tolerance assessment
- ✅ Patience scoring
- ✅ Discipline measurement

**Usage**:
```python
from cognition.utils import analyze_trader_text

result = analyze_trader_text("I'm confident this setup will work. Easy money!")
print(result['emotional_tone'])  # 'overconfident'
print(result['detected_biases'])  # ['overconfidence']
print(result['sentiment_score'])  # 0.65
```

---

### 3. **Market Regime Detector** (regime_detector.py)

**Libraries**: pandas, scikit-learn, numpy

**Capabilities**:
- ✅ Technical indicator calculation:
  - Trend strength (ADX-based)
  - Average True Range (ATR)
  - Bollinger Band width
  - Volume analysis
  - Trend consistency metrics
- ✅ Pattern detection (higher_highs, lower_lows, range_bound, squeeze)
- ✅ Regime classification with confidence scores
- ✅ Regime bias calculation (-1 avoid, +1 favorable)

**Regime Types**:
1. **strong_trend** - High ADX, consistent direction (+0.8 bias)
2. **weak_trend** - Moderate trend (+0.4 bias)
3. **choppy** - Range-bound, no clear direction (-0.5 bias - AVOID)
4. **squeeze** - Low volatility consolidation (+0.2 bias - breakout opportunity)
5. **volatile** - High volatility spikes (-0.3 to +0.1 bias depending on extremeness)
6. **quiet** - Low volatility (-0.2 bias)

**Usage**:
```python
import pandas as pd
from cognition.utils import detect_market_regime

# ohlc_data = DataFrame with open, high, low, close, volume columns
regime = detect_market_regime(ohlc_data)
print(regime['regime_type'])  # 'strong_trend'
print(regime['regime_bias'])  # 0.75
```

---

### 4. **Signal Clusterer** (signal_clusterer.py)

**Libraries**: scikit-learn (KMeans), pandas

**Capabilities**:
- ✅ Automatic signal grouping using K-Means clustering
- ✅ Feature extraction from signals (time, performance, strategy, market conditions)
- ✅ Performance metrics per cluster
- ✅ Reliability scoring (0-1 scale)
- ✅ Cluster prediction for new signals
- ✅ Silhouette score for cluster quality

**Usage**:
```python
from cognition.utils import cluster_signals

signals_data = [
    {'timestamp': '2025-11-10 14:00', 'strategy': 'breakout', 'outcome': 'win', ...},
    # ... more signals
]

result = cluster_signals(signals_data, n_clusters=5)
for cluster in result['cluster_metrics']:
    print(f"Cluster {cluster['cluster_id']}: {cluster['win_rate']:.1%} win rate")
    print(f"Reliability: {cluster['reliability_score']:.2f}")
```

---

### 5. **Prop Firm Predictor** (prop_predictor.py)

**Libraries**: scikit-learn, numpy

**Capabilities**:
- ✅ Pass probability calculation (rule-based heuristics)
- ✅ Failure risk assessment
- ✅ Completion days estimation
- ✅ Actionable recommendations generation
- ✅ Integration with psychological metrics

**Predictions**:
- Pass probability (0-1)
- Estimated days to target
- Risk of hitting max drawdown
- 5 specific recommendations for improvement

**Usage**:
```python
from cognition.utils import predict_challenge_success

metrics = {
    'challenge_type': 'phase1',
    'account_size': 100000,
    'profit_target': 10000,
    'max_drawdown': 5000,
    'current_profit': 3500,
    'current_drawdown': 1200,
    'days_remaining': 20,
    'current_win_rate': 0.58,
    'current_profit_factor': 1.4,
    'avg_discipline_score': 0.7,
}

prediction = predict_challenge_success(metrics)
print(f"Pass probability: {prediction['pass_probability']:.1%}")
print(f"Estimated completion: {prediction['estimated_completion_days']} days")
print("Recommendations:")
for rec in prediction['recommended_adjustments']:
    print(f"  - {rec}")
```

---

## 🔗 System Integration Points

### ZenBot AI Scoring Integration (Planned)

The cognition module provides three bias adjustments for `bot/ai_score.py`:

```python
# In bot/ai_score.py - integrate_cognition_bias()

# 1. Psychological Bias (-1 to +1)
psychological_bias = TraderPsychology.get_latest().get_psychological_bias_score()
# Penalizes overconfidence, rewards discipline

# 2. Regime Bias (-1 to +1)  
regime_bias = MarketRegime.get_latest(symbol).get_regime_bias_score()
# Reduces score in choppy markets, boosts in trends

# 3. Cluster Reliability (0 to 1)
cluster_reliability = SignalCluster.get_for_signal(signal).get_cluster_reliability_score()
# Adjusts based on historical cluster performance

# Final adjustment
cognition_adjustment = (
    psychological_bias * 0.3 +  # 30% weight
    regime_bias * 0.4 +          # 40% weight  
    cluster_reliability * 0.3    # 30% weight
) * 10  # Scale to ±10 points

adjusted_score = base_score + cognition_adjustment
```

---

## 📈 Database Status

✅ **Migrations Created**: `cognition/migrations/0001_initial.py`  
✅ **Migrations Applied**: All 5 models created in database  
✅ **Tables Created**:
- `cognition_traderpsychology`
- `cognition_marketregime`
- `cognition_signalcluster`
- `cognition_propfirmprediction`
- `cognition_cognitioninsight`

---

## 🛠️ What's Ready to Use

### Immediate Capabilities:

1. **Analyze Trader Text**:
   ```bash
   python3 manage.py shell
   >>> from cognition.utils import analyze_trader_text
   >>> analyze_trader_text("Feeling confident about today's trades!")
   ```

2. **Detect Market Regime**:
   ```python
   # From your OHLC data
   from cognition.utils import detect_market_regime
   regime = detect_market_regime(df)
   ```

3. **Cluster Signals**:
   ```python
   from cognition.utils import cluster_signals
   result = cluster_signals(your_signals, n_clusters=5)
   ```

4. **Predict Challenge Success**:
   ```python
   from cognition.utils import predict_challenge_success
   prediction = predict_challenge_success(user_metrics)
   ```

---

## 📦 Dependencies Required

All dependencies are **already installed** from the zennews setup:

✅ spacy (3.8.8) + en_core_web_sm model  
✅ textblob (0.19.0) + corpora  
✅ vaderSentiment (3.3.2)  
✅ nltk (3.9.2)  
✅ scikit-learn (1.6.1)  
✅ pandas (already in use)  
✅ numpy (already in use)

**No additional installations needed!**

---

## 🎯 Key Features

### Psychology Analysis
- ✅ Real-time sentiment tracking
- ✅ Bias detection (6 types)
- ✅ Confidence trendline over time
- ✅ Risk tolerance profiling
- ✅ Discipline scoring

### Market Intelligence  
- ✅ Automatic regime classification
- ✅ 6 regime types with confidence scores
- ✅ Pattern detection
- ✅ Volatility monitoring
- ✅ Trend strength calculation

### Signal Intelligence
- ✅ ML-based signal clustering
- ✅ Performance tracking by cluster
- ✅ Reliability scoring
- ✅ Automatic cluster assignment for new signals

### Prop Firm Intelligence
- ✅ Pass probability prediction
- ✅ Risk assessment
- ✅ Completion estimation
- ✅ Personalized recommendations

---

## 🚀 Next Steps

### To Complete Full Integration:

1. **Add ZenBot Integration** (\`bot/ai_score.py\`):
   - Create `integrate_cognition_bias()` function
   - Add psychological_bias, regime_bias, cluster_reliability to score breakdown

2. **Create Management Commands**:
   - `analyze_psychology` - Analyze journal entries
   - `detect_regime` - Classify current market state
   - `cluster_signals` - Group and analyze signals
   - `predict_challenge` - Calculate prop firm probability

3. **Build Dashboard UI**:
   - Trader Mindset Meter (sentiment gauge)
   - Market Regime Status badge
   - Signal Cluster Map (heatmap)
   - Prop-Firm Predictor panel
   - Summary feed of insights

4. **Configure Django Admin**:
   - Custom admin for all 5 models
   - Filters and search
   - Inline editing

5. **Create API Endpoints**:
   - `/cognition/api/psychology/`
   - `/cognition/api/regime/`
   - `/cognition/api/clusters/`
   - `/cognition/api/prop-prediction/`

---

## 💡 How It Works

### Workflow Example:

1. **Trader writes journal entry**: "Had a great day! Won 3 trades easily."
   - Psychology Analyzer detects: `sentiment=0.7`, `emotional_tone='confident'`, `confidence_level=0.8`
   - Stores in `TraderPsychology` model

2. **Market data arrives**: EURUSD 15m candles
   - Regime Detector calculates: `regime_type='strong_trend'`, `trend_strength=0.75`, `regime_bias=0.6`
   - Stores in `MarketRegime` model

3. **Signal generated**: ZenBot creates EURUSD buy signal
   - Signal Clusterer assigns to cluster: `cluster_id=2`, `reliability=0.72`
   - Stores in `SignalCluster` model

4. **AI scoring runs**:
   ```python
   base_score = 75.0
   
   # Apply cognition adjustments
   psych_bias = +0.3  # Confident trader
   regime_bias = +0.6  # Strong trend (favorable)
   cluster_reliability = 0.72  # Good cluster
   
   cognition_adjustment = (0.3*0.3 + 0.6*0.4 + 0.72*0.3) * 10 = +5.4
   
   final_score = 75 + 5.4 = 80.4
   ```

5. **Dashboard displays**:
   - "Trader: Confident ✅"
   - "Market: Strong Trend 📈"
   - "Signal: High Reliability Cluster 🎯"
   - "Overall: Favorable Conditions"

---

## ✨ System Architecture

```
Cognition Module
├── Models (Database)
│   ├── TraderPsychology (sentiment, biases, confidence)
│   ├── MarketRegime (trend, volatility, patterns)
│   ├── SignalCluster (ML grouping, reliability)
│   ├── PropFirmPrediction (challenge success)
│   └── CognitionInsight (alerts, summaries)
│
├── Utils (Intelligence Engines)
│   ├── psychology_analyzer.py (NLP + sentiment)
│   ├── regime_detector.py (technical analysis)
│   ├── signal_clusterer.py (ML clustering)
│   └── prop_predictor.py (probability calc)
│
├── Integration
│   └── bot/ai_score.py (cognition bias injection)
│
├── Dashboard (UI)
│   ├── Mindset Meter
│   ├── Regime Status
│   ├── Cluster Map
│   └── Prop Predictor
│
└── Management Commands
    ├── analyze_psychology
    ├── detect_regime
    ├── cluster_signals
    └── predict_challenge
```

---

## 🎉 Status: Core System Complete

✅ **5 Database Models** - Created and migrated  
✅ **4 Intelligence Engines** - Fully implemented  
✅ **NLP Analysis** - spaCy, TextBlob, VADER, NLTK  
✅ **ML Clustering** - scikit-learn KMeans  
✅ **Regime Detection** - Technical indicators + patterns  
✅ **Prop Prediction** - Rule-based heuristics  
✅ **Zero External APIs** - Fully local, free

**The cognition module is operational and ready for integration with ZenBot and dashboard!**

---

## 📚 Example Use Cases

### 1. Detect Overconfidence
```python
text = "This is guaranteed money. I'm all in!"
analysis = analyze_trader_text(text)
# Result: emotional_tone='overconfident', detected_biases=['overconfidence']
# Action: Reduce position size automatically
```

### 2. Avoid Choppy Markets
```python
regime = detect_market_regime(ohlc_data)
if regime['regime_type'] == 'choppy':
    # Result: regime_bias=-0.5
    # Action: Lower signal confidence by 5 points
    pass
```

### 3. Trust High-Performing Clusters
```python
result = cluster_signals(historical_signals)
best_cluster = max(result['cluster_metrics'], key=lambda x: x['reliability_score'])
# If new signal matches best cluster: boost confidence
# If new signal matches worst cluster: reduce confidence
```

### 4. Warn Before Failure
```python
prediction = predict_challenge_success(metrics)
if prediction['pass_probability'] < 0.3:
    # Alert: "High risk of challenge failure - 70% risk"
    # Show recommendations to user
    pass
```

---

**ZenithEdge is now psychologically intelligent, market-aware, and adaptive!** 🧠📈🚀
