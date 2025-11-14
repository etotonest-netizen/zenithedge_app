# ZenBrain Implementation Roadmap

**Purpose:** Step-by-step guide to build the unified ZenBrain orchestration system  
**Timeline:** 2-3 weeks (40-60 developer hours)  
**Priority:** Strategic enhancement (not blocking current operations)

---

## 🎯 Strategic Decision Required

Before proceeding, you need to decide:

### Option A: Rapid MVP (1 week - 20 hours)
Build minimal viable ZenBrain with:
- Core orchestrator
- Event bus (simple)
- Module registry
- Basic adapters
- Simple insight conversion

**Pros:** Fast, proves concept, minimal risk  
**Cons:** Limited features, manual tuning needed

### Option B: Full Implementation (3 weeks - 60 hours)
Build complete ZenBrain with:
- All adapters
- Full insight engine
- Drift monitoring
- Self-correction
- cPanel optimization

**Pros:** Complete solution, self-aware system  
**Cons:** Time-intensive, complex

### Option C: Incremental Rollout (2 weeks active + ongoing)
Build in phases, deploy progressively:
- Week 1: Core + adapters
- Week 2: Insights + drift
- Week 3+: Self-correction + optimization

**Pros:** Balanced approach, iterative feedback  
**Cons:** Requires multiple deployments

---

## 📋 Detailed Implementation Plan

### Week 1: Foundation (Days 1-7)

#### Day 1-2: ZenBrain Core App

**Tasks:**
1. Create Django app structure
```bash
python manage.py startapp zenbrain
mkdir -p zenbrain/{core,adapters,insight,drift}
```

2. Build core orchestrator (`zenbrain/core/orchestrator.py`)
```python
class ZenBrain:
    def __init__(self):
        self.modules = {}
        self.event_bus = EventBus()
        self.state = StateManager()
    
    def register_module(self, name, adapter):
        """Register a module with ZenBrain"""
        self.modules[name] = adapter
        logger.info(f"Module '{name}' registered")
    
    def get_module(self, name):
        """Get a module by name"""
        return self.modules.get(name)
    
    def publish_event(self, event_type, payload):
        """Publish event to bus"""
        self.event_bus.publish(event_type, payload)
    
    def get_status(self):
        """Get system status"""
        return {
            'status': self.state.get('status'),
            'modules': len(self.modules),
            'uptime': self.state.get('uptime'),
            'health': self.get_health()
        }
```

3. Create models (`zenbrain/models.py`)
```python
class SystemState(models.Model):
    status = models.CharField(max_length=20, default='READY')
    last_heartbeat = models.DateTimeField(auto_now=True)
    active_modules = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)

class ModuleHealth(models.Model):
    module_name = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, default='ACTIVE')
    last_active = models.DateTimeField(auto_now=True)
    error_count = models.IntegerField(default=0)
    metrics = models.JSONField(default=dict)

class Event(models.Model):
    event_type = models.CharField(max_length=50, db_index=True)
    source_module = models.CharField(max_length=50)
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    processed = models.BooleanField(default=False)
```

4. Run migrations
```bash
python manage.py makemigrations zenbrain
python manage.py migrate zenbrain
```

**Deliverable:** Working ZenBrain core with database

---

#### Day 3-4: Module Adapters

**Create Adapter Base Class** (`zenbrain/adapters/base.py`)
```python
class ModuleAdapter(ABC):
    """Base class for all module adapters"""
    
    def __init__(self, zenbrain):
        self.zenbrain = zenbrain
        self.logger = logging.getLogger(self.name)
    
    @property
    @abstractmethod
    def name(self):
        """Module name"""
        pass
    
    @abstractmethod
    def health_check(self):
        """Check module health"""
        pass
    
    def publish(self, event_type, payload):
        """Publish event to ZenBrain"""
        self.zenbrain.publish_event(event_type, payload)
```

**Build Key Adapters:**

