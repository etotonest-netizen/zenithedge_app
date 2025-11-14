# Zenith Market Analyst - Visual Insights Mode Implementation Guide

## 🎯 System Overview

**Zenith Market Analyst** is a revolutionary Visual Insights Mode that transforms ZenithEdge from a signal-only system into a **continuous market intelligence companion**. Every bar generates unique, professional market commentary - NO REPETITION, NO EXTERNAL APIs, 100% LOCAL.

---

## 📊 What Has Been Built

### 1. **Database Models** (`autopsy/models.py`) ✅
Added comprehensive models for Visual Insights Mode:

#### **MarketInsight** - Core insight storage
- Symbol, timeframe, timestamp
- Market metadata: regime, structure, momentum, volume, session
- AI-generated insights and suggestions
- Insight Index (0-100 quality score)
- Component scores: structure_clarity, regime_stability, volume_quality, momentum_alignment, session_validity, risk_level
- News integration fields
- Chart labels for TradingView display
- Variation tracking (vocabulary_hash, sentence_structure_id)

#### **VariationVocabulary** - Dynamic vocabulary management
- Category-based phrase storage (liquidity, momentum, structure, regime, session, volume)
- Variations array for synonym swapping
- Usage tracking and rotation
- Context-aware rules

#### **InsightTemplate** - Sentence structure templates
- Template ID and structure with slots
- Regime/structure filters
- Usage rotation for uniqueness

---

### 2. **Insight Parser** (`autopsy/insight_parser.py`) ✅
**Purpose**: Parse Pine Script metadata JSON into validated Python objects

**Features**:
- Validates required fields (regime, structure, momentum, volume, session)
- Normalizes all enum values to match database choices
- Converts timestamps to datetime objects
- Extracts chart labels for TradingView overlay
- Calculates preliminary context quality score (0-100)
- Builds human-readable risk summaries

**Key Methods**:
```python
parser = InsightParser()
metadata = parser.parse(raw_pine_data)  # Returns structured dict
chart_labels = parser.extract_chart_labels(metadata)  # For TradingView
context_score = parser.calculate_context_score(metadata)  # Preliminary score
```

---

### 3. **Variation Engine** (`autopsy/variation_engine.py`) ✅
**Purpose**: Ensure ZERO REPETITION through dynamic vocabulary generation

**Comprehensive Vocabulary Library**:
- **Liquidity**: building, sweeping (8+ variations each)
- **Momentum**: increasing, decreasing, diverging (6-8 variations each)
- **Structure**: BOS, CHoCH, pullback, sweep, FVG, OB, compression (4-5 variations each)
- **Regime**: trending, ranging, volatile, consolidation (4-5 variations each)
- **Session**: London, NY, Asia, off-session (4 variations each)
- **Expectation**: expansion, retracement, reversal, liquidity_grab (4 variations each)

**Sentence Templates**:
- 5+ structural templates with variable slots
- Context-aware slot filling
- Automatic hash-based uniqueness tracking

**Key Methods**:
```python
engine = VariationEngine()
insight_text, vocab_hash = engine.generate_insight(metadata)  # Unique every time
suggestion = engine.generate_suggestion(metadata)  # Actionable guidance
```

**Example Outputs** (same metadata, different results):
```
"Price is building liquidity and has just swept a prior low within a ranging environment."
"Liquidity forming near key levels as market oscillates between boundaries."
"Resting liquidity observed above prior structure within bound range conditions."
```

---

### 4. **Insight Scorer** (`autopsy/insight_scorer.py`) ✅
**Purpose**: Calculate comprehensive Insight Index (0-100)

**Scoring Components** (weighted):
1. **Structure Clarity (25%)**: How clear is the market structure?
   - BOS = 95, CHoCH = 85, OB = 80, Liquidity Sweep = 75
   - Adjusted by strength value

2. **Regime Stability (20%)**: How predictable is the regime?
   - Trending = 90, Consolidation = 70, Ranging = 60, Volatile = 30

3. **Volume Quality (15%)**: Does volume support price action?
   - Spike during breakout = excellent (+15)
   - Low volume during pullback = acceptable (+15)
   - Low volume during breakout = warning (-20)

4. **Momentum Alignment (15%)**: Does momentum support structure?
   - Divergence = 85 (always valuable)
   - Momentum + trending = +15
   - Momentum + structure break = +10

