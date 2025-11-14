"""
Test Suite for Knowledge Base System
"""
import pytest
from django.test import TestCase
from knowledge_base.models import Source, KnowledgeEntry
from knowledge_base.normalizer import ContentNormalizer, TradingTermExtractor
from knowledge_base.scraper import ScrapedContent
from datetime import datetime


class TestTradingTermExtractor(TestCase):
    """Test term extraction and normalization"""
    
    def setUp(self):
        self.extractor = TradingTermExtractor()
    
    def test_extract_canonical_term_known_concepts(self):
        """Test extraction of known trading concepts"""
        title = "Understanding Order Blocks in Smart Money Concepts"
        text = "Order blocks are key supply and demand zones..."
        
        term, aliases = self.extractor.extract_canonical_term(title, text)
        
        assert term.lower() == "order block"
        assert len(aliases) > 0
    
    def test_categorize_smc(self):
        """Test SMC categorization"""
        term = "order block"
        text = "Smart money concepts use order blocks to identify institutional zones"
        
        category = self.extractor.categorize(term, text)
        
        assert category == 'smc'
    
    def test_assess_difficulty(self):
        """Test difficulty assessment"""
        simple_text = "This is a basic introduction to support levels. It's very simple."
        complex_text = "The sophisticated institutional algorithmic order flow dynamics necessitate advanced analysis."
        
        assert self.extractor.assess_difficulty(simple_text) in ['intro', 'intermediate']
        assert self.extractor.assess_difficulty(complex_text) in ['advanced', 'expert']
    
    def test_detect_asset_classes(self):
        """Test asset class detection"""
        forex_text = "EURUSD forex pair trading with currency analysis"
        crypto_text = "Bitcoin and Ethereum cryptocurrency markets"
        
        assert 'forex' in self.extractor.detect_asset_classes(forex_text)
        assert 'crypto' in self.extractor.detect_asset_classes(crypto_text)


class TestContentNormalizer(TestCase):
    """Test content normalization pipeline"""
    
    def setUp(self):
        self.normalizer = ContentNormalizer()
        
        # Create test source
        self.source = Source.objects.create(
            domain='test.com',
            name='Test Source',
            base_url='https://test.com',
            trust_level='high'
        )
        
        # Mock scraped content
        self.scraped = ScrapedContent(
            url='https://test.com/order-block',
            title='Order Block Definition',
            main_text=(
                "An order block is a consolidation area where institutional "
                "traders have placed significant orders. It represents the last "
                "up-close candle before a strong bearish move. Order blocks "
                "are used in smart money concepts to identify key supply and "
                "demand zones in the market structure."
            ),
            examples=['EURUSD 1H chart example', 'GBPJPY 4H example'],
            code_blocks=[],
            metadata={'author': 'Test Author'},
            crawl_timestamp=datetime.now()
        )
    
    def test_extract_summary(self):
        """Test summary extraction"""
        summary = self.normalizer.extract_summary(self.scraped.main_text)
        
        assert len(summary) > 20
        assert len(summary) < 500
        assert summary.endswith('.')
    
    def test_extract_definition(self):
        """Test definition extraction"""
        definition = self.normalizer.extract_definition(self.scraped.main_text)
        
        assert len(definition) > 50
    
    def test_calculate_quality_score(self):
        """Test quality scoring"""
        score = self.normalizer.calculate_quality_score(
            self.scraped.main_text,
            self.scraped.examples,
            'high'
        )
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.5  # Should be decent quality with examples
    
    def test_normalize_full_entry(self):
        """Test full normalization pipeline"""
        normalized = self.normalizer.normalize(self.scraped, 'high')
        
        assert normalized is not None
        assert normalized.term
        assert normalized.summary
        assert normalized.definition
        assert normalized.category in ['smc', 'ict', 'ta', 'risk', 'other']
        assert 0.0 <= normalized.quality_score <= 1.0


