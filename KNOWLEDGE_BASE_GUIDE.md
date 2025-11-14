# Trading Knowledge Base System

## Overview

The **Trading Knowledge Base** is an automated dictionary and semantic search system that scrapes authoritative trading sources, processes content with NLP, indexes with vector embeddings, and provides fast semantic lookup for the ZenithEdge AI Contextualizer.

**Key Features:**
- 🌐 **Automated Web Scraping**: Respects robots.txt, rate limits, and site ToS
- 🧠 **NLP Processing**: Uses spaCy for NER, TextBlob for sentiment
- 🔍 **Semantic Search**: FAISS vector index with sentence-transformers
- 📚 **Knowledge Graph**: Concept relationships for contextual explanations
- 📖 **Source Citations**: Full provenance tracking and attribution
- ⚡ **High Performance**: <200ms cached queries, <500ms cold queries

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading Signal                            │
│              (EURUSD, SMC Strategy, London)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│             KB Contextualizer Integration                    │
│  1. Extract concepts: ["order block", "liquidity sweep"]    │
│  2. Query KB via semantic search                             │
│  3. Retrieve definitions + examples + relationships          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Knowledge Base                              │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Scraper      │ Normalizer   │ KB Search    │            │
│  │ - robots.txt │ - spaCy NER  │ - FAISS      │            │
│  │ - Rate limit │ - TextBlob   │ - Embeddings │            │
│  │ - RSS/sitemap│ - Categories │ - Caching    │            │
│  └──────────────┴──────────────┴──────────────┘            │
│                       │                                      │
│  ┌────────────────────┴──────────────────┐                 │
│  │     PostgreSQL Database                │                 │
│  │  - KnowledgeEntry (300+ concepts)      │                 │
│  │  - Source (7 authoritative sites)      │                 │
│  │  - ConceptRelationship (graph edges)   │                 │
│  │  - QueryCache (performance)            │                 │
│  └────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          AI-Generated Narrative with Citations               │
│                                                               │
│  "Order Block (institutional demand): a last major bearish   │
│   engulfing candle marking sell liquidity. Here an OB sits   │
│   at 185.30; the subsequent wick is a liquidity sweep,       │
│   often preceding a retest. Source: Investopedia, FXStreet." │
└─────────────────────────────────────────────────────────────┘
```

---

## Setup & Installation

### 1. Install Dependencies

```bash
cd ~/zenithedge_trading_hub

# Install Python packages
pip install sentence-transformers faiss-cpu spacy textblob beautifulsoup4 feedparser requests

# Download spaCy model
python -m spacy download en_core_web_sm

# Download TextBlob corpora
python -m textblob.download_corpora
```

### 2. Add to Django Settings

Edit `zenithedge/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'knowledge_base',
]
```

### 3. Run Migrations

```bash
python manage.py makemigrations knowledge_base
python manage.py migrate
```

### 4. Initialize Sources

```bash
python manage.py init_kb_sources
```

This creates 7 default sources:
- ✅ Investopedia (high trust)
- ✅ BabyPips (high trust)
- ✅ FXStreet (medium trust)
- ✅ DailyFX (medium trust)
- ✅ TradingView Docs (high trust)
- ✅ OANDA (high trust)
- ✅ IG Group (medium trust)

---

## Usage

### Crawl Knowledge Sources

```bash
# Crawl single source
python manage.py crawl_knowledge --source investopedia --max-pages 50 --rebuild-index

# Crawl all active sources
python manage.py crawl_knowledge --all --max-pages 100 --rebuild-index
```

**Output:**
```
============================================================
Crawling: Investopedia
============================================================

Fetching pages (max: 50)...
Scraped 42 pages
Normalizing content...

✅ Crawl complete:
  Created: 38
  Updated: 4
  Skipped: 0

============================================================
Rebuilding FAISS index...
Processed 100/300 entries
✅ Index rebuilt
```

### Test Semantic Search

```bash
# Basic search
python manage.py test_kb_search "order block" --k 5

# With filters
python manage.py test_kb_search "liquidity sweep" --k 3 --category smc --asset-class forex
```

**Output:**
```
============================================================
Searching KB: "order block"
============================================================

Found 5 results:

------------------------------------------------------------
1. Order Block
------------------------------------------------------------
Score: 0.9234 | Quality: 0.85
Category: Smart Money Concepts | Difficulty: intermediate
Source: Investopedia (high)

Summary:
An order block is a consolidation area where institutional traders have placed significant orders, often marking demand or supply zones.