5. **Session Validity (15%)**: Liquidity conditions
   - NY = 95, London = 90, Asia = 70, Off-session = 30
   - Overlap boost = +10

6. **Risk Level (10%)**: Inverted - lower risk = higher score
   - Deductions for: high volatility (-20), news risk (-25), no structure (-15)

**Key Methods**:
```python
scorer = InsightScorer()
insight_index, breakdown = scorer.calculate_insight_index(metadata)
quality_label = scorer.get_quality_label(insight_index)  # "Exceptional", "High Quality", etc.
color = scorer.get_color_code(insight_index)  # #10b981, #3b82f6, etc.
```

---

### 5. **AI Insight Engine** (`autopsy/insight_engine.py`) ✅
**Purpose**: Central intelligence system tying everything together

**Complete Processing Pipeline**:
```python
analyst = ZenithMarketAnalyst()

# Process single bar from Pine Script
insight_data = analyst.process_bar(raw_pine_json)
# Returns complete insight object ready for database

# Save to database
insight = analyst.save_insight(insight_data)

# Retrieve for UI
latest_insights = analyst.get_latest_insights(symbol='EURUSD', limit=50)

# Get statistics
stats = analyst.get_insight_statistics(hours=24)
```

**Key Features**:
- Automatic news integration from `zennews` app
- Hash-based uniqueness tracking
- Comprehensive error handling and logging
- Built-in testing mode (`test_insight_generation(sample_count=10)`)

---

## 🔧 Setup & Deployment Instructions

### Step 1: Run Database Migrations

```bash
cd ~/zenithedge_trading_hub

# Create migrations for new models
python3 manage.py makemigrations autopsy

# Apply migrations
python3 manage.py migrate autopsy

# Verify tables created
python3 manage.py dbshell
sqlite> .tables
# Should see: autopsy_marketinsight, autopsy_variationvocabulary, autopsy_insighttemplate
sqlite> .quit
```

### Step 2: Populate Initial Vocabulary (Optional)

```python
# Create management command: autopsy/management/commands/seed_vocabulary.py
python3 manage.py seed_vocabulary
```

### Step 3: Add Admin Interfaces

```bash
# Edit autopsy/admin.py - add:
from autopsy.models import MarketInsight, VariationVocabulary, InsightTemplate

@admin.register(MarketInsight)
class MarketInsightAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'timeframe', 'regime', 'structure', 
                    'insight_index', 'timestamp']
    list_filter = ['regime', 'structure', 'session', 'created_at']
    search_fields = ['symbol', 'insight_text']
    readonly_fields = ['vocabulary_hash', 'created_at']

@admin.register(VariationVocabulary)
class VariationVocabularyAdmin(admin.ModelAdmin):
    list_display = ['category', 'subcategory', 'base_phrase', 'usage_count', 
                    'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['base_phrase']

@admin.register(InsightTemplate)
class InsightTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_id', 'usage_count', 'is_active', 'priority']
    list_filter = ['is_active']
```

### Step 4: Add URL Endpoints

Create `autopsy/urls.py`:
```python
from django.urls import path
from autopsy import views

app_name = 'autopsy'

urlpatterns = [
    # Existing URLs
    path('', views.dashboard, name='dashboard'),
    
    # NEW: Visual Insights Mode
    path('market-analyst/', views.market_analyst_view, name='market_analyst'),
    path('api/submit-insight/', views.submit_insight_webhook, name='submit_insight'),
    path('api/get-insights/', views.get_insights_api, name='get_insights'),
    path('api/chart-labels/<str:symbol>/', views.get_chart_labels, name='chart_labels'),
]
```

### Step 5: Create Views

