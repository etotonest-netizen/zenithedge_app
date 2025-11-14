"""
Create diverse test news events for trading symbols
"""
import os
import django
import random
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from django.utils import timezone
from zennews.models import NewsEvent

# News templates for different symbols
NEWS_TEMPLATES = {
    'EURUSD': [
        "ECB maintains interest rates at current levels amid inflation concerns",
        "Euro strengthens against dollar on strong economic data from Germany",
        "European Central Bank signals potential policy shift in coming months",
        "Eurozone manufacturing PMI exceeds expectations, boosting EUR sentiment",
        "ECB President announces new monetary policy framework",
    ],
    'GBPUSD': [
        "Bank of England holds interest rates steady amid economic concerns",
        "Sterling rallies as UK inflation data comes in better than expected",
        "Pound weakens on disappointing retail sales figures",
        "UK employment data shows strong jobs growth, supporting GBP",
        "Bank of England minutes reveal split vote on rate decision",
    ],
    'USDJPY': [
        "Bank of Japan maintains ultra-loose monetary policy stance",
        "Yen strengthens as risk-off sentiment dominates markets",
        "Japanese inflation data supports case for BOJ policy adjustment",
        "USD/JPY reaches multi-year highs on rate differential concerns",
        "BOJ Governor hints at potential yield curve control modifications",
    ],
    'AUDUSD': [
        "Australian dollar gains on strong employment figures",
        "RBA keeps rates unchanged, cites global economic uncertainty",
        "Commodity prices boost Aussie dollar sentiment",
        "Australian GDP growth exceeds forecasts, supporting AUD",
        "China economic data impacts Australian dollar outlook",
    ],
    'USDCAD': [
        "Canadian dollar strengthens on higher oil prices",
        "Bank of Canada signals pause in rate hiking cycle",
        "Loonie weakens as crude oil inventories rise unexpectedly",
        "Canadian employment data beats expectations, supporting CAD",
        "USD/CAD falls as trade balance improves for Canada",
    ],
    'NZDUSD': [
        "New Zealand dollar rallies on RBNZ hawkish commentary",
        "Kiwi weakens as dairy prices decline in latest auction",
        "RBNZ keeps OCR unchanged, maintains cautious outlook",
        "New Zealand GDP growth stronger than expected",
        "NZD gains on improved risk appetite in global markets",
    ],
    'XAUUSD': [
        "Gold prices surge to new highs on safe-haven demand",
        "Precious metals rally as inflation concerns mount",
        "Gold retreats from highs as dollar strengthens",
        "Central bank gold purchases reach record levels",
        "Gold volatility increases amid geopolitical tensions",
    ],
    'BTCUSD': [
        "Bitcoin surges past $90,000 on institutional buying",
        "Crypto markets rally on regulatory clarity news",
        "Bitcoin consolidates after recent sharp gains",
        "Major institutional investor announces Bitcoin allocation",
        "Cryptocurrency market cap reaches new all-time high",
    ],
}

IMPACT_LEVELS = ['low', 'medium', 'high']
SENTIMENTS = [-0.7, -0.5, -0.3, -0.1, 0.0, 0.1, 0.3, 0.5, 0.7]

def create_news_events():
    """Create test news events for all symbols"""
    print("📰 Creating test news events...\n")
    
    created_count = 0
    
    for symbol, headlines in NEWS_TEMPLATES.items():
        print(f"\n{symbol}:")
        
        for i, headline in enumerate(headlines):
            # Random timestamp within last 24 hours
            hours_ago = random.randint(1, 24)
            timestamp = timezone.now() - timedelta(hours=hours_ago)
            
            # Random sentiment and impact
            sentiment = random.choice(SENTIMENTS)
            impact_level = random.choice(IMPACT_LEVELS)
            
            # Calculate relevance rank (higher for more recent news)
            relevance_rank = max(50, 100 - (hours_ago * 2))
            
            try:
                news = NewsEvent.objects.create(
                    symbol=symbol,
                    headline=headline,
                    content_extract=f"{headline}. Market analysts are closely monitoring developments...",
                    sentiment=sentiment,
                    impact_level=impact_level,
                    relevance_rank=relevance_rank,
                    source='Test Financial News',
                    timestamp=timestamp
                )
                created_count += 1
                
                sentiment_emoji = "📈" if sentiment > 0.3 else "📉" if sentiment < -0.3 else "➡️"
                impact_emoji = "🔴" if impact_level == 'high' else "🟡" if impact_level == 'medium' else "🟢"
                
                print(f"  {sentiment_emoji} {impact_emoji} {hours_ago:2d}h ago | {headline[:60]}...")
                
            except Exception as e:
                print(f"  ❌ Error creating news: {e}")
    
    print(f"\n✅ Created {created_count} news events")
    print(f"📊 Total news in database: {NewsEvent.objects.count()}")
    
    # Show news count by symbol
    print("\n📊 News by symbol:")
    for symbol in NEWS_TEMPLATES.keys():
        count = NewsEvent.objects.filter(symbol=symbol).count()
        print(f"  {symbol}: {count} events")

if __name__ == '__main__':
    create_news_events()
