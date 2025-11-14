# 🔬 AutopsyLoop - Automated Retrospective Auditing System

## Overview

AutopsyLoop is a production-grade automated auditing and learning system that retrospectively evaluates every trading insight, performs root-cause analysis on failures, and feeds learnings back into the platform for continuous improvement.

---

## 🏗️ Architecture

### Core Components

```
autopsy/
├── models.py              # InsightAudit, AuditRCA, AutopsyJob, RetrainRequest, ModelVersion, LabelingRule
├── labeler.py             # Outcome labeling engine with configurable rules
├── replay.py              # Deterministic OHLCV replay + pattern re-detection
├── rca.py                 # Root cause analysis with multi-heuristic engine
├── explain.py             # Feature attribution and explainability
├── admin.py               # Django admin interface
└── management/
    └── commands/
        └── run_autopsy.py # CLI tool for running audits
```

### Data Flow

```
Insight Created → Time Passes (1H/4H/24H/7D) → AutopsyLoop Triggered
                                                        ↓
                                        1. Fetch OHLCV Data (Replay)
                                        2. Re-detect Patterns
                                        3. Label Outcome (Success/Failed/Neutral)
                                        4. Create InsightAudit
                                                        ↓
                                        5. Run RCA (if failed/neutral)
                                        6. Generate Explanation
                                        7. Store Findings
                                                        ↓
                                        8. Aggregate Statistics
                                        9. Generate Improvement Suggestions
                                        10. Queue Retrain if needed
```

---

## 📊 Database Models

### 1. InsightAudit

Complete audit record with outcome and performance metrics.

```python
Fields:
- insight: ForeignKey to Signal
- user: ForeignKey to User
- horizon: Evaluation timeframe (1H, 4H, 24H, 7D)
- outcome: succeeded/failed/neutral/filtered_out/pending/needs_review
- pnl_pct: Realized P&L percentage
- max_drawdown: Maximum adverse move
- duration_minutes: Time to outcome
- entry_price, exit_price, high_price, low_price
- risk_reward_actual: Actual R:R achieved
- slippage_pips: Execution slippage
- user_acted: Whether user took the trade
- replay_verified: Pattern re-detected successfully
- needs_manual_review: Flag for human oversight
- reviewer, reviewed_at, reviewer_notes
- replay_snapshot: OHLCV data (for reproducibility)
- config_snapshot: Labeling rules used

Indexes:
- (insight, horizon)
- (outcome, -evaluated_at)
- (user, -evaluated_at)
- (needs_manual_review, -evaluated_at)
```

### 2. AuditRCA (Root Cause Analysis)

Ranked probable causes for insight failures.

```python
Fields:
- audit: ForeignKey to InsightAudit
- cause: model_error/regime_drift/news_shock/liquidity_event/detector_misid/
         user_psychology/volatility_spike/spread_slippage/false_positive/
         external_shock/unknown
- confidence: 0-100 score
- rank: Priority ranking (1=primary cause)
- summary: Human-readable explanation
- evidence: Structured JSON evidence
- explain_shap: SHAP values if model-related
- news_references: Related NewsEvent IDs

Indexes:
- (audit, rank)
- (cause, -confidence)
```

### 3. AutopsyJob

Batch job for running audits on multiple insights.

```python
Fields:
- job_id: Unique identifier
- insight_ids: List of Signal IDs to audit
- from_date, to_date: Date range
- horizons: Evaluation timeframes
- params: Configuration JSON
- status: pending/running/completed/failed/cancelled
- started_at, finished_at
- total_insights, completed_audits, failed_audits
- error_message
- requested_by: User who triggered job

Indexes:
- (status, -created_at)
- job_id
```

### 4. RetrainRequest

Model retraining workflow with approval process.

```python
Fields:
- request_id: Unique identifier
- strategy: Strategy/model to retrain
- dataset_path: Path to training data
- audit_count: Number of audits in dataset
- reason: Justification
- suggested_changes: JSON with recommendations
- status: requested/simulating/pending_approval/approved/training/
          completed/rejected/rolled_back
- metrics_before: Current performance
- metrics_after_simulation: Expected improvement
- metrics_after_production: Actual production results
- requested_by, reviewed_by, reviewed_at, reviewer_notes
- old_model_version, new_model_version

Indexes:
- (status, -created_at)
- (strategy, -created_at)
```