1. **ZenDataAdapter** (`zenbrain/adapters/data.py`)
```python
class ZenDataAdapter(ModuleAdapter):
    name = 'data'
    
    def get_latest_bars(self, symbol, timeframe, count=200):
        """Get latest bars from engine.models.MarketBar"""
        from engine.models import MarketBar
        bars = MarketBar.objects.filter(
            symbol=symbol, 
            timeframe=timeframe
        ).order_by('-timestamp')[:count]
        return bars
    
    def health_check(self):
        from engine.models import MarketBar
        count = MarketBar.objects.count()
        return {'status': 'healthy', 'bar_count': count}
```

2. **ZenSignalAdapter** (`zenbrain/adapters/signal.py`)
```python
class ZenSignalAdapter(ModuleAdapter):
    name = 'signal'
    
    def detect_all(self, bars, symbol, timeframe):
        """Run all strategy detectors"""
        from engine.smc import detect_smc
        from engine.strategies import TrendDetector, BreakoutDetector
        
        events = []
        events.extend(detect_smc(bars, symbol, timeframe))
        # Add other detectors...
        
        self.publish('raw_events_detected', {
            'count': len(events),
            'symbol': symbol,
            'timeframe': timeframe
        })
        
        return events
    
    def health_check(self):
        return {'status': 'healthy', 'strategies': 10}
```

3. **ZenMemoryAdapter** (`zenbrain/adapters/memory.py`)
```python
class ZenMemoryAdapter(ModuleAdapter):
    name = 'memory'
    
    def get_concept(self, term):
        """Get trading concept from KB"""
        from knowledge_base.models import Concept
        try:
            concept = Concept.objects.get(term__iexact=term)
            return concept
        except Concept.DoesNotExist:
            return None
    
    def search_concepts(self, query, limit=10):
        """Semantic search in KB"""
        from knowledge_engine.query_engine import query_knowledge_base
        results = query_knowledge_base(query, top_k=limit)
        return results
    
    def health_check(self):
        from knowledge_base.models import Concept
        count = Concept.objects.count()
        return {'status': 'healthy', 'concept_count': count}
```

**Deliverable:** Working adapters for data, signal, memory

---

#### Day 5-7: ZenInsight Engine (MVP)

**Create Insight Models** (`zenbrain/insight/models.py`)
```python
class Insight(models.Model):
    """Generated insight (replaces raw signal)"""
    
    TYPES = [
        ('structural', 'Structural Insight'),
        ('liquidity', 'Liquidity Insight'),
        ('regime', 'Regime Insight'),
        ('timing', 'Timing Insight'),
        ('confluence', 'Confluence Insight'),
    ]
    
    insight_type = models.CharField(max_length=20, choices=TYPES)
    narrative = models.TextField()
    confidence = models.IntegerField()
    uncertainty = models.CharField(max_length=50)
    regime = models.CharField(max_length=50)
    factors = models.JSONField()
    watch_next = models.TextField()
    session_context = models.TextField(blank=True)
    related_concepts = models.JSONField(default=list)
    
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
```

