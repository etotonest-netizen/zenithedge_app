"""
RSS Feed Fetcher for ZenNews
Fetches financial news from multiple public RSS feeds
"""
import hashlib
import logging
from datetime import datetime, timezone as dt_timezone
from typing import List, Dict, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class RSSFeedFetcher:
    """
    Fetches and parses RSS feeds from multiple financial news sources
    """
    
    # Public RSS feeds for financial news
    FEED_SOURCES = {
        'FXStreet': 'https://www.fxstreet.com/news/rss',
        'ForexLive': 'https://www.forexlive.com/feed/news',
        'DailyFX': 'https://www.dailyfx.com/feeds/market-news',
        'Investing.com Forex': 'https://www.investing.com/rss/news_285.rss',
        'Investing.com Commodities': 'https://www.investing.com/rss/news_301.rss',
        'Reuters Business': 'https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best',
        'MarketWatch': 'https://feeds.content.dowjones.io/public/rss/mw_topstories',
        'Bloomberg Markets': 'https://feeds.bloomberg.com/markets/news.rss',
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fetch_all_feeds(self) -> List[Dict]:
        """
        Fetch all configured RSS feeds
        
        Returns:
            List of parsed feed entries
        """
        all_entries = []
        
        for source_name, feed_url in self.FEED_SOURCES.items():
            try:
                entries = self.fetch_feed(source_name, feed_url)
                all_entries.extend(entries)
                self.logger.info(f"Fetched {len(entries)} entries from {source_name}")
            except Exception as e:
                self.logger.error(f"Error fetching feed from {source_name}: {str(e)}")
                continue
        
        return all_entries
    
    def fetch_feed(self, source_name: str, feed_url: str, max_entries: int = 50) -> List[Dict]:
        """
        Fetch and parse a single RSS feed
        
        Args:
            source_name: Name of the news source
            feed_url: URL of the RSS feed
            max_entries: Maximum number of entries to fetch
            
        Returns:
            List of parsed entries with standardized format
        """
        try:
            # Lazy import to avoid dependency issues on server startup
            try:
                import feedparser
            except ImportError:
                self.logger.error("feedparser not installed. Run: pip install feedparser")
                return []
            
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                self.logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries[:max_entries]:
                parsed_entry = self._parse_entry(entry, source_name)
                if parsed_entry:
                    entries.append(parsed_entry)
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Error parsing feed {source_name}: {str(e)}")
            return []
    
    def _parse_entry(self, entry: Dict, source_name: str) -> Optional[Dict]:
        """
        Parse a single feed entry into standardized format
        
        Args:
            entry: Feed entry dict
            source_name: Name of the news source
            
        Returns:
            Standardized entry dict or None if parsing fails
        """
        try:
            # Extract title
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # Extract link
            link = entry.get('link', '')
            
            # Extract and parse timestamp
            published = entry.get('published') or entry.get('updated')
            if published:
                try:
                    # Lazy import dateutil
                    try:
                        from dateutil import parser as date_parser
                    except ImportError:
                        self.logger.debug("python-dateutil not installed, using current time")
                        timestamp = timezone.now()
                    else:
                        timestamp = date_parser.parse(published)
                        # Make timezone-aware if needed
                        if timestamp.tzinfo is None:
                            timestamp = timezone.make_aware(timestamp)
                except Exception as e:
                    self.logger.debug(f"Error parsing date '{published}': {e}")
                    timestamp = timezone.now()
            else:
                timestamp = timezone.now()
            
            # Extract description/summary
            description = entry.get('description', '') or entry.get('summary', '')
            
            # Create content hash for deduplication
            content_for_hash = f"{title}{link}{published}"
            content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
            
            return {
                'headline': title,
                'source': source_name,
                'source_url': link,
                'timestamp': timestamp,
                'content_hash': content_hash,
                'description': description[:500],  # Limit description length
            }
            
        except Exception as e:
            self.logger.debug(f"Error parsing entry: {str(e)}")
            return None
    
    def is_duplicate(self, content_hash: str, existing_hashes: set) -> bool:
        """
        Check if an entry is a duplicate based on content hash
        
        Args:
            content_hash: SHA256 hash of the content
            existing_hashes: Set of existing content hashes
            
        Returns:
            True if duplicate, False otherwise
        """
        return content_hash in existing_hashes


def fetch_latest_news(max_age_hours: int = 24) -> List[Dict]:
    """
    Convenience function to fetch latest news
    
    Args:
        max_age_hours: Maximum age of news items in hours
        
    Returns:
        List of parsed news entries
    """
    fetcher = RSSFeedFetcher()
    all_entries = fetcher.fetch_all_feeds()
    
    # Filter by age
    cutoff_time = timezone.now() - timezone.timedelta(hours=max_age_hours)
    recent_entries = [
        entry for entry in all_entries 
        if entry['timestamp'] >= cutoff_time
    ]
    
    logger.info(f"Fetched {len(recent_entries)} recent news entries (last {max_age_hours} hours)")
    return recent_entries