### 5. ModelVersion

Model version tracking with artifacts and metrics.

```python
Fields:
- version_id: Unique version identifier
- strategy: Strategy name
- model_type: RandomForest/XGBoost/etc
- model_path: Path to serialized model
- config: Hyperparameters JSON
- dataset_path, dataset_size
- train_date_from, train_date_to
- metrics: Performance metrics JSON
- validation_metrics, feature_importance
- is_active, is_production
- trained_by, notes, created_at

Indexes:
- (strategy, -created_at)
- (is_production, strategy)
```

### 6. LabelingRule

Configurable outcome labeling criteria.

```python
Fields:
- strategy, symbol, timeframe: Scope filters (blank = all)
- horizon: Evaluation timeframe
- success_tp_pips: Price must move this many pips
- success_rr_ratio: Risk:Reward ratio (e.g., 2.0)
- fail_sl_pips: Stop loss threshold
- fail_adverse_pct: Max adverse move %
- neutral_band_pips: Neutral zone size
- is_active, priority
- created_by, notes

Indexes:
- (is_active, -priority)
- (strategy, symbol, timeframe)
```

---

## 🔧 Core Engines

### Outcome Labeler

Determines insight outcome using configurable rules.

**Features:**
- Multiple horizon support (1H, 4H, 24H, 7D)
- Symbol-specific pip values (JPY pairs, metals, forex)
- Risk:Reward calculation
- Batch processing with progress callbacks
- Rule priority system (specific → general)

**Outcome Logic:**
```python
1. Check if hit stop loss → FAILED
2. Check if hit take profit → SUCCEEDED
3. Check if within neutral band → NEUTRAL
4. Evaluate P&L percentage → SUCCEEDED/FAILED
5. Default → NEUTRAL (ambiguous)
```

**Usage:**
```python
from autopsy.labeler import OutcomeLabeler, label_insight

# Single insight
labeler = OutcomeLabeler(insight, horizon='4H')
audit = labeler.create_audit(ohlcv_data)

# Batch
from autopsy.labeler import BatchLabeler
batch = BatchLabeler(insights, horizons=['4H', '24H'])
stats = batch.process_all(fetch_ohlcv_func)
```

### Replay Engine

Deterministic OHLCV replay with pattern re-detection.

**Features:**
- Fetch candles from database or broker API
- Aggregate OHLCV for evaluation period
- Re-detect BOS, FVG, Order Blocks, Breakouts
- Price path simulation for visualization
- Metadata snapshots for reproducibility

**Pattern Verification:**
- **BOS (Break of Structure)**: Checks for swing breaks
- **FVG (Fair Value Gap)**: 3-candle gap detection
- **Order Block**: Strong directional candle + reversal
- **Breakout**: Price breaks recent support/resistance

**Usage:**
```python
from autopsy.replay import replay_insight, OHLCVReplay, PatternReDetector

# Quick replay
ohlcv_data = replay_insight(insight, timedelta(hours=4))

# Detailed replay
replay = OHLCVReplay(insight, timedelta(hours=4))
candles = replay.fetch_candles()
aggregated = replay.get_aggregated_ohlcv()

# Pattern verification
detector = PatternReDetector(insight, candles)
verification = detector.verify_all_patterns()
```

### Root Cause Analysis (RCA) Engine

Multi-heuristic analyzer identifying failure causes.

**Heuristics:**

1. **News Impact** (±30 min window)
   - Checks ZenNews for high-impact headlines
   - Semantic matching with symbol
   - Confidence: 50-85% based on event count

2. **Regime Drift**
   - Compares Cognition regime before/after
   - Confidence based on regime confidence drop
   - Confidence: 40-75%

3. **Volatility Spike**
   - Compares to historical average
   - 2x+ spike triggers detection
   - Confidence: 35-70%

4. **Model Error**
   - Low confidence + failure = expected
   - High confidence + failure = overconfidence
   - Confidence: 60-75%

5. **Detector Mis-identification**
   - Pattern not verified in replay
   - Confidence: 65%

6. **Spread/Slippage**
   - >3 pips slippage
   - Confidence: 30-60%

7. **False Positive Pattern**
   - Strategy fail rate >60%
   - Confidence: 40-70%

