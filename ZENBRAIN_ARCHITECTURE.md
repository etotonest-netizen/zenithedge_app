# ZenBrain - Master Orchestration System

**Version:** 1.0.0-alpha  
**Status:** Architecture Defined, Implementation Pending  
**Purpose:** Unified coordinator for all ZenithEdge subsystems

---

## 🧠 System Architecture

### Core Philosophy

ZenBrain is the **central nervous system** of ZenithEdge. It doesn't replace existing modules - it **orchestrates, monitors, and optimizes** them.

### Architectural Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                         ZenBrain                             │
│  (Master Orchestrator, Event Bus, State Manager)            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   ZenData    │───▶│  ZenSignal   │───▶│  ZenInsight  │
│ (Market Data)│    │ (Detectors)  │    │ (Intelligence)│
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        │                   ▼                   ▼
        │           ┌──────────────┐    ┌──────────────┐
        │           │ ZenAutopsy   │    │  ZenVision   │
        │           │ (Outcomes)   │    │  (Visuals)   │
        │           └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────┐
│              ZenMemory (Knowledge Base)               │
│         (Vector embeddings, Trading Dictionary)       │
└──────────────────────────────────────────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  ZenMentor   │    │   ZenRisk    │    │  ZenTicker   │
│ (Education)  │    │ (Prop Coach) │    │ (Alerts)     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   ZenDrift   │
                    │(Health Check)│
                    └──────────────┘
```

---

## 📋 Module Mapping (Existing → ZenBrain)

### Current System → ZenBrain Unification

| ZenBrain Module | Current Implementation | Status | Integration Needed |
|----------------|------------------------|--------|-------------------|
| **ZenBrain Core** | ❌ Not exists | NEW | Create orchestrator |
| **ZenData** | `engine/` + `marketdata/` | ✅ 90% | Add unified API |
| **ZenSignal** | `engine/strategies.py` + `engine/smc.py` | ✅ 100% | Wrapper needed |
| **ZenInsight** | `signals/` (raw signals only) | ⚠️ 40% | Convert to insights |
| **ZenAutopsy** | `autopsy/` | ✅ 100% | Connect to event bus |
| **ZenMemory** | `knowledge_base/` + `knowledge_engine/` | ✅ 75% | Add embeddings API |
| **ZenMentor** | `zenithmentor/` | ✅ 100% | Add scenario engine |
| **ZenRisk** | `propcoach/` | ✅ 100% | Connect to insights |
| **ZenTicker** | `notifications/` | ✅ 100% | Add priority routing |
| **ZenVision** | `engine/visuals.py` | ✅ 80% | Add insight cards |
| **ZenBacktest** | `analytics/` + `engine/backtest.py` | ✅ 100% | Merge APIs |
| **ZenDrift** | ❌ Not exists | NEW | Create monitor |

---

## 🏗️ Implementation Phases

### Phase 1: ZenBrain Core (Foundation) - 2 days
**Priority:** 🔴 CRITICAL

**Deliverables:**
1. `zenbrain/` Django app
2. `zenbrain/core.py` - Master orchestrator class
3. `zenbrain/event_bus.py` - Internal event system
4. `zenbrain/state.py` - Global state manager
5. `zenbrain/registry.py` - Module registry
6. `zenbrain/models.py` - SystemState, ModuleHealth, EventLog

**Components:**
```python
class ZenBrain:
    - modules: Dict[str, Module]
    - event_bus: EventBus
    - state: StateManager
    - health: HealthMonitor
    
    def register_module(name, module)
    def publish_event(event)
    def get_module(name)
    def get_state()
    def run_diagnostic()
