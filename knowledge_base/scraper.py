"""
Web Scraper for Trading Knowledge Base
Respects robots.txt, rate limits, and site TOS
"""
import time
import logging
import hashlib
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import feedparser
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Container for scraped page content"""
    url: str
    title: str
    main_text: str
    examples: List[str]
    code_blocks: List[str]
    metadata: Dict
    crawl_timestamp: datetime


class RobotsTxtChecker:
    """Check if crawling is allowed per robots.txt"""
    
    def __init__(self):
        self.parsers = {}  # domain -> RobotFileParser
        self.cache_timeout = timedelta(hours=24)
        self.last_checked = {}
    
    def can_fetch(self, url: str, user_agent: str = "ZenithEdgeBot/1.0") -> bool:
        """Check if URL can be fetched"""
        domain = urlparse(url).netloc
        
        # Check cache
        if domain in self.parsers and domain in self.last_checked:
            if datetime.now() - self.last_checked[domain] < self.cache_timeout:
                return self.parsers[domain].can_fetch(user_agent, url)
        
        # Fetch and parse robots.txt
        robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        try:
            parser.read()
            self.parsers[domain] = parser
            self.last_checked[domain] = datetime.now()
            return parser.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"Could not read robots.txt for {domain}: {e}")
            # Default to allowing if robots.txt unavailable
            return True
    
    def get_crawl_delay(self, url: str, user_agent: str = "ZenithEdgeBot/1.0") -> float:
        """Get recommended crawl delay from robots.txt"""
        domain = urlparse(url).netloc
        if domain in self.parsers:
            delay = self.parsers[domain].crawl_delay(user_agent)
            return float(delay) if delay else 2.0
        return 2.0


class RateLimiter:
    """Enforce rate limits between requests to same domain"""
    
    def __init__(self):
        self.last_request = {}  # domain -> timestamp
    
    def wait_if_needed(self, domain: str, min_delay: float = 2.0):
        """Wait if necessary before next request"""
        if domain in self.last_request:
            elapsed = time.time() - self.last_request[domain]
            if elapsed < min_delay:
                sleep_time = min_delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request[domain] = time.time()


class ContentScrubber:
    """Extract clean content from HTML, remove boilerplate"""
    
    def __init__(self):
        # Common boilerplate patterns to remove
        self.noise_classes = [
            'header', 'footer', 'nav', 'sidebar', 'advertisement',
            'ad', 'banner', 'menu', 'social', 'related', 'comment',
            'popup', 'modal', 'subscribe', 'newsletter'
        ]
        
        self.noise_ids = [
            'header', 'footer', 'sidebar', 'nav', 'menu', 'ads',
            'comments', 'related-posts', 'social-share'
        ]
    
    def scrub(self, html: str, url: str) -> ScrapedContent:
        """Extract main content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove noise
        for tag in soup.find_all(class_=lambda x: x and any(n in x.lower() for n in self.noise_classes)):
            tag.decompose()
        
        for tag in soup.find_all(id=lambda x: x and any(n in x.lower() for n in self.noise_ids)):
            tag.decompose()
        
        # Remove scripts and styles
        for tag in soup(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract main content
        main_text = self._extract_main_text(soup)
        
        # Extract examples
        examples = self._extract_examples(soup)
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(soup)
        
        # Extract metadata
        metadata = self._extract_metadata(soup, url)
        
        return ScrapedContent(
            url=url,
            title=title,
            main_text=main_text,
            examples=examples,
            code_blocks=code_blocks,
            metadata=metadata,
            crawl_timestamp=datetime.now()
        )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try h1 first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Fall back to title tag
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return "Untitled"
    
    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """Extract main article text"""
        # Try common article containers
        containers = [
            soup.find('article'),
            soup.find('main'),
            soup.find(class_=re.compile(r'content|article|post|entry', re.I)),
            soup.find(id=re.compile(r'content|article|post|entry', re.I))
        ]
        
        for container in containers:
            if container:
                # Get all paragraphs
                paragraphs = container.find_all(['p', 'li'])
                text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if len(text) > 200:  # Minimum content length
                    return text
        
        # Fallback: all paragraphs
        paragraphs = soup.find_all('p')
        return '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    
    def _extract_examples(self, soup: BeautifulSoup) -> List[str]:
        """Extract example boxes or highlighted sections"""
        examples = []
        
        # Look for example containers
        example_containers = soup.find_all(class_=re.compile(r'example|sample|demo|illustration', re.I))
        for container in example_containers:
            text = container.get_text(strip=True)
            if 50 < len(text) < 1000:  # Reasonable example length
                examples.append(text)
        
        return examples
    
    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[str]:
        """Extract code blocks"""
        code_blocks = []
        
        for tag in soup.find_all(['code', 'pre']):
            code = tag.get_text(strip=True)
            if len(code) > 20:  # Minimum code length
                code_blocks.append(code)
        
        return code_blocks
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract page metadata"""
        metadata = {
            'domain': urlparse(url).netloc,
            'author': None,
            'publish_date': None,
            'tags': []
        }
        
        # Extract author
        author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                     soup.find('meta', attrs={'property': 'article:author'})
        if author_meta:
            metadata['author'] = author_meta.get('content', '')
        
        # Extract publish date
        date_meta = soup.find('meta', attrs={'property': 'article:published_time'}) or \
                   soup.find('meta', attrs={'name': 'publish_date'})
        if date_meta:
            metadata['publish_date'] = date_meta.get('content', '')
        
        # Extract tags/keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            keywords = keywords_meta.get('content', '')
            metadata['tags'] = [k.strip() for k in keywords.split(',')]
        
        return metadata


class KnowledgeScraper:
    """Main scraper orchestrator"""
    
    def __init__(self, respect_robots: bool = True, default_delay: float = 2.0):
        self.robots_checker = RobotsTxtChecker()
        self.rate_limiter = RateLimiter()
        self.scrubber = ContentScrubber()
        self.respect_robots = respect_robots
        self.default_delay = default_delay
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ZenithEdgeBot/1.0 (Educational Trading Research; +https://zenithedge.ai/bot)'
        })
    
    def scrape_url(self, url: str, source_config: Dict) -> Optional[ScrapedContent]:
        """Scrape a single URL"""
        domain = urlparse(url).netloc
        
        # Check robots.txt
        if self.respect_robots and not self.robots_checker.can_fetch(url):
            logger.info(f"Robots.txt disallows: {url}")
            return None
        
        # Rate limiting
        delay = source_config.get('rate_limit_seconds', self.default_delay)
        crawl_delay = self.robots_checker.get_crawl_delay(url)
        effective_delay = max(delay, crawl_delay)
        
        self.rate_limiter.wait_if_needed(domain, effective_delay)
        
        # Fetch page
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Scrub and extract content
            content = self.scrubber.scrub(response.text, url)
            
            return content
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            return None
    
    def discover_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """Extract URLs from XML sitemap"""
        urls = []
        try:
            response = self.session.get(sitemap_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            locs = soup.find_all('loc')
            
            for loc in locs:
                url = loc.get_text(strip=True)
                if url:
                    urls.append(url)
            
            logger.info(f"Discovered {len(urls)} URLs from sitemap: {sitemap_url}")
            
        except Exception as e:
            logger.error(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return urls
    
    def discover_urls_from_rss(self, feed_url: str) -> List[str]:
        """Extract URLs from RSS feed"""
        urls = []
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                if hasattr(entry, 'link'):
                    urls.append(entry.link)
            
            logger.info(f"Discovered {len(urls)} URLs from RSS: {feed_url}")
            
        except Exception as e:
            logger.error(f"Failed to parse RSS {feed_url}: {e}")
        
        return urls
    
    def crawl_source(
        self, 
        source_config: Dict,
        max_pages: int = 100,
        url_filter: Optional[callable] = None
    ) -> List[ScrapedContent]:
        """
        Crawl a complete source
        
        Args:
            source_config: Dict with 'base_url', 'seed_urls', 'sitemap', 'rss', etc.
            max_pages: Maximum pages to crawl
            url_filter: Optional function to filter URLs
        
        Returns:
            List of ScrapedContent objects
        """
        results = []
        crawled_urls = set()
        
        # Discover URLs
        urls_to_crawl = set()
        
        # Add seed URLs
        if 'seed_urls' in source_config:
            urls_to_crawl.update(source_config['seed_urls'])
        
        # Add sitemap URLs
        if 'sitemap' in source_config:
            sitemap_urls = self.discover_urls_from_sitemap(source_config['sitemap'])
            urls_to_crawl.update(sitemap_urls)
        
        # Add RSS URLs
        if 'rss' in source_config:
            rss_urls = self.discover_urls_from_rss(source_config['rss'])
            urls_to_crawl.update(rss_urls)
        
        # Apply filter
        if url_filter:
            urls_to_crawl = {u for u in urls_to_crawl if url_filter(u)}
        
        logger.info(f"Starting crawl: {len(urls_to_crawl)} URLs discovered")
        
        # Crawl URLs
        for i, url in enumerate(urls_to_crawl):
            if i >= max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break
            
            if url in crawled_urls:
                continue
            
            content = self.scrape_url(url, source_config)
            if content and len(content.main_text) > 200:
                results.append(content)
                crawled_urls.add(url)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{min(len(urls_to_crawl), max_pages)} pages")
        
        logger.info(f"Crawl complete: {len(results)} pages scraped")
        return results


# Predefined source configurations
SOURCE_CONFIGS = {
    'investopedia': {
        'base_url': 'https://www.investopedia.com',
        'sitemap': 'https://www.investopedia.com/sitemap_index.xml',
        'rate_limit_seconds': 3,
        'url_patterns': [r'/terms/', r'/articles/'],
    },
    'babypips': {
        'base_url': 'https://www.babypips.com',
        'seed_urls': [
            'https://www.babypips.com/learn/forex',
            'https://www.babypips.com/learn/forex/glossary',
        ],
        'rate_limit_seconds': 2,
    },
    'fxstreet': {
        'base_url': 'https://www.fxstreet.com',
        'seed_urls': [
            'https://www.fxstreet.com/education',
        ],
        'rate_limit_seconds': 3,
    },
    'tradingview_pine': {
        'base_url': 'https://www.tradingview.com',
        'seed_urls': [
            'https://www.tradingview.com/pine-script-docs/en/v5/Introduction.html',
        ],
        'rate_limit_seconds': 2,
    },
    'oanda': {
        'base_url': 'https://www.oanda.com',
        'seed_urls': [
            'https://www.oanda.com/forex-trading/learn',
        ],
        'rate_limit_seconds': 2,
    },
}