Add to `autopsy/views.py`:
```python
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from autopsy.insight_engine import analyst
import json

@csrf_exempt
@require_POST
def submit_insight_webhook(request):
    """Webhook endpoint for Pine Script to submit bar metadata"""
    try:
        data = json.loads(request.body)
        
        # Process bar through AI engine
        insight_data = analyst.process_bar(data)
        
        # Save to database
        insight = analyst.save_insight(insight_data)
        
        return JsonResponse({
            'status': 'success',
            'insight_id': insight.id,
            'insight_index': insight.insight_index
        })
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def market_analyst_view(request):
    """Main Visual Insights dashboard"""
    symbol = request.GET.get('symbol', '')
    timeframe = request.GET.get('timeframe', '')
    
    # Get latest insights
    insights = analyst.get_latest_insights(symbol=symbol, timeframe=timeframe, limit=50)
    
    # Get statistics
    stats = analyst.get_insight_statistics(hours=24)
    
    context = {
        'insights': insights,
        'stats': stats,
        'symbol': symbol,
        'timeframe': timeframe,
    }
    
    return render(request, 'autopsy/market_analyst.html', context)

def get_insights_api(request):
    """API endpoint for real-time insight updates"""
    symbol = request.GET.get('symbol')
    timeframe = request.GET.get('timeframe')
    limit = int(request.GET.get('limit', 20))
    
    insights = analyst.get_latest_insights(symbol=symbol, timeframe=timeframe, limit=limit)
    
    data = [{
        'id': i.id,
        'symbol': i.symbol,
        'timeframe': i.timeframe,
        'timestamp': i.timestamp.isoformat(),
        'regime': i.get_regime_display(),
        'structure': i.get_structure_display(),
        'insight_text': i.insight_text,
        'suggestion': i.suggestion,
        'insight_index': i.insight_index,
        'chart_labels': i.chart_labels,
        'news_context': i.news_context,
    } for i in insights]
    
    return JsonResponse({'insights': data})
```

---

## 🧪 Testing Commands

### Test 1: Insight Generation

```bash
cd ~/zenithedge_trading_hub
python3 manage.py shell
```

```python
from autopsy.insight_engine import analyst

# Test with sample data
test_results = analyst.test_insight_generation(sample_count=10)

# Should output 10 unique insights with different vocabulary
# Verify no two insights are identical
```

### Test 2: Parser Validation

```python
from autopsy.insight_parser import InsightParser

parser = InsightParser()

test_data = {
    'symbol': 'EURUSD',
    'timeframe': '1H',
    'timestamp': '2025-11-13T12:00:00Z',
    'regime': 'trending',
    'structure': 'bos',
    'momentum': 'increasing',
    'volume_state': 'spike',
    'session': 'london',
    'expected_behavior': 'Expansion',
    'strength': 85,
    'risk_notes': ['High volatility'],
}

metadata = parser.parse(test_data)
print(f"Parsed: {metadata}")

chart_labels = parser.extract_chart_labels(metadata)
print(f"Chart labels: {chart_labels}")
```

### Test 3: Variation Engine Uniqueness

```python
from autopsy.variation_engine import VariationEngine

engine = VariationEngine()

# Generate 100 insights from same metadata
test_metadata = {
    'regime': 'ranging',
    'structure': 'liquidity_sweep',
    'momentum': 'increasing',
    'session': 'london',
    'expected_behavior': 'Liquidity grab',
    'strength': 75,
    'risk_notes': [],
}

insights = []
for i in range(100):
    text, hash_val = engine.generate_insight(test_metadata)
    insights.append(text)

# Check uniqueness
unique = set(insights)
print(f"Generated {len(insights)} insights, {len(unique)} unique ({len(unique)/len(insights)*100:.1f}%)")
# Should be >95% unique
```

### Test 4: Scorer Accuracy

```python
from autopsy.insight_scorer import InsightScorer

scorer = InsightScorer()

# High quality setup
high_quality = {
    'structure': 'bos',
    'regime': 'trending',
    'momentum': 'increasing',
    'volume_state': 'spike',
    'session': 'newyork',
    'expected_behavior': 'Expansion',
    'strength': 90,
    'risk_notes': [],
    'timestamp': timezone.now(),
}

index, breakdown = scorer.calculate_insight_index(high_quality)
print(f"High Quality Score: {index}/100")
print(f"Breakdown: {breakdown}")
# Should be 80+

# Low quality setup
low_quality = {
    'structure': 'none',
    'regime': 'volatile',
    'momentum': 'neutral',
    'volume_state': 'drop',
    'session': 'off',
    'expected_behavior': '',
    'strength': 30,
    'risk_notes': ['High volatility', 'News risk'],
    'timestamp': timezone.now(),
}

index2, breakdown2 = scorer.calculate_insight_index(low_quality)
print(f"Low Quality Score: {index2}/100")
# Should be <40
```

---

## 📈 Pine Script Integration (Next Step)

### Enhanced Pine Script Template

