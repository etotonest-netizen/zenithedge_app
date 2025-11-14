# Knowledge Base - Quick Reference Card

## 🚀 Quick Start (30 Minutes)

```bash
# 1. Install dependencies (5 min)
pip install -r requirements_kb.txt
python -m spacy download en_core_web_sm

# 2. Run migrations (1 min)
python manage.py makemigrations knowledge_base
python manage.py migrate

# 3. Initialize sources (1 min)
python manage.py init_kb_sources

# 4. First crawl - Investopedia (15-20 min)
python manage.py crawl_knowledge --source investopedia --max-pages 50 --rebuild-index

# 5. Test search (2 min)
python manage.py test_kb_search "order block" --k 5
```

---

## 📚 Common Commands

### Crawling

```bash
# Crawl single source
python manage.py crawl_knowledge --source investopedia --max-pages 50 --rebuild-index

# Crawl all sources
python manage.py crawl_knowledge --all --max-pages 100 --rebuild-index

# Daily incremental (20 pages)
python manage.py crawl_knowledge --all --max-pages 20 --rebuild-index
```

### Search & Testing

```bash
# Basic search
python manage.py test_kb_search "order block" --k 5

# With filters
python manage.py test_kb_search "liquidity sweep" --k 3 --category smc --asset-class forex

# Rebuild index
python manage.py rebuild_kb_index --batch-size 100
```

### Maintenance

```bash
# Django shell - Check stats
python manage.py shell -c "
from knowledge_base.models import KnowledgeEntry, Source
print(f'Entries: {KnowledgeEntry.objects.count()}')
print(f'Sources: {Source.objects.filter(active=True).count()}')
"

# Clear old cache
python manage.py shell -c "
from knowledge_base.kb_search import KnowledgeBaseSearch
kb = KnowledgeBaseSearch()
print(f'Cleared: {kb.clear_cache(older_than_hours=48)} entries')
"
```

---

## 🔧 Integration Code

### Enhanced Narrative Generation

```python
from knowledge_base.kb_contextualizer import KBContextualizer

# Initialize
kb_ctx = KBContextualizer()

# Generate enhanced narrative
enhanced_narrative, kb_trace = kb_ctx.generate_kb_enhanced_narrative(
    signal_data={
        'symbol': 'EURUSD',
        'side': 'buy',
        'strategy': 'smc',
        'regime': 'breakout',
        'price': 1.0850,
        'sl': 1.0820,
        'tp': 1.0910
    },
    validation_result={
        'truth_index': 83,
        'status': 'approved',
        'breakdown': {}
    },
    base_narrative="EURUSD setup detected — 83/100 confidence (SMC)"
)

# Save with provenance
signal.narrative = enhanced_narrative
signal.kb_trace = kb_trace  # For explainability
signal.save()
```

### Direct KB Search

```python
from knowledge_base.kb_search import KnowledgeBaseSearch

kb = KnowledgeBaseSearch()

# Search
results = kb.search(
    query="order block",
    k=10,
    category='smc',
    asset_class='forex',
    min_quality=0.5,
    use_cache=True,
    symbol='EURUSD'
)

# Use results
for result in results:
    entry = result['entry']
    score = result['score']
    print(f"{entry.term}: {entry.summary} (score: {score:.3f})")
```

---

## 📊 Admin Shortcuts

**URL:** `http://localhost:8000/admin/knowledge_base/`

### Quick Links

- **Sources:** `/admin/knowledge_base/source/`
- **Entries:** `/admin/knowledge_base/knowledgeentry/`
- **Crawl Logs:** `/admin/knowledge_base/crawllog/`
- **Cache:** `/admin/knowledge_base/querycache/`

### Filters

**Knowledge Entries:**
- Category: SMC, ICT, TA, Risk, etc.
- Quality: ≥0.8 (high), ≥0.6 (medium), <0.6 (low)
- Verified: Yes/No
- Source Trust: High/Medium/Low

**Actions:**
- ✅ Verify entries (bulk)
- ✅ Activate/Deactivate
- ✅ Clear expired cache

---

## 🕐 Scheduled Tasks (Cron)

```bash
# Edit crontab
crontab -e

# Daily incremental crawl (2 AM)
0 2 * * * cd /path/to/zenithedge && python manage.py crawl_knowledge --all --max-pages 20 --rebuild-index >> /var/log/kb_crawl.log 2>&1

# Weekly full crawl (Sunday 3 AM)
0 3 * * 0 cd /path/to/zenithedge && python manage.py crawl_knowledge --all --max-pages 100 --rebuild-index >> /var/log/kb_crawl_full.log 2>&1

# Daily cache cleanup (4 AM)
0 4 * * * cd /path/to/zenithedge && python manage.py shell -c "from knowledge_base.kb_search import KnowledgeBaseSearch; kb = KnowledgeBaseSearch(); kb.clear_cache(older_than_hours=48)" >> /var/log/kb_cache.log 2>&1
```