```

### Phase 2: Module Unification Layer - 3 days
**Priority:** 🔴 CRITICAL

**Create Unified APIs:**
1. `zenbrain/adapters/data_adapter.py` - Wraps `engine/` + `marketdata/`
2. `zenbrain/adapters/signal_adapter.py` - Wraps `engine/strategies.py`
3. `zenbrain/adapters/insight_adapter.py` - NEW (converts signals → insights)
4. `zenbrain/adapters/memory_adapter.py` - Wraps `knowledge_base/`
5. `zenbrain/adapters/autopsy_adapter.py` - Wraps `autopsy/`

**Benefits:**
- Uniform API across all modules
- Easy to swap implementations
- Centralized error handling
- Consistent logging

### Phase 3: ZenInsight Engine - 4 days
**Priority:** 🔴 CRITICAL

**Build Intelligence Layer:**
1. `zenbrain/insight/` - New app
2. `zenbrain/insight/generator.py` - Converts raw signals to insights
3. `zenbrain/insight/formatter.py` - Natural language generation
4. `zenbrain/insight/scorer.py` - Confidence + uncertainty
5. `zenbrain/insight/models.py` - Insight, InsightType, Context

**Types:**
- Structural Insight (OB, FVG, CHoCH)
- Liquidity Insight (sweeps, pools)
- Regime Insight (trend, range, volatile)
- Timing Insight (killzones, sessions)
- Confluence Insight (multi-factor)

**Example Output:**
```json
{
  "type": "structural_insight",
  "narrative": "Price is approaching a premium discount zone near 1.0850 where a previously formed order block sits. This area has absorbed selling pressure in the past, suggesting potential bullish interest. Current regime is trending bullish with increasing momentum.",
  "confidence": 82,
  "uncertainty": "Medium - depends on session volume",
  "regime": "trending_bullish",
  "factors": ["order_block", "premium_zone", "momentum_increase"],
  "watch_next": "Look for wick rejection at 1.0850 or sweep below 1.0840",
  "session_sensitivity": "NY open (2 hours away) may trigger liquidity sweep",
  "related_concepts": ["order_block", "premium_discount", "liquidity"]
}
```

### Phase 4: ZenDrift Monitor - 2 days
**Priority:** 🟡 HIGH

**Build Self-Awareness:**
1. `zenbrain/drift/` - New app
2. `zenbrain/drift/detector.py` - Distribution monitoring
3. `zenbrain/drift/health.py` - System health checks
4. `zenbrain/drift/repair.py` - Auto-healing logic
5. `zenbrain/drift/models.py` - DriftLog, HealthStatus

**Monitors:**
- Signal frequency drift
- Confidence score drift
- Outcome accuracy drift
- Latency drift
- Data quality drift

**Actions:**
- Alert ZenBrain
- Trigger recalibration
- Update thresholds
- Disable degraded modules

### Phase 5: Event Bus Integration - 2 days
**Priority:** 🟡 HIGH

**Connect Everything:**
1. All modules publish to event bus
2. ZenBrain routes events
3. Modules subscribe to relevant events
4. Async processing with Celery

**Event Flow:**
```
ZenData → "new_bar" → ZenSignal
ZenSignal → "raw_event" → ZenInsight
ZenInsight → "insight_generated" → ZenTicker + ZenVision
ZenAutopsy → "outcome_evaluated" → ZenDrift → ZenBrain
ZenDrift → "drift_detected" → ZenBrain → trigger_recalibration
```

### Phase 6: Insight Enhancement - 3 days
**Priority:** 🟡 HIGH

**Enhance Natural Language:**
1. Integrate with ZenMemory (10k+ dictionary terms)
2. Add linguistic variation engine
3. Add session context
4. Add macro sentiment (from internal KB)
5. Add regime-aware wording

**Before:** "Bullish signal at 1.0850"

**After:** "The market structure is exhibiting bullish characteristics near 1.0850, where an unmitigated order block from yesterday's session remains active. Given the current trending regime and approaching NY open killzone, institutional flows may test this area before continuing higher. Watch for wick rejections or displacement candles as confirmation."

### Phase 7: Self-Correction Loop - 2 days
**Priority:** 🟢 MEDIUM

**Build Learning System:**
1. ZenAutopsy feeds outcomes to ZenBrain
2. ZenBrain analyzes patterns
3. Updates internal rules
4. Adjusts confidence thresholds
5. Logs self-corrections

**Example Self-Journal:**
```
2025-11-14 18:00 UTC
ZenBrain Self-Diagnostic Report

