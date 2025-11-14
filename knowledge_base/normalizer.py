"""
Content Normalizer - NLP Processing for Knowledge Base
Uses spaCy for NER, TextBlob for sentiment, extracts canonical terms
"""
import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter
import hashlib

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - using fallback term extraction")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("TextBlob not available - skipping sentiment analysis")

logger = logging.getLogger(__name__)


@dataclass
class NormalizedEntry:
    """Normalized knowledge base entry ready for database"""
    term: str
    aliases: List[str]
    summary: str
    definition: str
    examples: List[str]
    
    category: str
    difficulty: str
    asset_classes: List[str]
    
    quality_score: float
    relevance_score: float
    completeness_score: float
    
    metadata: Dict


class TradingTermExtractor:
    """Extract and normalize trading terminology"""
    
    # Known trading concept patterns
    TRADING_TERMS = {
        # SMC/ICT
        'order block': ['ob', 'orderblock', 'demand zone', 'supply zone'],
        'fair value gap': ['fvg', 'imbalance', 'inefficiency'],
        'liquidity sweep': ['stop hunt', 'liquidity grab', 'sweep'],
        'break of structure': ['bos', 'break of structure', 'structural break'],
        'change of character': ['choch', 'change of character', 'character change'],
        'market structure shift': ['mss', 'structure shift'],
        'optimal trade entry': ['ote', 'optimal entry', 'entry zone'],
        'breaker block': ['breaker', 'failed order block'],
        
        # Technical Analysis
        'support': ['support level', 'demand', 'floor'],
        'resistance': ['resistance level', 'supply', 'ceiling'],
        'trend': ['trending', 'directional move'],
        'consolidation': ['range', 'sideways', 'chop'],
        'breakout': ['break out', 'breakthrough'],
        'retracement': ['pullback', 'correction'],
        'fibonacci': ['fib', 'fibonacci retracement'],
        'moving average': ['ma', 'ema', 'sma'],
        
        # Order Flow
        'volume profile': ['vp', 'volume analysis'],
        'point of control': ['poc', 'value area'],
        'delta': ['volume delta', 'cumulative delta'],
        'absorption': ['volume absorption', 'iceberg order'],
        
        # Risk Management
        'stop loss': ['sl', 'stop', 'protective stop'],
        'take profit': ['tp', 'target', 'profit target'],
        'risk reward': ['rr', 'risk-reward ratio', 'r:r'],
        'position sizing': ['lot size', 'size calculation'],
        'drawdown': ['dd', 'equity drawdown'],
    }
    
    CATEGORIES = {
        'smc': ['order block', 'fair value gap', 'liquidity sweep', 'breaker block'],
        'ict': ['optimal trade entry', 'break of structure', 'change of character', 'market structure shift'],
        'ta': ['support', 'resistance', 'trend', 'consolidation', 'fibonacci', 'moving average'],
        'orderflow': ['volume profile', 'point of control', 'delta', 'absorption'],
        'risk': ['stop loss', 'take profit', 'risk reward', 'position sizing', 'drawdown'],
    }
    
    DIFFICULTY_KEYWORDS = {
        'intro': ['basic', 'beginner', 'introduction', 'fundamental', 'simple'],
        'intermediate': ['strategy', 'technique', 'approach', 'method'],
        'advanced': ['advanced', 'complex', 'sophisticated', 'institutional'],
        'expert': ['expert', 'professional', 'mastery', 'algorithmic'],
    }
    
    ASSET_KEYWORDS = {
        'forex': ['forex', 'fx', 'currency', 'pair', 'eurusd', 'gbpusd'],
        'crypto': ['crypto', 'bitcoin', 'btc', 'ethereum', 'cryptocurrency'],
        'stocks': ['stock', 'equity', 'shares', 'nasdaq', 'spy'],
        'futures': ['futures', 'contract', 'es', 'nq'],
        'commodities': ['gold', 'oil', 'commodity', 'xauusd'],
    }
    
    def __init__(self):
        # Load spaCy model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
                logger.info("Loaded spaCy model: en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found - use: python -m spacy download en_core_web_sm")
    
    def extract_canonical_term(self, title: str, text: str) -> Tuple[str, List[str]]:
        """
        Extract canonical term and aliases from content
        Returns: (canonical_term, [aliases])
        """
        # First check if title contains known term
        title_lower = title.lower()
        
        for canonical, aliases in self.TRADING_TERMS.items():
            if canonical in title_lower or any(alias in title_lower for alias in aliases):
                return canonical.title(), aliases
        
        # Extract from first sentence/heading
        if self.nlp:
            doc = self.nlp(title)
            # Get noun phrases
            noun_phrases = [chunk.text for chunk in doc.noun_chunks]
            if noun_phrases:
                return noun_phrases[0].title(), []
        
        # Fallback: use title
        cleaned_title = re.sub(r'\s*[:-]\s*.*$', '', title).strip()
        return cleaned_title, []
    
    def categorize(self, term: str, text: str) -> str:
        """Determine category for term"""
        term_lower = term.lower()
        text_lower = text.lower()
        
        # Check direct term mapping
        for category, terms in self.CATEGORIES.items():
            if any(t in term_lower for t in terms):
                return category
        
        # Check text content
        category_scores = {}
        for category, terms in self.CATEGORIES.items():
            score = sum(1 for t in terms if t in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'other'
    
    def assess_difficulty(self, text: str) -> str:
        """Assess content difficulty level"""
        text_lower = text.lower()
        
        scores = {}
        for difficulty, keywords in self.DIFFICULTY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[difficulty] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        # Fallback: based on text complexity
        sentences = text.split('.')
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 10
        
        if avg_length < 12:
            return 'intro'
        elif avg_length < 18:
            return 'intermediate'
        elif avg_length < 25:
            return 'advanced'
        else:
            return 'expert'
    
    def detect_asset_classes(self, text: str) -> List[str]:
        """Detect applicable asset classes"""
        text_lower = text.lower()
        
        detected = []
        for asset_class, keywords in self.ASSET_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(asset_class)
        
        # Default to 'any' if no specific class detected
        return detected if detected else ['any']


class ContentNormalizer:
    """Main content normalization pipeline"""
    
    def __init__(self):
        self.term_extractor = TradingTermExtractor()
    
    def extract_summary(self, text: str, max_sentences: int = 2) -> str:
        """Extract concise summary from text (1-2 sentences)"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return text[:200]
        
        # Return first N sentences
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)
        
        if not summary.endswith('.'):
            summary += '.'
        
        return summary
    
    def extract_definition(self, text: str, max_paragraphs: int = 5) -> str:
        """Extract detailed definition (3-5 paragraphs)"""
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
        
        # Return first N paragraphs
        definition_paragraphs = paragraphs[:max_paragraphs]
        return '\n\n'.join(definition_paragraphs)
    
    def extract_examples(self, examples_list: List[str], text: str) -> List[str]:
        """Extract usage examples"""
        # Use provided examples
        if examples_list:
            return examples_list[:3]  # Max 3 examples
        
        # Try to find example sections in text
        example_pattern = r'(?:example|for instance|such as)[:\s]+([^.]+\.)'
        matches = re.findall(example_pattern, text, re.IGNORECASE)
        
        return matches[:3] if matches else []
    
    def calculate_quality_score(
        self, 
        text: str, 
        examples: List[str],
        source_trust: str = 'medium'
    ) -> float:
        """Calculate quality score (0.0-1.0)"""
        score = 0.5  # Base score
        
        # Content length bonus
        if len(text) > 500:
            score += 0.1
        if len(text) > 1000:
            score += 0.1
        
        # Examples bonus
        if examples:
            score += 0.1
        if len(examples) >= 2:
            score += 0.05
        
        # Source trust bonus
        trust_bonus = {'high': 0.2, 'medium': 0.1, 'low': 0.0}
        score += trust_bonus.get(source_trust, 0.0)
        
        # Readability check (simple heuristic)
        sentences = text.split('.')
        if sentences:
            avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 < avg_words < 25:  # Good readability range
                score += 0.05
        
        return min(1.0, score)
    
    def calculate_relevance_score(self, term: str, text: str) -> float:
        """Calculate trading relevance score"""
        text_lower = text.lower()
        
        # Check for trading-specific terms
        trading_keywords = [
            'price', 'market', 'trade', 'trading', 'trend', 'analysis',
            'support', 'resistance', 'breakout', 'entry', 'exit', 'strategy'
        ]
        
        hits = sum(1 for kw in trading_keywords if kw in text_lower)
        relevance = min(1.0, hits / 5.0)  # Normalize
        
        return relevance
    
    def calculate_completeness_score(
        self,
        summary: str,
        definition: str,
        examples: List[str]
    ) -> float:
        """Calculate completeness score"""
        score = 0.0
        
        if summary and len(summary) > 50:
            score += 0.4
        
        if definition and len(definition) > 200:
            score += 0.4
        
        if examples:
            score += 0.2
        
        return score
    
    def normalize(
        self,
        scraped_content,
        source_trust: str = 'medium'
    ) -> Optional[NormalizedEntry]:
        """
        Normalize scraped content into KB entry
        
        Args:
            scraped_content: ScrapedContent object from scraper
            source_trust: Source trust level (high/medium/low)
        
        Returns:
            NormalizedEntry or None if content inadequate
        """
        # Extract canonical term
        term, aliases = self.term_extractor.extract_canonical_term(
            scraped_content.title,
            scraped_content.main_text
        )
        
        # Categorize
        category = self.term_extractor.categorize(term, scraped_content.main_text)
        
        # Assess difficulty
        difficulty = self.term_extractor.assess_difficulty(scraped_content.main_text)
        
        # Detect asset classes
        asset_classes = self.term_extractor.detect_asset_classes(scraped_content.main_text)
        
        # Extract summary
        summary = self.extract_summary(scraped_content.main_text)
        
        # Extract definition
        definition = self.extract_definition(scraped_content.main_text)
        
        # Extract examples
        examples = self.extract_examples(
            scraped_content.examples,
            scraped_content.main_text
        )
        
        # Calculate quality metrics
        quality_score = self.calculate_quality_score(
            scraped_content.main_text,
            examples,
            source_trust
        )
        
        relevance_score = self.calculate_relevance_score(term, scraped_content.main_text)
        
        completeness_score = self.calculate_completeness_score(
            summary,
            definition,
            examples
        )
        
        # Quality threshold
        if quality_score < 0.3 or relevance_score < 0.3:
            logger.info(f"Skipping low-quality content: {term} (Q:{quality_score:.2f}, R:{relevance_score:.2f})")
            return None
        
        # Build metadata
        metadata = {
            'crawl_timestamp': scraped_content.crawl_timestamp.isoformat(),
            'original_title': scraped_content.title,
            **scraped_content.metadata
        }
        
        return NormalizedEntry(
            term=term,
            aliases=aliases,
            summary=summary,
            definition=definition,
            examples=examples,
            category=category,
            difficulty=difficulty,
            asset_classes=asset_classes,
            quality_score=quality_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            metadata=metadata
        )


class RelationshipDetector:
    """Detect relationships between trading concepts"""
    
    # Relationship patterns
    RELATIONSHIP_PATTERNS = {
        'related_to': [
            ('order block', 'fair value gap'),
            ('support', 'resistance'),
            ('trend', 'breakout'),
            ('liquidity sweep', 'stop loss'),
        ],
        'is_subconcept_of': [
            ('order block', 'market structure'),
            ('fair value gap', 'imbalance'),
            ('fibonacci', 'technical analysis'),
        ],
        'prerequisite_for': [
            ('trend', 'breakout'),
            ('support', 'entry'),
        ],
        'common_with': [
            ('liquidity sweep', 'fair value gap'),
            ('order block', 'break of structure'),
        ],
    }
    
    def detect_relationships(
        self,
        entries: List[NormalizedEntry]
    ) -> List[Tuple[str, str, str, float]]:
        """
        Detect relationships between entries
        
        Returns:
            List of (source_term, target_term, relationship_type, strength)
        """
        relationships = []
        
        # Build term index
        term_to_entry = {e.term.lower(): e for e in entries}
        
        # Check predefined patterns
        for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
            for source_term, target_term in patterns:
                if source_term in term_to_entry and target_term in term_to_entry:
                    relationships.append((source_term, target_term, rel_type, 0.9))
        
        # Detect co-occurrence in definitions
        for i, entry1 in enumerate(entries):
            for entry2 in entries[i+1:]:
                # Check if terms mention each other
                if entry2.term.lower() in entry1.definition.lower():
                    relationships.append((
                        entry1.term,
                        entry2.term,
                        'related_to',
                        0.6
                    ))
                elif entry1.term.lower() in entry2.definition.lower():
                    relationships.append((
                        entry2.term,
                        entry1.term,
                        'related_to',
                        0.6
                    ))
        
        # Deduplicate
        seen = set()
        unique_relationships = []
        for rel in relationships:
            key = (rel[0], rel[1], rel[2])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        return unique_relationships
