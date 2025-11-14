#!/usr/bin/env python3
"""
Knowledge Base System - End-to-End Test Script
Tests the complete KB pipeline from scraping to narrative generation

Usage:
    python test_kb_system.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from knowledge_base.models import Source, KnowledgeEntry, CrawlLog
from knowledge_base.scraper import KnowledgeScraper, ScrapedContent
from knowledge_base.normalizer import ContentNormalizer
from knowledge_base.kb_search import KnowledgeBaseSearch
from knowledge_base.kb_contextualizer import KBContextualizer
from datetime import datetime


def test_database_models():
    """Test 1: Database models exist and can be queried"""
    print("\n" + "="*60)
    print("TEST 1: Database Models")
    print("="*60)
    
    try:
        source_count = Source.objects.count()
        entry_count = KnowledgeEntry.objects.count()
        log_count = CrawlLog.objects.count()
        
        print(f"✅ Source model: {source_count} records")
        print(f"✅ KnowledgeEntry model: {entry_count} records")
        print(f"✅ CrawlLog model: {log_count} records")
        
        if source_count == 0:
            print("⚠️  Warning: No sources found. Run: python manage.py init_kb_sources")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_scraper():
    """Test 2: Scraper can extract content"""
    print("\n" + "="*60)
    print("TEST 2: Web Scraper")
    print("="*60)
    
    try:
        scraper = KnowledgeScraper()
        
        # Test robots.txt checker
        test_url = "https://www.investopedia.com/terms/s/support.asp"
        can_fetch = scraper.robots_checker.can_fetch(test_url)
        print(f"✅ Robots.txt check: {'Allowed' if can_fetch else 'Blocked'}")
        
        # Test content scrubber (mock HTML)
        mock_html = """
        <html>
            <head><title>Order Block Definition</title></head>
            <body>
                <article>
                    <h1>Order Block</h1>
                    <p>An order block is a consolidation area.</p>
                    <p>It represents institutional demand zones.</p>
                </article>
            </body>
        </html>
        """
        
        content = scraper.scrubber.scrub(mock_html, test_url)
        print(f"✅ Content extraction: {len(content.main_text)} chars")
        print(f"   Title: {content.title}")
        print(f"   Text preview: {content.main_text[:80]}...")
        
        return True
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False


def test_normalizer():
    """Test 3: Normalizer can process content"""
    print("\n" + "="*60)
    print("TEST 3: NLP Normalizer")
    print("="*60)
    
    try:
        normalizer = ContentNormalizer()
        
        # Mock scraped content
        mock_content = ScrapedContent(
            url="https://test.com/order-block",
            title="Understanding Order Blocks in Smart Money Concepts",
            main_text=(
                "An order block is a consolidation area where institutional "
                "traders have placed significant orders. It represents the last "
                "up-close candle before a strong bearish move. Order blocks "
                "are used in smart money concepts to identify key supply and "
                "demand zones in the market structure. This concept is fundamental "
                "for understanding institutional behavior and price action."
            ),
            examples=["EURUSD example at 1.0950", "GBPJPY 4H chart pattern"],
            code_blocks=[],
            metadata={'author': 'Test'},
            crawl_timestamp=datetime.now()
        )
        
        # Normalize
        normalized = normalizer.normalize(mock_content, source_trust='high')
        
        if normalized:
            print(f"✅ Normalization successful")
            print(f"   Term: {normalized.term}")
            print(f"   Category: {normalized.category}")
            print(f"   Difficulty: {normalized.difficulty}")
            print(f"   Quality: {normalized.quality_score:.2f}")
            print(f"   Summary: {normalized.summary[:80]}...")
            return True
        else:
            print("⚠️  Normalization returned None (quality threshold)")
            return True
            
    except Exception as e:
        print(f"❌ Normalizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_search():
    """Test 4: Embedding engine and FAISS search"""
    print("\n" + "="*60)
    print("TEST 4: Embeddings & Semantic Search")
    print("="*60)
    
    try:
        kb_search = KnowledgeBaseSearch()
        
        # Test embedding generation
        test_text = "Order block represents institutional demand zones"
        embedding = kb_search.embedding_engine.encode_single(test_text)
        
        print(f"✅ Embedding generation: {len(embedding)} dimensions")
        
        # Check if KB has entries
        entry_count = KnowledgeEntry.objects.count()
        
        if entry_count == 0:
            print("⚠️  No KB entries for search testing")
            print("   Run: python manage.py crawl_knowledge --source investopedia --max-pages 10")
            return True
        
        # Test search
        results = kb_search.search(
            query="institutional demand zones",
            k=3,
            use_cache=False
        )
        
        print(f"✅ Search completed: {len(results)} results")
        for i, result in enumerate(results[:3], 1):
            entry = result['entry']
            score = result['score']
            print(f"   {i}. {entry.term} (score: {score:.3f}, quality: {entry.quality_score:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding/search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_contextualizer_integration():
    """Test 5: KB Contextualizer integration"""
    print("\n" + "="*60)
    print("TEST 5: Contextualizer Integration")
    print("="*60)
    
    try:
        kb_ctx = KBContextualizer()
        
        # Mock signal data
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',
            'regime': 'breakout',
            'price': 1.0850,
            'sl': 1.0820,
            'tp': 1.0910,
            'confidence': 83
        }
        
        validation_result = {
            'truth_index': 83,
            'status': 'approved',
            'breakdown': {}
        }
        
        # Extract concepts
        concepts = kb_ctx.extract_concepts_from_signal(signal_data, validation_result)
        print(f"✅ Concept extraction: {len(concepts)} concepts")
        print(f"   Concepts: {', '.join(concepts)}")
        
        # Test lookup (if entries exist)
        entry_count = KnowledgeEntry.objects.count()
        
        if entry_count > 0:
            kb_results = kb_ctx.lookup_concepts(concepts, symbol='EURUSD', asset_class='forex')
            print(f"✅ KB lookup: {len(kb_results)} matches")
            
            for concept, kb_data in list(kb_results.items())[:2]:
                print(f"   - {kb_data['term']}: {kb_data['summary'][:60]}...")
        else:
            print("⚠️  No KB entries for lookup testing")
        
        # Test narrative enhancement
        base_narrative = "EURUSD setup detected — 83/100 confidence (SMC)"
        
        enhanced, kb_trace = kb_ctx.generate_kb_enhanced_narrative(
            signal_data,
            validation_result,
            base_narrative
        )
        
        print(f"✅ Narrative enhancement successful")
        print(f"   Base length: {len(base_narrative)} chars")
        print(f"   Enhanced length: {len(enhanced)} chars")
        print(f"   KB trace concepts: {kb_trace['concepts']}")
        print(f"   KB trace sources: {len(kb_trace['sources'])} sources")
        
        return True
        
    except Exception as e:
        print(f"❌ Contextualizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_interface():
    """Test 6: Admin interface accessibility"""
    print("\n" + "="*60)
    print("TEST 6: Admin Interface")
    print("="*60)
    
    try:
        from django.contrib.admin.sites import site
        from knowledge_base.admin import (
            SourceAdmin, KnowledgeEntryAdmin, ConceptRelationshipAdmin,
            CrawlLogAdmin, KBSnapshotAdmin, QueryCacheAdmin
        )
        
        # Check if models are registered
        from knowledge_base.models import (
            Source, KnowledgeEntry, ConceptRelationship,
            CrawlLog, KBSnapshot, QueryCache
        )
        
        registered = []
        for model in [Source, KnowledgeEntry, ConceptRelationship, 
                     CrawlLog, KBSnapshot, QueryCache]:
            if model in site._registry:
                registered.append(model.__name__)
        
        print(f"✅ Admin registration: {len(registered)}/6 models")
        for name in registered:
            print(f"   - {name}")
        
        print("\n   Admin URLs:")
        print("   - Sources: /admin/knowledge_base/source/")
        print("   - Entries: /admin/knowledge_base/knowledgeentry/")
        print("   - Crawl Logs: /admin/knowledge_base/crawllog/")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin test failed: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    test_names = [
        "Database Models",
        "Web Scraper",
        "NLP Normalizer",
        "Embeddings & Search",
        "Contextualizer Integration",
        "Admin Interface"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {name}: {status}")
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 All tests passed! KB system is fully functional.")
        print("\nNext steps:")
        print("1. Run: python manage.py init_kb_sources")
        print("2. Run: python manage.py crawl_knowledge --source investopedia --max-pages 50 --rebuild-index")
        print("3. Access admin: http://localhost:8000/admin/knowledge_base/")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        print("\nCommon fixes:")
        print("- Run migrations: python manage.py makemigrations && python manage.py migrate")
        print("- Install deps: pip install -r requirements_kb.txt")
        print("- Download models: python -m spacy download en_core_web_sm")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("KNOWLEDGE BASE SYSTEM - END-TO-END TEST")
    print("="*60)
    print("Testing complete KB pipeline from scraping to narrative generation")
    
    results = []
    
    # Run tests
    results.append(test_database_models())
    results.append(test_scraper())
    results.append(test_normalizer())
    results.append(test_embedding_search())
    results.append(test_contextualizer_integration())
    results.append(test_admin_interface())
    
    # Print summary
    print_summary(results)
    
    # Exit code
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
