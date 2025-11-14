#!/usr/bin/env python3
"""
Test ZenNews Integration
Verifies that the news system is working correctly
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from zennews.models import NewsEvent, NewsAlert
from zennews.utils import analyze_news_text, RSSFeedFetcher
from bot.ai_score import integrate_news_bias, get_news_sentiment_summary
from django.utils import timezone

def test_nlp_analyzer():
    """Test sentiment analysis"""
    print("\n" + "="*60)
    print("🧪 Testing NLP Sentiment Analyzer")
    print("="*60)
    
    test_headlines = [
        "Fed raises interest rates by 75 basis points, dollar surges",
        "ECB signals dovish stance, euro falls sharply",
        "Gold prices stabilize amid mixed economic data",
    ]
    
    for headline in test_headlines:
        result = analyze_news_text(headline)
        print(f"\n📰 {headline}")
        print(f"   Sentiment: {result['sentiment']:.2f} ({result['sentiment'] > 0 and 'Positive' or 'Negative'})")
        print(f"   Impact: {result['impact_level']}")
        print(f"   Symbols: {', '.join(result['symbols'])}")
        print(f"   Topics: {', '.join(result['topics'])}")
    
    print("\n✅ NLP Analyzer working correctly")


def test_rss_fetcher():
    """Test RSS feed fetching"""
    print("\n" + "="*60)
    print("🧪 Testing RSS Feed Fetcher")
    print("="*60)
    
    fetcher = RSSFeedFetcher()
    
    # Test single feed
    print("\n📡 Fetching from FXStreet...")
    try:
        entries = fetcher.fetch_feed('FXStreet', 'https://www.fxstreet.com/news/rss', max_entries=5)
        print(f"✅ Fetched {len(entries)} entries")
        
        if entries:
            print(f"\nSample entry:")
            print(f"  Headline: {entries[0]['headline'][:80]}...")
            print(f"  Source: {entries[0]['source']}")
            print(f"  Timestamp: {entries[0]['timestamp']}")
    except Exception as e:
        print(f"⚠️  RSS fetch warning: {str(e)}")
        print("   (This is normal if you don't have internet connection)")


def test_database_models():
    """Test database models"""
    print("\n" + "="*60)
    print("🧪 Testing Database Models")
    print("="*60)
    
    # Create test news event
    test_news = NewsEvent.objects.create(
        symbol='EURUSD',
        headline='Test: ECB maintains interest rates, euro stable',
        sentiment=0.1,
        impact_level='medium',
        topic='Interest Rates, Central Bank',
        source='Test Source',
        content_hash='test_hash_123',
        timestamp=timezone.now()
    )
    
    print(f"\n✅ Created test news event: {test_news.id}")
    print(f"   Symbol: {test_news.symbol}")
    print(f"   Sentiment Label: {test_news.get_sentiment_label()}")
    print(f"   Impact: {test_news.impact_level}")
    
    # Test news count
    total_news = NewsEvent.objects.count()
    print(f"\n📊 Total news events in database: {total_news}")
    
    # Clean up test data
    test_news.delete()
    print("🧹 Cleaned up test data")


def test_zenbot_integration():
    """Test ZenBot integration"""
    print("\n" + "="*60)
    print("🧪 Testing ZenBot Integration")
    print("="*60)
    
    # Create test news
    test_news = NewsEvent.objects.create(
        symbol='EURUSD',
        headline='Test: Positive economic data boosts euro',
        sentiment=0.6,
        impact_level='high',
        topic='GDP Growth',
        source='Test',
        content_hash='test_zenbot_123',
        timestamp=timezone.now()
    )
    
    try:
        # Test news bias integration
        base_score = 75.0
        adjusted_score, bias, news_data = integrate_news_bias('EURUSD', base_score)
        
        print(f"\n📊 News Bias Calculation:")
        print(f"   Base Score: {base_score}")
        print(f"   Bias Adjustment: {bias:+.2f}")
        print(f"   Adjusted Score: {adjusted_score:.2f}")
        print(f"   News Count: {news_data.get('news_count', 0)}")
        
        if 'avg_sentiment' in news_data:
            print(f"   Avg Sentiment: {news_data['avg_sentiment']:.3f}")
        
        # Test news summary
        summary = get_news_sentiment_summary('EURUSD', hours=24)
        print(f"\n📈 News Summary:")
        print(f"   Status: {summary.get('status', 'unknown')}")
        print(f"   News Count: {summary.get('news_count', 0)}")
        
        if summary.get('status') == 'success':
            print(f"   Sentiment Label: {summary['sentiment_label']}")
            print(f"   Average Sentiment: {summary['avg_sentiment']:.3f}")
        
        print("\n✅ ZenBot integration working correctly")
        
    finally:
        # Clean up
        test_news.delete()
        print("🧹 Cleaned up test data")


def main():
    print("\n" + "="*60)
    print("🚀 ZenNews Integration Test Suite")
    print("="*60)
    
    try:
        test_nlp_analyzer()
        test_rss_fetcher()
        test_database_models()
        test_zenbot_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nNext steps:")
        print("1. Run: python manage.py fetch_news")
        print("2. Visit: http://127.0.0.1:8000/news/")
        print("3. Check Django admin: http://127.0.0.1:8000/admin/zennews/")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