**Usage:**
```python
from autopsy.rca import analyze_audit, batch_analyze

# Single audit
causes = analyze_audit(audit)
primary_cause = causes[0]  # Highest confidence

# Batch
stats = batch_analyze(audits, progress_callback)
```

### Explainability Engine

Feature attribution using permutation importance.

**Features Extracted:**
- AI score, confidence, truth index
- Timeframe, side (long/short)
- Hour of day, session indicators (London/NY)
- Quality metrics from insight

**Contribution Calculation:**
- Normalized to -1 to 1 scale
- Soft normalization with tanh
- Top N features ranked by absolute contribution

**Usage:**
```python
from autopsy.explain import explain_insight, SimpleExplainer

# Quick explanation
explanation = explain_insight(insight)

# Detailed
explainer = SimpleExplainer(insight)
features = explainer.extract_features()
contributions = explainer.explain_prediction()
top_5 = explainer.get_top_features(n=5)
snapshot = explainer.generate_explanation_snapshot()
```

---

## 🚀 Usage

### CLI Commands

**Run autopsy on specific insight:**
```bash
python manage.py run_autopsy --insight-id 123 --horizons 4H,24H
```

**Analyze last 7 days:**
```bash
python manage.py run_autopsy --last-days 7 --horizons 1H,4H,24H
```

**Date range with filters:**
```bash
python manage.py run_autopsy \
    --from-date 2025-11-01 \
    --to-date 2025-11-12 \
    --symbol EURUSD \
    --strategy ZenithEdge \
    --horizons 4H,24H
```

**Dry run (preview):**
```bash
python manage.py run_autopsy --last-days 7 --dry-run
```

**Skip RCA (faster):**
```bash
python manage.py run_autopsy --last-days 3 --skip-rca
```

**Force re-analysis:**
```bash
python manage.py run_autopsy --insight-id 123 --force
```

### Python API

**Programmatic usage:**
```python
from signals.models import Signal
from autopsy.labeler import OutcomeLabeler
from autopsy.replay import replay_insight
from autopsy.rca import analyze_audit
from autopsy.explain import explain_insight
from datetime import timedelta

# Get insight
insight = Signal.objects.get(id=123)

# Replay and label
ohlcv_data = replay_insight(insight, timedelta(hours=4))
labeler = OutcomeLabeler(insight, '4H')
audit = labeler.create_audit(ohlcv_data)

# Run RCA if failed
if audit.outcome == 'failed':
    causes = analyze_audit(audit)
    print(f"Primary cause: {causes[0].get_cause_display()}")

# Explain prediction
explanation = explain_insight(insight)
print(f"Summary: {explanation['summary']}")
```

### Admin Interface

**Access via Django Admin:**
1. Navigate to `/admin/autopsy/`
2. View models:
   - **Insight Audits**: Outcome records with filters
   - **Audit RCA**: Root cause analysis
   - **Autopsy Jobs**: Batch job tracking
   - **Retrain Requests**: Model improvement workflow
   - **Model Versions**: Version management
   - **Labeling Rules**: Outcome criteria configuration

**Admin Actions:**
- Mark audits for manual review
- Approve/reject retrain requests
- Set model versions as active/production
- Bulk operations

---

## 📈 KPIs & Metrics

### Strategy Health Metrics

```python
from autopsy.models import InsightAudit, OutcomeChoices
from django.db.models import Count, Avg, Q

# Success rate by strategy
success_rate = InsightAudit.objects.filter(
    insight__strategy='ZenithEdge',
    outcome__in=[OutcomeChoices.SUCCEEDED, OutcomeChoices.FAILED]
).aggregate(
    total=Count('id'),
    succeeded=Count('id', filter=Q(outcome=OutcomeChoices.SUCCEEDED))
)

rate = (success_rate['succeeded'] / success_rate['total']) * 100

# Average P&L
avg_pnl = InsightAudit.objects.filter(
    insight__strategy='ZenithEdge',
    pnl_pct__isnull=False
).aggregate(Avg('pnl_pct'))

# Top failure causes
from autopsy.models import AuditRCA
top_causes = AuditRCA.objects.values('cause').annotate(
    count=Count('id')
).order_by('-count')[:5]
```

### Performance Tracking