**Build Insight Generator** (`zenbrain/insight/generator.py`)
```python
class InsightGenerator:
    """Converts raw signals/events into insights"""
    
    def __init__(self, memory_adapter):
        self.memory = memory_adapter
        self.templates = self._load_templates()
    
    def generate(self, signal_data, metadata):
        """Generate insight from signal"""
        
        # Determine insight type
        insight_type = self._classify_type(signal_data)
        
        # Build narrative
        narrative = self._build_narrative(signal_data, metadata, insight_type)
        
        # Calculate confidence
        confidence = self._calculate_confidence(signal_data, metadata)
        
        # Determine uncertainty
        uncertainty = self._assess_uncertainty(metadata)
        
        # Detect regime
        regime = metadata.get('regime', 'unknown')
        
        # Extract factors
        factors = self._extract_factors(metadata)
        
        # Generate "watch next"
        watch_next = self._generate_watch_next(signal_data, metadata)
        
        # Add session context
        session_context = self._add_session_context(signal_data)
        
        # Find related concepts
        related = self._find_related_concepts(factors)
        
        return {
            'insight_type': insight_type,
            'narrative': narrative,
            'confidence': confidence,
            'uncertainty': uncertainty,
            'regime': regime,
            'factors': factors,
            'watch_next': watch_next,
            'session_context': session_context,
            'related_concepts': related
        }
    
    def _build_narrative(self, signal, metadata, insight_type):
        """Build natural language narrative"""
        
        # Get concepts from memory
        concepts = []
        for tag in metadata.get('structure_tags', []):
            concept = self.memory.get_concept(tag)
            if concept:
                concepts.append(concept)
        
        # Build narrative using templates + concepts
        if insight_type == 'structural':
            narrative = self._structural_narrative(signal, metadata, concepts)
        elif insight_type == 'liquidity':
            narrative = self._liquidity_narrative(signal, metadata, concepts)
        else:
            narrative = self._default_narrative(signal, metadata)
        
        return narrative
    
    def _structural_narrative(self, signal, metadata, concepts):
        """Generate structural insight narrative"""
        
        # Example advanced narrative
        ob = metadata.get('order_blocks', [])
        fvg = metadata.get('fvgs', [])
        structure = metadata.get('structure', 'unknown')
        
        narrative_parts = []
        
        # Opening context
        narrative_parts.append(f"The market structure is showing {signal['side']} characteristics")
        
        # Add order block context
        if ob:
            ob_concept = self.memory.get_concept('order_block')
            if ob_concept:
                narrative_parts.append(f"with an unmitigated order block at {ob[0]['top']:.5f}")
        
        # Add FVG context
        if fvg:
            narrative_parts.append(f"accompanied by a fair value gap that remains unfilled")
        
        # Add structure context
        if structure:
            narrative_parts.append(f"The recent {structure} formation suggests {self._structure_meaning(structure)}")
        
        # Add regime awareness
        regime = metadata.get('regime', '')
        if 'trending' in regime:
            narrative_parts.append("Current trending regime supports directional moves")
        elif 'ranging' in regime:
            narrative_parts.append("but ranging conditions suggest caution near extremes")
        
        return ". ".join(narrative_parts) + "."
```

**Deliverable:** Working insight generator that converts signals to narratives

---

### Week 2: Intelligence Enhancement (Days 8-14)

#### Day 8-9: Event Bus Implementation

**Create Event Bus** (`zenbrain/core/event_bus.py`)
```python
class EventBus:
    """Internal event bus for module communication"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.logger = logging.getLogger('zenbrain.eventbus')
    
    def subscribe(self, event_type, callback):
        """Subscribe to event type"""
        self.subscribers[event_type].append(callback)
        self.logger.info(f"Subscribed to {event_type}")
    
    def publish(self, event_type, payload):
        """Publish event to subscribers"""
        from zenbrain.models import Event
        
        # Log to database
        Event.objects.create(
            event_type=event_type,
            source_module=payload.get('source', 'unknown'),
            payload=payload
        )
        
        # Notify subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(payload)
            except Exception as e:
                self.logger.error(f"Event handler failed: {e}")
    
    def get_recent_events(self, event_type=None, limit=100):
        """Get recent events"""
        from zenbrain.models import Event
        qs = Event.objects.all()
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs.order_by('-timestamp')[:limit]
```

**Connect Modules:**
```python
# In startup script
brain = ZenBrain()

# Subscribe to events
brain.event_bus.subscribe('new_bar', lambda p: brain.signal.detect_all(p['bars']))
brain.event_bus.subscribe('raw_events_detected', lambda p: brain.insight.generate(p['events']))
brain.event_bus.subscribe('insight_generated', lambda p: brain.ticker.notify(p['insight']))
```

---

#### Day 10-11: ZenDrift Monitor