---

## 🐛 Troubleshooting

### Issue: "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### Issue: "FAISS import error"
```bash
pip install faiss-cpu  # or faiss-gpu if CUDA available
```

### Issue: "No results from search"
```bash
# Rebuild index
python manage.py rebuild_kb_index

# Check entries exist
python manage.py shell -c "from knowledge_base.models import KnowledgeEntry; print(KnowledgeEntry.objects.count())"
```

### Issue: "Slow crawling"
- Check `rate_limit_seconds` in Source admin (default: 2-3s)
- Verify network latency: `ping investopedia.com`
- Review robots.txt crawl-delay

### Issue: "Low quality scores"
- Filter by source trust level (high only)
- Manually verify entries in admin
- Adjust quality thresholds in `normalizer.py`

---

## 📈 Monitoring

```bash
# Check crawl status
tail -f /var/log/kb_crawl.log

# KB statistics
python manage.py shell << EOF
from knowledge_base.models import *
from django.db.models import Avg, Count

print(f"Total entries: {KnowledgeEntry.objects.count()}")
print(f"Active entries: {KnowledgeEntry.objects.filter(is_active=True).count()}")
print(f"Verified entries: {KnowledgeEntry.objects.filter(is_verified=True).count()}")
print(f"Avg quality: {KnowledgeEntry.objects.aggregate(Avg('quality_score'))['quality_score__avg']:.2f}")
print(f"\nBy category:")
for cat in KnowledgeEntry.objects.values('category').annotate(count=Count('id')):
    print(f"  {cat['category']}: {cat['count']}")
print(f"\nRecent crawls:")
for log in CrawlLog.objects.order_by('-started_at')[:5]:
    print(f"  {log.source.name}: {log.status} ({log.entries_created} created)")
EOF
```

---

## 🎯 Success Metrics

**Target after first week:**
- [ ] ≥300 KB entries
- [ ] 7 sources crawled
- [ ] Avg quality score ≥0.7
- [ ] Cache hit rate ≥60%
- [ ] <200ms cached query latency

**Check metrics:**
```python
from knowledge_base.models import *
from knowledge_base.kb_search import KnowledgeBaseSearch

# Entry count
print(f"Entries: {KnowledgeEntry.objects.count()}/300")

# Average quality
avg_q = KnowledgeEntry.objects.aggregate(Avg('quality_score'))['quality_score__avg']
print(f"Avg quality: {avg_q:.2f}/1.0")

# Sources crawled
sources = Source.objects.filter(last_crawled__isnull=False).count()
print(f"Sources crawled: {sources}/7")

# Cache stats
cache_total = QueryCache.objects.count()
recent_hits = QueryCache.objects.filter(hit_count__gt=1).count()
print(f"Cache hit rate: {recent_hits/cache_total*100:.1f}%")
```

---

## 📝 Daily Checklist

**Morning (5 min):**
- [ ] Check overnight crawl logs
- [ ] Review new entries (quality filter ≥0.7)
- [ ] Verify 5-10 random entries

**Weekly (30 min):**
- [ ] Run full crawl (all sources, 100 pages)
- [ ] Review crawl statistics
- [ ] Manually add high-value entries
- [ ] Curate concept relationships
- [ ] Clear old cache (>48h)

**Monthly (1 hour):**
- [ ] Review KB usage analytics
- [ ] Update source configurations
- [ ] Fine-tune quality thresholds
- [ ] Create KB snapshot
- [ ] Review narrative quality (sample 20 signals)

---

## 🚨 Emergency Procedures

### KB Corruption
```bash
# Backup current state
python manage.py dumpdata knowledge_base > kb_backup_$(date +%Y%m%d).json

# Restore from snapshot
python manage.py loaddata kb_backup_20250115.json

# Rebuild index
python manage.py rebuild_kb_index
```

### FAISS Index Corruption
```bash
# Delete index
rm -f data/knowledge_base/faiss_index.bin*

# Rebuild
python manage.py rebuild_kb_index
```

### Rate Limit Exceeded
```bash
# Increase delay in admin: /admin/knowledge_base/source/
# Or via shell:
from knowledge_base.models import Source
Source.objects.filter(domain='investopedia.com').update(rate_limit_seconds=5)
```

---

## 📞 Support Resources

- **Full Guide:** `KNOWLEDGE_BASE_GUIDE.md`
- **Schema:** `kb_schema.json`
- **Deployment:** `KB_DEPLOYMENT_CHECKLIST.md`
- **Summary:** `KB_IMPLEMENTATION_SUMMARY.md`
- **Tests:** `tests/test_knowledge_base.py`

---

**Quick Help:** For most issues, rebuild the index:
```bash
python manage.py rebuild_kb_index
```