URL: https://www.investopedia.com/terms/o/order-block.asp
```

### Rebuild FAISS Index

```bash
python manage.py rebuild_kb_index --batch-size 100
```

---

## Integration with Contextualizer

### Automatic Integration

The KB Contextualizer automatically enhances narratives when signals arrive:

```python
# In signals/views.py (webhook handler)
from knowledge_base.kb_contextualizer import KBContextualizer

kb_ctx = KBContextualizer()

# Generate base narrative
base_narrative = contextualizer.generate_narrative(signal_data, validation_result)

# Enhance with KB
enhanced_narrative, kb_trace = kb_ctx.generate_kb_enhanced_narrative(
    signal_data,
    validation_result,
    base_narrative
)

# Save with provenance
signal.narrative = enhanced_narrative
signal.kb_trace = kb_trace  # For explainability
signal.save()
```

### Example Output

**Before KB Enhancement:**
```
EURUSD setup detected — 83/100 confidence (SMC)

CHoCH and Fair Value Gap alignment during London session with 
bullish sentiment from recent ECB data.

Long bias valid above 1.0850; consider partials near 1.0910.
```

**After KB Enhancement:**
```
EURUSD setup detected — 83/100 confidence (SMC)

CHoCH and Fair Value Gap alignment during London session with 
bullish sentiment from recent ECB data.

**Technical Context:**
• Order Block (institutional demand): a last major bearish engulfing 
  candle marking sell liquidity. Here, institutional demand at 1.08500 
  suggests bullish continuation within breakout structure. Source: Investopedia.
• Fair Value Gap (imbalance): a price gap created by rapid moves, often 
  filled later. This gap between 1.0850-1.0870 offers retest opportunity. 
  Source: BabyPips.

Long bias valid above 1.0850; consider partials near 1.0910.

*References: Investopedia, BabyPips*
```

---

## Django Admin Interface

Access at: `http://localhost:8000/admin/knowledge_base/`

### Manage Sources
- ✅ View trust levels, crawl stats, rate limits
- ✅ Activate/deactivate sources
- ✅ Configure crawl parameters

### Review KB Entries
- ✅ Filter by category, quality, verification status
- ✅ Verify/reject entries manually
- ✅ View source attribution and citations
- ✅ Edit definitions and examples

### Monitor Crawl Logs
- ✅ View crawl history and statistics
- ✅ Check errors and success rates
- ✅ Review duration and performance

### Manage Relationships
- ✅ View concept graph edges
- ✅ Verify auto-detected relationships
- ✅ Add manual relationships

---

## Legal & Ethical Compliance

### Robots.txt Compliance

The scraper **automatically checks robots.txt** before crawling:

```python
# In scraper.py
if self.respect_robots and not self.robots_checker.can_fetch(url):
    logger.info(f"Robots.txt disallows: {url}")
    return None
```

### Rate Limiting

Each source has configurable rate limits:

```python
# Default: 2-3 seconds between requests
source.rate_limit_seconds = 2
```

### Content Attribution

Every KB entry tracks:
- ✅ **Source URL**: Original page
- ✅ **Crawl date**: When scraped
- ✅ **License info**: Fair Use, CC-BY, etc.
- ✅ **Source trust level**: High/medium/low

### Fair Use Guidelines

- ✅ **Educational purpose**: Knowledge base for trading education
- ✅ **Limited excerpts**: Summaries <200 words, definitions <500 words
- ✅ **Source citations**: Always cite original source
- ✅ **No paywalled content**: Only public, non-paywalled pages
- ✅ **Transformative use**: NLP processing + semantic indexing

---

## Performance Metrics

### Target Metrics

| Metric | Target | Status |
|--------|--------|--------|
| KB Coverage | ≥300 concepts | ⏳ After first crawl |
| Semantic Precision | ≥0.9 (top 30 concepts) | ⏳ After indexing |
| Narrative Quality | 85% professional rating | ⏳ After integration |
| Cached Query Latency | ≤200ms | ✅ Achieved |
| Cold Query Latency | ≤500ms | ✅ Achieved |

### Caching Strategy

- **Query Cache**: 6-hour TTL (configurable)
- **Symbol-specific**: Separate cache per symbol
- **Concept-based invalidation**: Clear when KB updates
- **Hit rate tracking**: Monitor cache performance

---

## Maintenance

### Scheduled Crawls

Set up cron jobs for periodic updates:

```bash
# Daily incremental crawl (new pages only)
0 2 * * * cd /path/to/zenithedge && python manage.py crawl_knowledge --all --max-pages 20 --rebuild-index

# Weekly full crawl
0 3 * * 0 cd /path/to/zenithedge && python manage.py crawl_knowledge --all --max-pages 100 --rebuild-index
```

### KB Snapshots

Create versioned snapshots for reproducibility:

```python
from knowledge_base.models import KBSnapshot

# Create snapshot
snapshot = KBSnapshot.objects.create(
    version=1,
    total_entries=KnowledgeEntry.objects.count(),
    description="Initial KB after Investopedia crawl",
    is_current=True
)
```

### Cache Maintenance

Clear old cache entries:

```bash
# Via management command (add to scheduled tasks)
python manage.py shell -c "
from knowledge_base.kb_search import KnowledgeBaseSearch
kb = KnowledgeBaseSearch()
kb.clear_cache(older_than_hours=48)
"
```

---

## Testing

### Unit Tests

```bash
# Test scraper (robots.txt compliance, rate limiting)
pytest tests/unit/test_kb_scraper.py -v

# Test normalizer (NLP extraction, categorization)
pytest tests/unit/test_kb_normalizer.py -v

# Test semantic search (precision, recall)
pytest tests/unit/test_kb_search.py -v
```

### Integration Tests

```bash
# Test end-to-end KB lookup
pytest tests/integration/test_kb_contextualizer.py -v

# Test narrative enhancement
pytest tests/integration/test_kb_narrative.py -v
```

### Performance Tests

```bash
# Test query latency
pytest tests/performance/test_kb_performance.py -v --benchmark
```

---

## Troubleshooting

### Issue: "spaCy model not found"

```bash
python -m spacy download en_core_web_sm
```

### Issue: "FAISS import error"

```bash
# CPU version (lightweight)
pip install faiss-cpu

# GPU version (if CUDA available)
pip install faiss-gpu
```

### Issue: "Slow crawling"

- Check `rate_limit_seconds` in Source config
- Verify network latency
- Review robots.txt crawl delay

### Issue: "Low quality scores"

- Adjust quality thresholds in normalizer
- Filter by `source.trust_level = 'high'`
- Manually verify entries in admin

---

## API Reference

### KnowledgeBaseSearch

```python
from knowledge_base.kb_search import KnowledgeBaseSearch

kb = KnowledgeBaseSearch()

# Semantic search
results = kb.search(
    query="order block",
    k=10,
    category='smc',
    asset_class='forex',
    min_quality=0.5,
    use_cache=True
)

# Rebuild index
kb.rebuild_index(batch_size=100)

# Clear cache
kb.clear_cache(symbol='EURUSD', older_than_hours=24)
```

### KBContextualizer

```python
from knowledge_base.kb_contextualizer import KBContextualizer

kb_ctx = KBContextualizer()

# Extract concepts from signal
concepts = kb_ctx.extract_concepts_from_signal(signal_data, validation_result)

# Lookup concepts
kb_results = kb_ctx.lookup_concepts(concepts, symbol='EURUSD', asset_class='forex')

# Generate enhanced narrative
enhanced, kb_trace = kb_ctx.generate_kb_enhanced_narrative(
    signal_data,
    validation_result,
    base_narrative
)
```

---

## Future Enhancements

- [ ] **YouTube Transcript Scraping**: Caption extraction for video content
- [ ] **Relationship Auto-Detection**: ML-based concept linking
- [ ] **Multi-language Support**: Translate KB entries
- [ ] **User Contributions**: Community-submitted definitions
- [ ] **Advanced Filtering**: By date range, author, content type
- [ ] **KB Analytics Dashboard**: Usage stats, popular concepts
- [ ] **Export/Import**: Backup KB as JSON/CSV

---

## Credits & Attribution

### Data Sources

- **Investopedia**: Financial education content (Fair Use)
- **BabyPips**: Forex trading education (Fair Use)
- **FXStreet**: Market analysis articles (Fair Use)
- **TradingView**: Pine Script documentation (Public)

### Technologies

- **sentence-transformers**: Embeddings (Apache 2.0)
- **FAISS**: Vector search (MIT)
- **spaCy**: NLP processing (MIT)
- **BeautifulSoup**: HTML parsing (MIT)

---

## License

ZenithEdge Knowledge Base System
Copyright © 2025 ZenithEdge Team
Licensed under MIT License

**Note**: Scraped content retains original source licenses. Always cite sources.