class TestKnowledgeEntry(TestCase):
    """Test KB entry model"""
    
    def setUp(self):
        self.source = Source.objects.create(
            domain='investopedia.com',
            name='Investopedia',
            base_url='https://www.investopedia.com',
            trust_level='high'
        )
    
    def test_create_entry(self):
        """Test creating KB entry"""
        entry = KnowledgeEntry.objects.create(
            term='Order Block',
            aliases=['OB', 'demand zone'],
            summary='Institutional demand zone',
            definition='Detailed explanation...',
            examples='EURUSD example',
            category='smc',
            difficulty='intermediate',
            asset_classes=['any'],
            source=self.source,
            source_url='https://investopedia.com/test',
            quality_score=0.85,
            relevance_score=0.90,
            completeness_score=0.88
        )
        
        assert entry.id is not None
        assert entry.term == 'Order Block'
        assert len(entry.aliases) == 2
    
    def test_increment_usage(self):
        """Test usage tracking"""
        entry = KnowledgeEntry.objects.create(
            term='Test Term',
            summary='Test summary',
            definition='Test definition',
            category='ta',
            source=self.source,
            source_url='https://test.com',
            quality_score=0.5
        )
        
        initial_count = entry.view_count
        entry.increment_usage()
        
        assert entry.view_count == initial_count + 1
        assert entry.last_used is not None


class TestSemanticSearch(TestCase):
    """Test semantic search functionality"""
    
    def setUp(self):
        # Create test source
        self.source = Source.objects.create(
            domain='test.com',
            name='Test Source',
            base_url='https://test.com',
            trust_level='high'
        )
        
        # Create test entries
        self.entries = [
            KnowledgeEntry.objects.create(
                term='Order Block',
                summary='Institutional demand zone marking key price levels',
                definition='Order blocks represent areas where institutions placed orders',
                category='smc',
                source=self.source,
                source_url='https://test.com/ob',
                quality_score=0.85
            ),
            KnowledgeEntry.objects.create(
                term='Fair Value Gap',
                summary='Price imbalance gap created by rapid moves',
                definition='FVG is a three-candle pattern showing imbalance',
                category='smc',
                source=self.source,
                source_url='https://test.com/fvg',
                quality_score=0.80
            ),
        ]
    
    def test_kb_search_basic(self):
        """Test basic KB search"""
        from knowledge_base.kb_search import KnowledgeBaseSearch
        
        kb = KnowledgeBaseSearch()
        
        # Rebuild index with test entries
        kb.rebuild_index(batch_size=10)
        
        # Search for "institutional zones"
        results = kb.search(
            query="institutional demand zones",
            k=5,
            use_cache=False
        )
        
        # Should find Order Block entry
        assert len(results) > 0
        
        # Top result should be relevant
        top_entry = results[0]['entry']
        assert 'order' in top_entry.term.lower() or 'institutional' in top_entry.summary.lower()


# Fixture for testing
@pytest.fixture
def sample_kb_entries():
    """Create sample KB entries for testing"""
    source = Source.objects.create(
        domain='investopedia.com',
        name='Investopedia',
        base_url='https://www.investopedia.com',
        trust_level='high'
    )
    
    entries = []
    concepts = [
        ('Order Block', 'Institutional demand zone', 'smc'),
        ('Fair Value Gap', 'Price imbalance', 'smc'),
        ('Liquidity Sweep', 'Stop hunt pattern', 'smc'),
        ('Support Level', 'Price floor zone', 'ta'),
        ('Resistance Level', 'Price ceiling zone', 'ta'),
    ]
    
    for term, summary, category in concepts:
        entry = KnowledgeEntry.objects.create(
            term=term,
            summary=summary,
            definition=f'{summary}. Detailed explanation...',
            category=category,
            source=source,
            source_url=f'https://investopedia.com/{term.lower().replace(" ", "-")}',
            quality_score=0.8
        )
        entries.append(entry)
    
    return entries