**Create Drift Detector** (`zenbrain/drift/detector.py`)
```python
class DriftMonitor:
    """Detects system drift and performance degradation"""
    
    def check_signal_frequency(self):
        """Check if signal frequency has changed"""
        from zenbrain.insight.models import Insight
        
        # Get last 7 days average
        week_ago = timezone.now() - timedelta(days=7)
        recent = Insight.objects.filter(timestamp__gte=week_ago).count()
        avg_per_day = recent / 7
        
        # Get today's count
        today = timezone.now().date()
        today_count = Insight.objects.filter(timestamp__date=today).count()
        
        # Check drift
        if today_count < avg_per_day * 0.5:
            self._alert_drift('signal_frequency', avg_per_day, today_count)
    
    def check_confidence_drift(self):
        """Check if average confidence is dropping"""
        from zenbrain.insight.models import Insight
        
        week_ago = timezone.now() - timedelta(days=7)
        recent = Insight.objects.filter(timestamp__gte=week_ago)
        
        if recent.count() < 10:
            return  # Not enough data
        
        avg_confidence = recent.aggregate(Avg('confidence'))['confidence__avg']
        
        # Get last 24h average
        yesterday = timezone.now() - timedelta(days=1)
        recent_24h = Insight.objects.filter(timestamp__gte=yesterday)
        avg_24h = recent_24h.aggregate(Avg('confidence'))['confidence__avg']
        
        # Check drift (>10% drop)
        if avg_24h < avg_confidence * 0.9:
            self._alert_drift('confidence', avg_confidence, avg_24h)
    
    def run_health_check(self):
        """Run full system health check"""
        issues = []
        
        # Check each module
        for name, module in self.zenbrain.modules.items():
            health = module.health_check()
            if health.get('status') != 'healthy':
                issues.append(f"{name}: {health}")
        
        # Check drift
        self.check_signal_frequency()
        self.check_confidence_drift()
        
        return {
            'status': 'READY' if not issues else 'DEGRADED',
            'issues': issues,
            'timestamp': timezone.now()
        }
```

**Create Management Command** (`zenbrain/management/commands/zenbrain_healthcheck.py`)
```bash
# Run via cron every hour
*/60 * * * * cd ~/etotonest.com && python manage.py zenbrain_healthcheck
```

---

#### Day 12-14: Self-Correction Loop

**Create Self-Correction Engine** (`zenbrain/core/self_correction.py`)
```python
class SelfCorrectionEngine:
    """Analyzes failures and adjusts system parameters"""
    
    def analyze_outcomes(self):
        """Analyze autopsy outcomes and detect patterns"""
        from autopsy.models import InsightAudit
        
        # Get recent failures
        week_ago = timezone.now() - timedelta(days=7)
        audits = InsightAudit.objects.filter(
            created_at__gte=week_ago,
            outcome='fail'
        )
        
        # Analyze root causes
        causes = defaultdict(int)
        for audit in audits:
            for cause in audit.root_causes.all():
                causes[cause.category] += 1
        
        # Identify top issues
        top_issues = sorted(causes.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Apply corrections
        for issue, count in top_issues:
            self._apply_correction(issue, count)
    
    def _apply_correction(self, issue, frequency):
        """Apply correction based on issue type"""
        
        if issue == 'volatility_threshold':
            # Tighten volatility threshold
            self._update_threshold('volatility', adjustment=-0.0005)
            self._log_correction(
                issue='Volatility threshold too loose',
                action='Reduced threshold by 0.0005',
                expected='Fewer false positives in low-vol periods'
            )
        
        elif issue == 'order_block_confirmation':
            # Add volume confirmation requirement
            self._update_rule('order_block', 'require_volume_confirmation', True)
            self._log_correction(
                issue='Order blocks without volume confirmation',
                action='Added volume confirmation requirement',
                expected='Higher quality OB signals'
            )
    
    def generate_self_report(self):
        """Generate daily self-diagnostic report"""
        from zenbrain.models import SelfCorrection
        
        yesterday = timezone.now() - timedelta(days=1)
        corrections = SelfCorrection.objects.filter(timestamp__gte=yesterday)
        
        report = f"""
ZenBrain Self-Diagnostic Report
Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Performance Summary:
- Insights Generated: {self._count_insights()}
- Accuracy: {self._calculate_accuracy()}%
- Corrections Applied: {corrections.count()}

Issues Detected:
{self._format_issues()}

Actions Taken:
{self._format_corrections(corrections)}

System Status: {self._get_status()}
Next Review: {(timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}
        """
        
        return report
```

