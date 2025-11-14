# 🚀 AutopsyLoop Quick Start Guide

## Installation Complete ✅

The AutopsyLoop system has been successfully installed and is ready to use!

---

## 🎯 Quick Test Run

### 1. Access Admin Interface

Open your browser and navigate to:
```
http://localhost:8000/admin/autopsy/
```

You'll see:
- **Insight Audits** - Outcome records
- **Audit RCA** - Root cause analysis
- **Autopsy Jobs** - Batch processing
- **Retrain Requests** - Model improvement
- **Model Versions** - Version tracking
- **Labeling Rules** - Configuration

### 2. Run Your First Autopsy

Analyze a specific insight:
```bash
cd ~/zenithedge_trading_hub
python3 manage.py run_autopsy --insight-id 28 --horizons 4H
```

Analyze last 7 days:
```bash
python3 manage.py run_autopsy --last-days 7 --horizons 4H,24H
```

Preview what would be analyzed:
```bash
python3 manage.py run_autopsy --last-days 3 --dry-run
```

### 3. View Results

**In Django Admin:**
1. Go to `/admin/autopsy/insightaudit/`
2. See color-coded outcomes (✅ Succeeded, ❌ Failed, ⚪ Neutral)
3. Click an audit to see:
   - P&L, drawdown, duration
   - Pattern verification results
   - Root cause analysis (if failed)
   - Price replay snapshot

**Check Root Causes:**
1. Go to `/admin/autopsy/auditrca/`
2. See ranked causes with confidence scores
3. View evidence: news events, regime changes, volatility spikes

---

## 📊 Key Features Overview

### Outcome Labeling
```python
from autopsy.labeler import label_insight

# Labels insight as succeeded/failed/neutral based on:
# - Price movement (pips)
# - R:R ratio achievement
# - Stop loss hit
# - Time horizon (1H, 4H, 24H, 7D)
```

### Root Cause Analysis
Automatically identifies failure causes:
- 📰 News shocks (ZenNews integration)
- 🔄 Regime drift (Cognition integration)
- 📈 Volatility spikes
- 🤖 Model errors (overconfidence/underconfidence)
- 🔍 Pattern mis-detection
- 💸 Spread/slippage issues
- ❌ False positive patterns

### Pattern Re-Detection
Verifies original pattern in replay:
- Break of Structure (BOS)
- Fair Value Gap (FVG)
- Order Blocks
- Breakouts

---

## 🔧 Configuration

### Create Labeling Rule

```python
from autopsy.models import LabelingRule

LabelingRule.objects.create(
    symbol='EURUSD',
    timeframe='4h',
    horizon='4H',
    success_tp_pips=20,      # Must move 20 pips in favor
    fail_sl_pips=15,         # Failure if 15 pips against
    neutral_band_pips=10,    # Within 10 pips = neutral
    is_active=True,
    priority=100
)
```

### Schedule Automatic Audits

**Option 1: Cron Job**
```bash
# Add to crontab
0 */4 * * * cd ~/zenithedge_trading_hub && python3 manage.py run_autopsy --last-days 1
```

**Option 2: Celery Beat (future)**
```python
# In celerybeat schedule
'autopsy-daily': {
    'task': 'autopsy.tasks.run_daily_audits',
    'schedule': crontab(hour=2, minute=0),
}
```

---

## 📈 View Statistics

### Django Admin Filters

**Insight Audits:**
- Filter by outcome, horizon, symbol
- Date range filtering
- "Needs manual review" flag
- User filter

**Root Causes:**
- Filter by cause type
- Confidence threshold
- Date range

### Quick Queries