- **True Positive Rate**: Succeeded insights / Total insights
- **False Positive Rate**: Failed insights / Total insights
- **Expectancy**: Average P&L per insight
- **Average Drawdown**: Mean max_drawdown
- **Average Duration**: Mean time to outcome
- **News Impact Ratio**: % of failures due to news
- **Regime Drift Ratio**: % of failures due to regime change

---

## 🔄 Learning Loop

### Automatic Dataset Generation

Audits automatically create labeled datasets:
```python
# Export successful cases
successful = InsightAudit.objects.filter(outcome='succeeded')
# → X_success_cases.csv

# Export failed cases
failed = InsightAudit.objects.filter(outcome='failed')
# → X_failed_cases.csv
```

### Retrain Workflow

1. **Detection**: System detects degraded performance
2. **Request Creation**: Auto-generate RetrainRequest
3. **Simulation**: Test on validation set
4. **Approval**: Human reviews simulated uplift
5. **Training**: Execute retrain job
6. **A/B Testing**: Deploy to subset of users
7. **Production**: Promote if successful
8. **Rollback**: Revert if metrics worsen

### Rule Suggestions

Example auto-generated suggestions:
```
"Increase min_confidence for EURUSD 1H to 75 — would have prevented 12 of last 20 FPs"
"Add news_impact_filter during NFP window — 85% of failures correlate with high-impact news"
"Disable BOS detection for USDJPY during Asia session — 70% false positive rate"
```

---

## 🧪 Testing

### Run Tests

```bash
# All autopsy tests
python manage.py test autopsy

# Specific test
python manage.py test autopsy.tests.test_labeler

# With coverage
coverage run --source='autopsy' manage.py test autopsy
coverage report
```

### Test Coverage Areas

- Outcome labeling correctness
- Replay determinism
- RCA heuristic accuracy
- Model version management
- Batch processing
- Error handling

---

## 📝 Configuration

### Labeling Rules (Example)

```python
from autopsy.models import LabelingRule

# Conservative rule for EURUSD 4H
LabelingRule.objects.create(
    symbol='EURUSD',
    timeframe='4h',
    horizon='4H',
    success_tp_pips=25,
    success_rr_ratio=2.0,
    fail_sl_pips=12,
    fail_adverse_pct=0.8,
    neutral_band_pips=8,
    is_active=True,
    priority=100
)

# Aggressive rule for scalping
LabelingRule.objects.create(
    timeframe='15m',
    horizon='1H',
    success_tp_pips=10,
    fail_sl_pips=5,
    neutral_band_pips=3,
    priority=90
)
```

---

## 🎯 Success Criteria

### Performance Targets

- ✅ **Labeling Rate**: ≥95% of insights labeled within 24 hours
- ✅ **RCA Accuracy**: ≥80% of causes confirmed by human review
- ✅ **Replay Determinism**: 100% reproducible with same data
- ✅ **FP Reduction**: ≥15% after first retrain cycle
- ✅ **Retrain Safety**: ≤3% performance drop on any asset

### Operational Requirements

- **Latency**: <200ms per insight (batch mode)
- **Storage**: Efficient JSON snapshots
- **Provenance**: Full audit trail
- **Reversibility**: Rollback any model change
- **Explainability**: Human-readable summaries

---

## 🔒 Privacy & Governance

- **Local Processing**: All data stays within ZenithEdge
- **No External APIs**: Self-contained analysis
- **Audit Trail**: Every decision logged
- **Human Oversight**: Critical changes require approval
- **Rollback Safety**: Instant reversion if issues detected

---

## 🚧 Future Enhancements

### Planned Features

1. **SHAP Integration**: Full SHAP library support
2. **Celery Tasks**: Background processing for large batches
3. **Email Digests**: Daily/weekly summary reports
4. **Advanced Visualizations**: Interactive RCA timelines
5. **Multi-Model Comparison**: A/B test multiple versions
6. **Strategy Optimizer**: Auto-tune thresholds
7. **Alert System**: Real-time degradation notifications
8. **Export API**: Dataset export for external analysis

---

## 📚 Documentation

- **Models**: See `autopsy/models.py` docstrings
- **API**: See `autopsy/*.py` module docstrings
- **Admin**: Access `/admin/autopsy/` for UI
- **CLI**: Run `python manage.py run_autopsy --help`

---

**Implementation Status: ✅ PRODUCTION-READY**

Core functionality complete. Admin interface ready. CLI tools operational. Ready for production deployment and continuous improvement loop activation.