Yesterday's Performance:
- 47 insights generated
- 12 resolved outcomes (6 correct, 4 wrong, 2 partial)
- Accuracy: 50% (below 70% target)

Root Causes Identified:
1. Volatility threshold too loose (6 false positives in low-vol periods)
2. Order block detection missing volume confirmation (4 failures)
3. Killzone timing off by 15 minutes (2 premature entries)

Actions Taken:
- Updated volatility_threshold: 0.005 → 0.0032
- Added volume_confirmation to OB detection
- Adjusted killzone_window: [-5, +60] → [-15, +45]
- Reduced confidence for low-volume OBs by 10%

Expected Improvement: +15% accuracy
Next Review: 2025-11-15 18:00 UTC
```

### Phase 8: cPanel Optimization - 1 day
**Priority:** 🟢 MEDIUM

**Optimize for Shared Hosting:**
1. Auto-detect cPanel environment
2. Use SQLite for events (not Redis)
3. Compress embeddings
4. Limit concurrent workers
5. Use cron instead of Celery beat
6. Optimize memory usage
7. Add graceful degradation

---

## 🔗 API Endpoints (zenbrain/)

### Admin Endpoints
- `GET /zenbrain/status/` - System health dashboard
- `GET /zenbrain/modules/` - List all modules + status
- `GET /zenbrain/events/` - Recent event log
- `POST /zenbrain/trigger/<module>/` - Manually trigger module

### Public Endpoints
- `GET /zenbrain/api/insights/latest/` - Latest insights
- `GET /zenbrain/api/insights/<id>/` - Specific insight
- `GET /zenbrain/api/health/` - Public health check
- `GET /zenbrain/api/drift/` - Drift status

### Internal Endpoints (Module Communication)
- `POST /zenbrain/internal/publish/` - Publish event
- `GET /zenbrain/internal/state/` - Get global state
- `POST /zenbrain/internal/register/` - Register module

---

## 📊 Database Schema

### New Models

```python
# zenbrain/models.py

class SystemState(models.Model):
    """Global system state"""
    status = models.CharField(max_length=20)  # READY, DEGRADED, CRITICAL
    last_heartbeat = models.DateTimeField()
    active_modules = models.JSONField()
    metrics = models.JSONField()

class ModuleHealth(models.Model):
    """Per-module health tracking"""
    module_name = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    last_active = models.DateTimeField()
    error_count = models.IntegerField(default=0)
    metrics = models.JSONField()

class Event(models.Model):
    """Event bus log"""
    event_type = models.CharField(max_length=50)
    source_module = models.CharField(max_length=50)
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

class Insight(models.Model):
    """Generated insights (replaces raw signals)"""
    insight_type = models.CharField(max_length=50)
    narrative = models.TextField()
    confidence = models.IntegerField()
    uncertainty = models.CharField(max_length=20)
    regime = models.CharField(max_length=50)
    factors = models.JSONField()
    watch_next = models.TextField()
    session_context = models.TextField()
    related_concepts = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class DriftLog(models.Model):
    """Drift detection log"""
    detected_at = models.DateTimeField(auto_now_add=True)
    metric_name = models.CharField(max_length=50)
    old_value = models.FloatField()
    new_value = models.FloatField()
    drift_magnitude = models.FloatField()
    action_taken = models.TextField()

class SelfCorrection(models.Model):
    """System self-correction log"""
    timestamp = models.DateTimeField(auto_now_add=True)
    issue_detected = models.TextField()
    root_cause = models.TextField()
    action_taken = models.TextField()
    expected_improvement = models.TextField()
```

---

## 🚀 Quick Start (After Implementation)

### Initialize ZenBrain

```python
# In Django shell or startup script
from zenbrain.core import ZenBrain

# Initialize
brain = ZenBrain.initialize()