```python
from autopsy.models import InsightAudit, OutcomeChoices
from django.db.models import Count, Avg

# Success rate
stats = InsightAudit.objects.aggregate(
    total=Count('id'),
    succeeded=Count('id', filter=Q(outcome='succeeded'))
)
success_rate = (stats['succeeded'] / stats['total']) * 100

# Average P&L
avg_pnl = InsightAudit.objects.aggregate(Avg('pnl_pct'))

# Top failure causes
from autopsy.models import AuditRCA
AuditRCA.objects.values('cause').annotate(
    count=Count('id')
).order_by('-count')[:5]
```

---

## 🎓 Example Workflow

### Full Analysis Pipeline

```python
from signals.models import Signal
from autopsy.labeler import OutcomeLabeler
from autopsy.replay import replay_insight
from autopsy.rca import analyze_audit
from autopsy.explain import explain_insight
from datetime import timedelta

# 1. Get insight
insight = Signal.objects.filter(symbol='EURUSD').first()

# 2. Replay price action
ohlcv_data = replay_insight(insight, timedelta(hours=4))

# 3. Label outcome
labeler = OutcomeLabeler(insight, '4H')
audit = labeler.create_audit(ohlcv_data)

print(f"Outcome: {audit.outcome}")
print(f"P&L: {audit.pnl_pct}%")

# 4. Run RCA if failed
if audit.outcome == 'failed':
    causes = analyze_audit(audit)
    for cause in causes:
        print(f"  {cause.rank}. {cause.get_cause_display()}: {cause.confidence}%")
        print(f"     {cause.summary}")

# 5. Explain prediction
explanation = explain_insight(insight)
print(f"\nExplanation: {explanation['summary']}")
```

### Batch Processing

```python
from signals.models import Signal
from autopsy.labeler import BatchLabeler
from datetime import datetime, timedelta

# Get recent insights
cutoff = datetime.now() - timedelta(days=7)
insights = Signal.objects.filter(received_at__gte=cutoff)

# Process in batch
batch = BatchLabeler(insights, horizons=['4H', '24H'])

def fetch_ohlcv(insight, horizon):
    # Your OHLCV fetching logic
    return replay_insight(insight, parse_horizon(horizon))

stats = batch.process_all(fetch_ohlcv)
print(batch.get_summary())
```

---

## 🚨 Important Notes

### Data Requirements

AutopsyLoop needs **OHLCV data** to function. Currently two options:

1. **Database Storage** (Preferred):
   - Store historical candles in `MarketData` model
   - Modify `autopsy/replay.py` if your model structure differs

2. **Broker API** (Future):
   - Implement broker integration in `replay.py`
   - Pass `broker_api` parameter to replay functions

### Current Limitations

- **No OHLCV data** = Can't evaluate outcomes (will show "No OHLCV data" warning)
- **Pattern re-detection** requires context_summary or quality_metrics with pattern indicators
- **Regime drift RCA** requires Cognition app with RegimeClassification model
- **News impact RCA** requires ZenNews app with NewsEvent model

### Next Steps

1. **Populate Labeling Rules** for your strategies
2. **Run initial batch audit** on last 30 days
3. **Review results** in admin panel
4. **Set up scheduled audits** (cron/Celery)
5. **Monitor KPIs** and adjust rules

---

## 🐛 Troubleshooting

### "No OHLCV data" error
- Implement OHLCV storage or broker API integration
- Check if `MarketData` model exists

### "No matching rule" warning
- Create LabelingRule for your symbol/strategy
- Create generic rule (blank symbol/strategy = applies to all)

### Audit created but no RCA
- RCA only runs for failed/neutral outcomes
- Check `--skip-rca` flag wasn't used

### Pattern verification always false
- Check insight has `context_summary` or `quality_metrics` with pattern mentions
- Verify OHLCV data quality

---

## 📞 Support

For issues or questions:
1. Check `/admin/autopsy/autopsyjob/` for job errors
2. Review Django logs for detailed error messages
3. Consult `AUTOPSY_LOOP_DOCS.md` for comprehensive documentation

---

**🎉 You're all set! Start auditing your insights and let AutopsyLoop make your platform smarter with every trade.**
