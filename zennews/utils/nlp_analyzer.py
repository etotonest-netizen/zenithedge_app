"""
NLP Sentiment & Entity Analyzer for ZenNews
Performs sentiment analysis and entity extraction from news text
"""
import re
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np

# Import NLP libraries with fallbacks
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("TextBlob not available - install with: pip install textblob")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("VADER not available - install with: pip install vaderSentiment")

try:
    import spacy
    try:
        nlp_model = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        SPACY_AVAILABLE = False
        logging.warning("spaCy model not found - run: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - install with: pip install spacy")

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """
    Analyzes financial news for sentiment and extracts entities
    """
    
    # Currency pairs and symbols to detect
    FOREX_SYMBOLS = {
        'EUR/USD': 'EURUSD', 'EUR': 'EURUSD', 'EURO': 'EURUSD',
        'GBP/USD': 'GBPUSD', 'GBP': 'GBPUSD', 'POUND': 'GBPUSD', 'STERLING': 'GBPUSD', 'CABLE': 'GBPUSD',
        'USD/JPY': 'USDJPY', 'JPY': 'USDJPY', 'YEN': 'USDJPY',
        'AUD/USD': 'AUDUSD', 'AUD': 'AUDUSD', 'AUSSIE': 'AUDUSD',
        'USD/CAD': 'USDCAD', 'CAD': 'USDCAD', 'LOONIE': 'USDCAD',
        'NZD/USD': 'NZDUSD', 'NZD': 'NZDUSD', 'KIWI': 'NZDUSD',
        'USD/CHF': 'USDCHF', 'CHF': 'USDCHF', 'FRANC': 'USDCHF', 'SWISSY': 'USDCHF',
        'GOLD': 'XAUUSD', 'XAU': 'XAUUSD',
        'SILVER': 'XAGUSD', 'XAG': 'XAGUSD',
        'OIL': 'USOIL', 'CRUDE': 'USOIL', 'BRENT': 'USOIL', 'WTI': 'USOIL',
        'BITCOIN': 'BTCUSD', 'BTC': 'BTCUSD',
        'ETHEREUM': 'ETHUSD', 'ETH': 'ETHUSD',
        'S&P': 'SPX500', 'SPX': 'SPX500',
        'DOW': 'US30', 'NASDAQ': 'NAS100',
    }
    
    # High-impact keywords
    HIGH_IMPACT_KEYWORDS = [
        'interest rate', 'central bank', 'fed', 'ecb', 'boe',
        'inflation', 'cpi', 'ppi', 'gdp', 'unemployment',
        'nfp', 'non-farm', 'fomc', 'rate hike', 'rate cut',
        'quantitative easing', 'qe', 'monetary policy',
        'recession', 'crisis', 'emergency', 'breaking'
    ]
    
    # Medium-impact keywords
    MEDIUM_IMPACT_KEYWORDS = [
        'policy', 'speech', 'statement', 'minutes', 'meeting',
        'forecast', 'outlook', 'guidance', 'target', 'expectations',
        'retail sales', 'consumer confidence', 'housing starts',
        'trade balance', 'manufacturing', 'services pmi'
    ]
    
    # Topic keywords
    TOPIC_KEYWORDS = {
        'Interest Rates': ['interest rate', 'rate hike', 'rate cut', 'basis points', 'bps'],
        'Inflation': ['inflation', 'cpi', 'ppi', 'deflation', 'price pressure'],
        'Employment': ['unemployment', 'jobs', 'nfp', 'non-farm payroll', 'jobless'],
        'Central Bank': ['fed', 'ecb', 'boe', 'boj', 'central bank', 'fomc', 'mpc'],
        'GDP Growth': ['gdp', 'growth', 'expansion', 'contraction', 'recession'],
        'Trade': ['trade', 'tariff', 'export', 'import', 'trade balance'],
        'Oil & Energy': ['oil', 'crude', 'energy', 'opec', 'petroleum'],
        'Crypto': ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'digital currency'],
        'Geopolitics': ['war', 'conflict', 'sanction', 'election', 'political'],
    }
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, headline: str, description: str = "") -> Dict:
        """
        Perform complete analysis on news text
        
        Args:
            headline: News headline
            description: News description/summary
            
        Returns:
            Dict with sentiment, symbols, impact, and topics
        """
        text = f"{headline}. {description}".strip()
        
        # Get sentiment
        sentiment = self.get_sentiment(text)
        
        # Extract symbols
        symbols = self.extract_symbols(text)
        
        # Determine impact level
        impact_level = self.determine_impact(text)
        
        # Extract topics
        topics = self.extract_topics(text)
        
        return {
            'sentiment': sentiment,
            'symbols': symbols if symbols else ['GENERAL'],
            'impact_level': impact_level,
            'topics': topics,
        }
    
    def get_sentiment(self, text: str) -> float:
        """
        Calculate sentiment score using available methods
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score from -1.0 to 1.0
        """
        sentiments = []
        
        # VADER sentiment (best for social media and news)
        if self.vader_analyzer:
            vader_scores = self.vader_analyzer.polarity_scores(text)
            sentiments.append(vader_scores['compound'])
        
        # TextBlob sentiment
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
            except Exception as e:
                self.logger.debug(f"TextBlob error: {e}")
        
        # Simple keyword-based sentiment as fallback
        if not sentiments:
            sentiments.append(self._keyword_sentiment(text))
        
        # Return average sentiment
        return float(np.mean(sentiments))
    
    def _keyword_sentiment(self, text: str) -> float:
        """
        Simple keyword-based sentiment analysis (fallback method)
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score from -1.0 to 1.0
        """
        text_lower = text.lower()
        
        positive_words = ['gain', 'rise', 'up', 'surge', 'rally', 'strong', 'boost', 
                         'improve', 'positive', 'optimis', 'confidence', 'growth']
        negative_words = ['fall', 'drop', 'down', 'plunge', 'weak', 'decline', 'crisis',
                         'concern', 'risk', 'negative', 'pessimis', 'fear', 'worry']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract trading symbols from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected symbols
        """
        text_upper = text.upper()
        detected_symbols = set()
        
        # Check for each known symbol/currency
        for keyword, symbol in self.FOREX_SYMBOLS.items():
            if keyword.upper() in text_upper or keyword.replace('/', '') in text_upper:
                detected_symbols.add(symbol)
        
        # Use spaCy for more sophisticated entity extraction if available
        if SPACY_AVAILABLE:
            try:
                doc = nlp_model(text)
                for ent in doc.ents:
                    if ent.label_ in ['ORG', 'GPE', 'MONEY']:
                        # Try to match entity to known symbols
                        ent_upper = ent.text.upper()
                        for keyword, symbol in self.FOREX_SYMBOLS.items():
                            if keyword.upper() in ent_upper:
                                detected_symbols.add(symbol)
            except Exception as e:
                self.logger.debug(f"spaCy extraction error: {e}")
        
        return list(detected_symbols)
    
    def determine_impact(self, text: str) -> str:
        """
        Determine impact level based on keywords
        
        Args:
            text: Text to analyze
            
        Returns:
            Impact level: 'high', 'medium', or 'low'
        """
        text_lower = text.lower()
        
        # Check for high-impact keywords
        high_impact_count = sum(
            1 for keyword in self.HIGH_IMPACT_KEYWORDS 
            if keyword in text_lower
        )
        
        if high_impact_count >= 2:
            return 'high'
        elif high_impact_count >= 1:
            return 'high'
        
        # Check for medium-impact keywords
        medium_impact_count = sum(
            1 for keyword in self.MEDIUM_IMPACT_KEYWORDS 
            if keyword in text_lower
        )
        
        if medium_impact_count >= 2:
            return 'medium'
        elif medium_impact_count >= 1:
            return 'medium'
        
        return 'low'
    
    def extract_topics(self, text: str) -> List[str]:
        """
        Extract topics/categories from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected topics
        """
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics if detected_topics else ['General Market']
    
    def batch_analyze(self, news_items: List[Dict]) -> List[Dict]:
        """
        Analyze multiple news items in batch
        
        Args:
            news_items: List of news dicts with 'headline' and optional 'description'
            
        Returns:
            List of analyzed news items with added analysis fields
        """
        analyzed_items = []
        
        for item in news_items:
            try:
                headline = item.get('headline', '')
                description = item.get('description', '')
                
                analysis = self.analyze(headline, description)
                
                # Merge analysis into item
                item.update({
                    'sentiment': analysis['sentiment'],
                    'symbols': analysis['symbols'],
                    'impact_level': analysis['impact_level'],
                    'topics': analysis['topics'],
                })
                
                analyzed_items.append(item)
                
            except Exception as e:
                self.logger.error(f"Error analyzing item: {str(e)}")
                continue
        
        return analyzed_items


# Convenience function
def analyze_news_text(headline: str, description: str = "") -> Dict:
    """
    Quick analysis of news text
    
    Args:
        headline: News headline
        description: Optional description
        
    Returns:
        Analysis dict with sentiment, symbols, impact, topics
    """
    analyzer = NewsAnalyzer()
    return analyzer.analyze(headline, description)
