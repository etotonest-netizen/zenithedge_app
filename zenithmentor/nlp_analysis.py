"""
NLP Analysis - Journal sentiment and bias detection
Uses spaCy, TextBlob, and NLTK for psychological analysis
"""
import re
from typing import Dict, List, Tuple
from textblob import TextBlob
import nltk
from collections import Counter

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

from nltk.sentiment import SentimentIntensityAnalyzer


class JournalAnalyzer:
    """Analyzes trader journal entries for psychological patterns."""
    
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        
        # Trading-specific bias indicators
        self.overconfidence_keywords = [
            'definitely', 'certain', 'guaranteed', 'no doubt', 'sure thing',
            'can\'t lose', 'easy money', 'obvious', 'clearly', 'perfect setup'
        ]
        
        self.revenge_keywords = [
            'revenge', 'get back', 'make up for', 'recover', 'payback',
            'shouldn\'t have', 'unfair', 'unlucky', 'robbed'
        ]
        
        self.fear_keywords = [
            'scared', 'afraid', 'worried', 'nervous', 'anxious',
            'panic', 'terrified', 'hesitant', 'unsure', 'doubt'
        ]
        
        self.greed_keywords = [
            'more', 'bigger', 'maximize', 'double down', 'all in',
            'missed out', 'FOMO', 'regret not taking'
        ]
        
        self.discipline_positive_keywords = [
            'plan', 'checklist', 'rules', 'patient', 'waited',
            'followed', 'disciplined', 'systematic', 'process'
        ]
        
        self.discipline_negative_keywords = [
            'impulsive', 'rushed', 'ignored', 'broke', 'violated',
            'didn\'t follow', 'emotional', 'tilted', 'frustrated'
        ]
    
    def analyze_journal_entry(self, text: str) -> Dict:
        """
        Comprehensive analysis of a journal entry.
        
        Returns:
            Dict with sentiment, bias scores, and detected patterns
        """
        if not text or len(text.strip()) < 10:
            return {
                'quality_score': 0,
                'sentiment': 'neutral',
                'sentiment_score': 0,
                'overconfidence_score': 0,
                'revenge_trading_risk': 0,
                'fear_level': 0,
                'greed_level': 0,
                'discipline_score': 50,
                'word_count': 0,
                'warnings': ['Journal entry too short'],
            }
        
        text_lower = text.lower()
        
        # Sentiment analysis
        sentiment_data = self._analyze_sentiment(text)
        
        # Bias detection
        overconfidence = self._detect_overconfidence(text_lower)
        revenge_risk = self._detect_revenge_trading(text_lower)
        fear_level = self._detect_fear(text_lower)
        greed_level = self._detect_greed(text_lower)
        
        # Discipline analysis
        discipline_score = self._analyze_discipline(text_lower)
        
        # Quality metrics
        word_count = len(text.split())
        sentence_count = len(nltk.sent_tokenize(text))
        
        quality_score = self._calculate_quality_score(
            word_count, sentence_count, discipline_score, overconfidence, revenge_risk
        )
        
        # Generate warnings
        warnings = []
        if overconfidence > 60:
            warnings.append("High overconfidence detected - verify your analysis")
        if revenge_risk > 70:
            warnings.append("Possible revenge trading mindset - take a break")
        if fear_level > 70:
            warnings.append("High fear levels - review your risk management")
        if greed_level > 70:
            warnings.append("Greed indicators detected - stick to your plan")
        if discipline_score < 40:
            warnings.append("Discipline concerns - review your rules")
        
        return {
            'quality_score': quality_score,
            'sentiment': sentiment_data['label'],
            'sentiment_score': sentiment_data['score'],
            'overconfidence_score': overconfidence,
            'revenge_trading_risk': revenge_risk,
            'fear_level': fear_level,
            'greed_level': greed_level,
            'discipline_score': discipline_score,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'warnings': warnings,
        }
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze emotional sentiment."""
        # VADER sentiment
        vader_scores = self.sia.polarity_scores(text)
        compound = vader_scores['compound']
        
        # TextBlob sentiment
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        # Average the two
        avg_score = (compound + polarity) / 2
        
        if avg_score > 0.2:
            label = 'positive'
        elif avg_score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': avg_score,
            'label': label,
            'vader_compound': compound,
            'textblob_polarity': polarity,
        }
    
    def _detect_overconfidence(self, text: str) -> int:
        """
        Detect overconfidence indicators.
        
        Returns:
            Score 0-100
        """
        count = sum(1 for keyword in self.overconfidence_keywords if keyword in text)
        
        # Normalize to 0-100 scale
        score = min(100, count * 20)
        
        return score
    
    def _detect_revenge_trading(self, text: str) -> int:
        """
        Detect revenge trading mindset.
        
        Returns:
            Risk score 0-100
        """
        count = sum(1 for keyword in self.revenge_keywords if keyword in text)
        
        # Check for specific patterns
        if 'shouldn\'t have' in text and 'loss' in text:
            count += 2
        
        if 'get back' in text or 'make up' in text:
            count += 2
        
        score = min(100, count * 15)
        
        return score
    
    def _detect_fear(self, text: str) -> int:
        """Detect fear/anxiety levels."""
        count = sum(1 for keyword in self.fear_keywords if keyword in text)
        score = min(100, count * 15)
        return score
    
    def _detect_greed(self, text: str) -> int:
        """Detect greed/FOMO indicators."""
        count = sum(1 for keyword in self.greed_keywords if keyword in text)
        
        # Pattern matching
        if 'fomo' in text:
            count += 2
        if 'missed' in text and 'opportunity' in text:
            count += 1
        
        score = min(100, count * 15)
        return score
    
    def _analyze_discipline(self, text: str) -> int:
        """
        Analyze discipline level from language.
        
        Returns:
            Score 0-100
        """
        positive_count = sum(1 for keyword in self.discipline_positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.discipline_negative_keywords if keyword in text)
        
        # Base score
        base_score = 50
        
        # Adjust based on keyword counts
        score = base_score + (positive_count * 10) - (negative_count * 10)
        
        # Clip to 0-100
        score = max(0, min(100, score))
        
        return score
    
    def _calculate_quality_score(self, word_count, sentence_count, 
                                 discipline_score, overconfidence, revenge_risk) -> int:
        """
        Calculate overall journal quality.
        
        Returns:
            Score 0-100
        """
        # Length component (0-30 points)
        if word_count < 20:
            length_score = word_count
        elif word_count < 100:
            length_score = 20 + ((word_count - 20) / 80) * 10
        else:
            length_score = 30
        
        # Structure component (0-20 points)
        if sentence_count >= 3:
            structure_score = 20
        else:
            structure_score = sentence_count * 6
        
        # Discipline component (0-30 points)
        discipline_component = discipline_score * 0.3
        
        # Bias penalty (0-20 points deduction)
        bias_penalty = (overconfidence + revenge_risk) / 10
        bias_component = max(0, 20 - bias_penalty)
        
        total = length_score + structure_score + discipline_component + bias_component
        
        return min(100, int(total))
    
    def analyze_batch(self, journal_entries: List[str]) -> Dict:
        """
        Analyze multiple journal entries to detect patterns.
        
        Returns:
            Aggregate analysis with trends
        """
        if not journal_entries:
            return {'entry_count': 0}
        
        analyses = [self.analyze_journal_entry(entry) for entry in journal_entries]
        
        # Aggregate metrics
        avg_quality = sum(a['quality_score'] for a in analyses) / len(analyses)
        avg_discipline = sum(a['discipline_score'] for a in analyses) / len(analyses)
        avg_overconfidence = sum(a['overconfidence_score'] for a in analyses) / len(analyses)
        avg_revenge_risk = sum(a['revenge_trading_risk'] for a in analyses) / len(analyses)
        
        # Sentiment distribution
        sentiment_counts = Counter(a['sentiment'] for a in analyses)
        
        # Warning aggregation
        all_warnings = []
        for a in analyses:
            all_warnings.extend(a['warnings'])
        warning_counts = Counter(all_warnings)
        
        return {
            'entry_count': len(journal_entries),
            'avg_quality_score': avg_quality,
            'avg_discipline_score': avg_discipline,
            'avg_overconfidence': avg_overconfidence,
            'avg_revenge_risk': avg_revenge_risk,
            'sentiment_distribution': dict(sentiment_counts),
            'common_warnings': warning_counts.most_common(5),
            'trend': self._determine_trend(analyses),
        }
    
    def _determine_trend(self, analyses: List[Dict]) -> str:
        """Determine if metrics are improving, declining, or stable."""
        if len(analyses) < 3:
            return 'insufficient_data'
        
        # Look at quality scores over time
        recent_quality = analyses[-3:]
        older_quality = analyses[:3] if len(analyses) > 5 else analyses[:2]
        
        recent_avg = sum(a['quality_score'] for a in recent_quality) / len(recent_quality)
        older_avg = sum(a['quality_score'] for a in older_quality) / len(older_quality)
        
        diff = recent_avg - older_avg
        
        if diff > 10:
            return 'improving'
        elif diff < -10:
            return 'declining'
        else:
            return 'stable'


class RationaleValidator:
    """Validates trade rationales for completeness and technical validity."""
    
    REQUIRED_ELEMENTS = {
        'entry_reason': ['why', 'because', 'signal', 'setup', 'pattern'],
        'risk_mgmt': ['stop', 'risk', 'target', 'r:r', 'reward'],
        'context': ['trend', 'support', 'resistance', 'timeframe', 'session'],
    }
    
    def validate_rationale(self, rationale: str) -> Dict:
        """
        Validate completeness of trade rationale.
        
        Returns:
            Dict with validation results
        """
        if not rationale or len(rationale.strip()) < 20:
            return {
                'is_valid': False,
                'completeness_score': 0,
                'missing_elements': list(self.REQUIRED_ELEMENTS.keys()),
                'feedback': 'Rationale too short. Explain your trade setup thoroughly.',
            }
        
        rationale_lower = rationale.lower()
        
        # Check for required elements
        found_elements = {}
        for element, keywords in self.REQUIRED_ELEMENTS.items():
            found = any(keyword in rationale_lower for keyword in keywords)
            found_elements[element] = found
        
        missing = [elem for elem, found in found_elements.items() if not found]
        completeness = (len(found_elements) - len(missing)) / len(found_elements) * 100
        
        # Generate feedback
        if completeness >= 80:
            feedback = "Excellent trade documentation."
        elif completeness >= 60:
            feedback = f"Good rationale, but consider adding: {', '.join(missing)}"
        else:
            feedback = f"Incomplete rationale. Please include: {', '.join(missing)}"
        
        return {
            'is_valid': completeness >= 60,
            'completeness_score': completeness,
            'missing_elements': missing,
            'found_elements': [k for k, v in found_elements.items() if v],
            'feedback': feedback,
        }


# Singleton instances
journal_analyzer = JournalAnalyzer()
rationale_validator = RationaleValidator()