# Register all modules
brain.register_module('data', ZenDataAdapter())
brain.register_module('signal', ZenSignalAdapter())
brain.register_module('insight', ZenInsightEngine())
brain.register_module('autopsy', ZenAutopsyAdapter())
brain.register_module('memory', ZenMemoryAdapter())
brain.register_module('mentor', ZenMentorAdapter())
brain.register_module('risk', ZenRiskAdapter())
brain.register_module('ticker', ZenTickerAdapter())
brain.register_module('vision', ZenVisionAdapter())
brain.register_module('drift', ZenDriftMonitor())

# Start event bus
brain.start()

# Check status
status = brain.get_status()
print(status)
```

### Usage Example

```python
# Unified API (all modules accessed through ZenBrain)

# Get latest market data
bars = brain.data.get_latest_bars('EURUSD', '1H', count=200)

# Detect raw events
events = brain.signal.detect_all(bars, 'EURUSD', '1H')

# Convert to insights
insights = brain.insight.generate(events)

# Send to user
brain.ticker.notify(insights, priority='high')

# Generate visuals
visuals = brain.vision.create_cards(insights)

# Log for autopsy
brain.autopsy.track(insights)

# Check system health
health = brain.drift.check_health()
if health.status == 'DEGRADED':
    brain.trigger_self_healing()
```

---

## 📈 Success Metrics

### System Performance
- Event processing latency < 100ms
- Module failure rate < 1%
- Uptime > 99.5%
- Memory usage < 500MB (cPanel)

### Intelligence Quality
- Insight accuracy > 70%
- Narrative uniqueness > 95%
- User engagement +50%
- Self-correction frequency > 1/day

### User Experience
- Time to insight < 5 seconds
- Alert relevance > 80%
- Education completion rate +30%
- Prop simulation pass rate +25%

---

## ⚠️ Implementation Priorities

### Phase 1 (Core Infrastructure) - MUST DO
1. ✅ ZenBrain core orchestrator
2. ✅ Event bus
3. ✅ Module adapters
4. ✅ Basic health monitoring

### Phase 2 (Intelligence Layer) - MUST DO
1. ✅ ZenInsight engine
2. ✅ Natural language generation
3. ✅ Dictionary integration
4. ✅ Insight scoring

### Phase 3 (Self-Awareness) - SHOULD DO
1. ⏳ ZenDrift monitoring
2. ⏳ Self-correction loop
3. ⏳ Learning system
4. ⏳ Auto-healing

### Phase 4 (Optimization) - NICE TO HAVE
1. ⏳ cPanel tuning
2. ⏳ Advanced caching
3. ⏳ Compression
4. ⏳ Load balancing

---

## 🎯 Next Steps

### Immediate Actions (This Week)

**Day 1-2: Create ZenBrain Core**
- Create `zenbrain/` Django app
- Build orchestrator class
- Build event bus
- Create database models
- Write tests

**Day 3-4: Build Adapters**
- Wrap existing modules
- Create unified APIs
- Add error handling
- Add logging

**Day 5-7: Build ZenInsight**
- Create insight generator
- Add NLG engine
- Integrate dictionary
- Test with real signals

### Medium-term (Next 2 Weeks)
- Build ZenDrift monitor
- Add self-correction
- Enhance visual insights
- Optimize for cPanel

### Long-term (Next Month)
- Advanced learning
- Multi-agent coordination
- Predictive health
- Auto-scaling

---

## 🔚 Conclusion

ZenBrain is the **missing orchestration layer** that will transform ZenithEdge from a collection of powerful modules into a **unified, self-aware trading intelligence system**.

**Current Status:** Architecture complete, ready for implementation  
**Estimated Time:** 2-3 weeks for full implementation  
**Developer Effort:** 40-60 hours  
**Impact:** Transforms system from modular to unified

---

**Document Version:** 1.0.0  
**Last Updated:** November 14, 2025  
**Status:** ARCHITECTURE DEFINED - AWAITING IMPLEMENTATION