The existing `TRADINGVIEW_INDICATOR_TEMPLATE.pine` needs to be enhanced to output Visual Insights metadata on **every bar** (not just signals).

**Required Additions**:

1. **Calculate regime, structure, momentum on every bar**
2. **Format metadata JSON**
3. **Send via alert() or webhook**

**Example alert payload structure**:
```json
{
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "timestamp": "{{time}}",
  "price": {{close}},
  "regime": "Trending",
  "structure": "BOS",
  "momentum": "Increasing",
  "volume_state": "Spike",
  "session": "London",
  "expected_behavior": "Expansion",
  "strength": 85,
  "risk_notes": ["High volatility"]
}
```

---

## 🎨 UI Dashboard Template

Create `autopsy/templates/autopsy/market_analyst.html` with:

- **Live insight cards** (auto-refresh)
- **Context line** (symbol, regime, session, time)
- **Insight box** (professional commentary)
- **Insight Index gauge** (0-100 with color coding)
- **Suggestion block** (actionable guidance)
- **News awareness tag** (high-impact events)
- **Chart label preview** (micro-labels display)
- **Statistics panel** (regime distribution, average index)

---

## 📊 Performance Expectations

### Uniqueness Targets
- **>95% unique insights** across 500+ bars
- **0% identical consecutive insights**
- **Dynamic vocabulary rotation**

### Speed Targets
- **<50ms processing time** per bar
- **<100ms database save**
- **<200ms total webhook response**

### Quality Targets
- **Exceptional (80+)**: 15-20% of insights
- **High Quality (65-79)**: 30-40% of insights
- **Moderate (50-64)**: 30-40% of insights
- **Low Quality (<50)**: <15% of insights

---

## 🔐 Security Notes

- All processing is **100% local** - no external API calls
- Webhook endpoint should use **authentication** in production
- Rate limiting recommended for public webhooks
- Database backups essential (MarketInsight table will grow large)

---

## 📝 Next Steps

1. ✅ **Models created** - Run migrations
2. ✅ **Core engines built** - Test in Python shell
3. ⏳ **Views/URLs** - Create webhook endpoints
4. ⏳ **UI template** - Build dashboard
5. ⏳ **Pine Script** - Enhanced metadata output
6. ⏳ **Testing suite** - 500+ bar validation
7. ⏳ **Admin interface** - Monitor insights
8. ⏳ **Documentation** - User guide

---

## 🎯 Success Criteria

The system is production-ready when:

- [ ] 500+ bar test shows >95% uniqueness
- [ ] No repeated consecutive insights
- [ ] Average Insight Index >60
- [ ] Webhook response time <200ms
- [ ] UI dashboard loads <1s
- [ ] All vocabulary categories populated
- [ ] News integration working
- [ ] Admin monitoring functional

---

## 💡 Example Use Cases

### Use Case 1: Real-Time Commentary
```
User opens chart → Sees micro-labels on candles → Clicks label → Full insight card appears
"Market shows consolidation phase with liquidity clustering near equal highs.
London session flow suggests accumulation rather than continuation.
Monitor reaction at key levels - structure supports directional bias."
```

### Use Case 2: Dashboard Monitoring
```
User opens Market Analyst dashboard → Sees live feed of insights
- 50 recent insights
- Filtered by symbol/timeframe
- Statistics showing regime distribution
- News awareness alerts
- Quality scores for each insight
```

### Use Case 3: Learning Mode
```
Trader reviews past insights → Sees how market behaved vs. AI commentary
"AI said: 'Compression phase - expansion likely' → Market expanded 2 hours later"
"AI said: 'Low-quality environment - mixed signals' → Market chopped sideways"
```

---

## 🚀 Deployment Checklist

- [ ] Run migrations (`makemigrations`, `migrate`)
- [ ] Seed vocabulary database
- [ ] Test all engines in Python shell
- [ ] Create webhook endpoint
- [ ] Test webhook with sample JSON
- [ ] Build UI dashboard
- [ ] Update Pine Script template
- [ ] Configure TradingView webhook
- [ ] Test end-to-end pipeline
- [ ] Monitor logs for errors
- [ ] Set up database backups
- [ ] Add admin monitoring
- [ ] Create user documentation

---

**Built by**: GitHub Copilot for ZenithEdge Intelligence System
**Date**: November 13, 2025
**Version**: 1.0.0
**Status**: Core engines complete, awaiting integration