**Deliverable:** Self-aware system that learns from mistakes

---

### Week 3: Optimization & Polish (Days 15-21)

#### Day 15-16: cPanel Optimization

**Auto-detect Environment** (`zenbrain/core/environment.py`)
```python
def detect_environment():
    """Detect if running on cPanel"""
    indicators = [
        os.path.exists('/home/equabish'),
        'cpanel' in os.uname().nodename.lower(),
        os.path.exists('/usr/local/cpanel')
    ]
    return 'cpanel' if any(indicators) else 'development'

def configure_for_cpanel():
    """Optimize settings for cPanel"""
    settings.DATABASES['default']['OPTIONS'] = {
        'timeout': 20,
        'check_same_thread': False
    }
    settings.CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
```

---

#### Day 17-19: Admin Dashboard

**Create Admin Views** (`zenbrain/admin.py`)
```python
@admin.register(SystemState)
class SystemStateAdmin(admin.ModelAdmin):
    list_display = ['status', 'last_heartbeat', 'module_count', 'uptime']
    
    def module_count(self, obj):
        return len(obj.active_modules)
    
    def uptime(self, obj):
        return obj.metrics.get('uptime', 'N/A')

@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ['insight_type', 'confidence', 'regime', 'timestamp']
    list_filter = ['insight_type', 'regime']
    search_fields = ['narrative', 'watch_next']
    date_hierarchy = 'timestamp'
```

---

#### Day 20-21: Testing & Documentation

**Write Tests** (`zenbrain/tests.py`)
```python
class ZenBrainTests(TestCase):
    def test_orchestrator_initialization(self):
        brain = ZenBrain()
        self.assertIsNotNone(brain.event_bus)
    
    def test_module_registration(self):
        brain = ZenBrain()
        adapter = ZenDataAdapter(brain)
        brain.register_module('data', adapter)
        self.assertEqual(brain.get_module('data'), adapter)
    
    def test_insight_generation(self):
        generator = InsightGenerator(memory_adapter)
        signal = {'side': 'long', 'price': 1.0850}
        metadata = {'order_blocks': [{'top': 1.0860}]}
        insight = generator.generate(signal, metadata)
        self.assertIn('narrative', insight)
        self.assertGreater(insight['confidence'], 0)
```

**Run Full Test Suite:**
```bash
python manage.py test zenbrain
```

---

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Database migrations created
- [ ] Environment detection working
- [ ] cPanel optimizations applied
- [ ] Admin interface functional
- [ ] Documentation complete

### Deployment Steps
1. Upload `zenbrain/` app to server
2. Run migrations: `python manage.py migrate zenbrain`
3. Initialize ZenBrain: `python manage.py zenbrain_init`
4. Register modules: `python manage.py zenbrain_register_modules`
5. Start health monitoring: Add cron job
6. Test API endpoints
7. Monitor logs for 24 hours

### Post-Deployment
- [ ] Verify event bus working
- [ ] Verify insights generating
- [ ] Verify drift monitoring active
- [ ] Verify self-corrections logging
- [ ] Verify admin dashboard accessible

---

## 📊 Success Metrics

After 1 week of operation:
- ✅ 100+ insights generated
- ✅ Event bus processing < 100ms
- ✅ No module failures
- ✅ Drift checks running hourly
- ✅ At least 1 self-correction logged

After 1 month:
- ✅ 1000+ insights generated
- ✅ Accuracy > 70%
- ✅ System uptime > 99%
- ✅ User engagement +30%
- ✅ Narrative uniqueness > 95%

---

## ⚠️ Important Notes

1. **Don't Break Existing System:** ZenBrain wraps existing modules, doesn't replace them
2. **Incremental Rollout:** Deploy in phases, test thoroughly
3. **Monitoring:** Watch logs closely for first week
4. **Fallback:** Keep existing direct access to modules during transition
5. **Documentation:** Update user docs once stable

---

**Ready to start?** Choose your implementation option (A, B, or C) and we'll begin!
