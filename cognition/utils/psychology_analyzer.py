"""
Psychology Analyzer for Cognition Module
Analyzes trader text using spaCy, TextBlob, and NLTK to extract:
- Sentiment and emotional tone
- Confidence levels
- Cognitive biases
- Risk tolerance indicators
"""
import re
import logging
from typing import Dict, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# Lazy imports for NLP libraries
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER not available")

try:
    import spacy
    try:
        nlp = spacy.load('en_core_web_sm')
        SPACY_AVAILABLE = True
    except OSError:
        SPACY_AVAILABLE = False
        logger.warning("spaCy model not available")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available")

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    # Try to use stopwords, download if not available
    try:
        stopwords.words('english')
    except LookupError:
        logger.info("Downloading NLTK stopwords")
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available")


class PsychologyAnalyzer:
    """
    Analyzes trader psychology from text inputs
    """
    
    # Emotional tone keywords
    EMOTION_KEYWORDS = {
        'fearful': [
            'scared', 'afraid', 'nervous', 'worried', 'anxious', 'panic',
            'terrified', 'fear', 'frightened', 'hesitant', 'uncertain'
        ],
        'anxious': [
            'stress', 'tension', 'pressure', 'overwhelmed', 'unsure',
            'doubt', 'concern', 'uneasy', 'restless', 'apprehensive'
        ],
        'confident': [
            'confident', 'sure', 'certain', 'strong', 'positive', 'optimistic',
            'assured', 'conviction', 'trust', 'believe', 'solid'
        ],
        'overconfident': [
            'guaranteed', 'definitely', 'always win', 'can\'t lose', 'easy money',
            'foolproof', 'no doubt', 'certain winner', 'all in', 'yolo'
        ],
        'greedy': [
            'moon', 'lambo', 'rich quick', 'jackpot', 'fortune', 'massive gains',
            'huge profit', 'get rich', 'easy money', '10x', '100x'
        ],
        'disciplined': [
            'patient', 'disciplined', 'controlled', 'systematic', 'planned',
            'methodical', 'consistent', 'rule-based', 'strategic', 'measured'
        ],
    }
    
    # Cognitive bias indicators
    BIAS_PATTERNS = {
        'overconfidence': [
            r'\b(always|never|definitely|guaranteed|certain|100%|sure thing)\b',
            r'\b(can\'t lose|easy money|foolproof)\b',
        ],
        'revenge_trading': [
            r'\b(get back|revenge|make up for|recover)\b.*\b(loss|losses)\b',
            r'\b(double down|all in|increase size)\b.*\b(after|following)\b.*\b(loss)\b',
        ],
        'fomo': [
            r'\b(fomo|fear of missing|missing out|everyone else|don\'t want to miss)\b',
            r'\b(jumping in|chasing|can\'t miss this)\b',
        ],
        'anchoring': [
            r'\b(should be at|used to be|was trading at)\b',
            r'\b(stuck at|fixated on)\b.*\b(price|level)\b',
        ],
        'confirmation_bias': [
            r'\b(only looking|ignoring|dismissing)\b.*\b(signs|signals|data)\b',
            r'\b(confirms my|fits my|supports my)\b.*\b(view|thesis|opinion)\b',
        ],
        'recency_bias': [
            r'\b(recent|lately|just saw|last few)\b.*\b(winning|losing)\b',
            r'\b(hot streak|cold streak|on a roll)\b',
        ],
    }
    
    # Risk tolerance indicators
    RISK_KEYWORDS = {
        'risk_seeking': [
            'aggressive', 'bold', 'high risk', 'big size', 'all in',
            'maximum', 'push limits', 'go big', 'high leverage'
        ],
        'risk_averse': [
            'conservative', 'careful', 'small size', 'protect capital',
            'risk management', 'stop loss', 'cautious', 'safe'
        ],
    }
    
    # Patience indicators
    PATIENCE_KEYWORDS = {
        'impatient': [
            'quick', 'fast', 'now', 'immediately', 'can\'t wait',
            'hurry', 'rush', 'instant', 'right away'
        ],
        'patient': [
            'wait', 'patience', 'timing', 'right moment', 'no rush',
            'take time', 'let it develop', 'gradual', 'slowly'
        ],
    }
    
    def __init__(self):
        """Initialize the psychology analyzer"""
        self.vader_analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
        
    def analyze(self, text: str) -> Dict:
        """
        Comprehensive psychological analysis of trader text
        
        Args:
            text: Trader's written content (journal, chat, feedback)
            
        Returns:
            Dictionary with psychological metrics
        """
        if not text or not isinstance(text, str):
            return self._get_default_result()
        
        text = text.strip()
        if not text:
            return self._get_default_result()
        
        # Perform multiple analyses
        sentiment = self._analyze_sentiment(text)
        confidence = self._analyze_confidence(text)
        emotional_tone = self._detect_emotional_tone(text)
        entities = self._extract_entities(text)
        key_phrases = self._extract_key_phrases(text)
        biases = self._detect_biases(text)
        risk_tolerance = self._assess_risk_tolerance(text)
        patience = self._assess_patience(text)
        discipline = self._assess_discipline(text)
        
        return {
            'sentiment_score': sentiment,
            'confidence_level': confidence,
            'emotional_tone': emotional_tone,
            'key_phrases': key_phrases,
            'entities': entities,
            'detected_biases': biases['biases'],
            'bias_severity': biases['severity'],
            'risk_tolerance': risk_tolerance,
            'patience_score': patience,
            'discipline_score': discipline,
        }
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze overall sentiment: -1 (negative) to +1 (positive)
        Uses VADER primarily, TextBlob as fallback, keyword-based as last resort
        """
        sentiments = []
        
        # VADER sentiment (best for social/informal text)
        if self.vader_analyzer:
            vader_scores = self.vader_analyzer.polarity_scores(text)
            sentiments.append(vader_scores['compound'])
        
        # TextBlob sentiment
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
            except Exception as e:
                logger.debug(f"TextBlob error: {e}")
        
        # Keyword-based fallback
        if not sentiments:
            positive_words = ['good', 'great', 'excellent', 'win', 'profit', 'success', 'happy']
            negative_words = ['bad', 'terrible', 'loss', 'lose', 'fail', 'wrong', 'mistake']
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            total = pos_count + neg_count
            if total > 0:
                sentiments.append((pos_count - neg_count) / total)
            else:
                sentiments.append(0.0)
        
        return sum(sentiments) / len(sentiments) if sentiments else 0.0
    
    def _analyze_confidence(self, text: str) -> float:
        """
        Analyze confidence level: 0 (uncertain) to 1 (very confident)
        """
        text_lower = text.lower()
        
        # Confidence indicators
        high_confidence = ['confident', 'sure', 'certain', 'definitely', 'clearly', 'obviously']
        low_confidence = ['maybe', 'perhaps', 'possibly', 'might', 'unsure', 'not sure', 'doubt']
        hedge_words = ['kind of', 'sort of', 'i think', 'i guess', 'probably', 'seems like']
        
        high_count = sum(1 for word in high_confidence if word in text_lower)
        low_count = sum(1 for word in low_confidence if word in text_lower)
        hedge_count = sum(1 for phrase in hedge_words if phrase in text_lower)
        
        # Count exclamation marks (indicates emphasis/confidence)
        exclamation_count = text.count('!')
        
        # Calculate confidence score
        confidence = 0.5  # Start neutral
        confidence += high_count * 0.15
        confidence += exclamation_count * 0.05
        confidence -= low_count * 0.2
        confidence -= hedge_count * 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _detect_emotional_tone(self, text: str) -> str:
        """
        Detect primary emotional tone from text
        """
        text_lower = text.lower()
        
        scores = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            scores[emotion] = count
        
        # Return emotion with highest score, default to neutral
        if not any(scores.values()):
            return 'neutral'
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _extract_entities(self, text: str) -> Dict:
        """
        Extract named entities (symbols, strategies) using spaCy
        """
        entities = {'symbols': [], 'strategies': [], 'indicators': []}
        
        # Common trading symbols
        symbol_patterns = [
            r'\b(EUR/?USD|GBP/?USD|USD/?JPY|AUD/?USD|USD/?CAD|NZD/?USD|USD/?CHF)\b',
            r'\b(XAU/?USD|XAG/?USD|XTI/?USD|BTC/?USD|ETH/?USD)\b',
            r'\b(EUR|GBP|USD|JPY|AUD|CAD|NZD|CHF|GOLD|SILVER|OIL|BTC|ETH)\b',
        ]
        
        for pattern in symbol_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['symbols'].extend([m.upper() for m in matches])
        
        # Use spaCy if available
        if SPACY_AVAILABLE:
            try:
                doc = nlp(text)
                # Extract organizations (could be brokers, firms)
                entities['organizations'] = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
                # Extract money mentions
                entities['money'] = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
            except Exception as e:
                logger.debug(f"spaCy extraction error: {e}")
        
        # Remove duplicates
        entities['symbols'] = list(set(entities['symbols']))
        
        return entities
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract important phrases from text
        """
        phrases = []
        
        # Look for patterns like "I think...", "I believe...", "My strategy..."
        thought_patterns = [
            r'I (think|believe|feel|expect|hope|plan)\s+(.{10,50})',
            r'(My|The) (strategy|approach|plan|goal)\s+(.{10,50})',
        ]
        
        for pattern in thought_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                phrase = ' '.join(match).strip()
                if phrase:
                    phrases.append(phrase[:100])  # Limit length
        
        return phrases[:5]  # Return top 5
    
    def _detect_biases(self, text: str) -> Dict:
        """
        Detect cognitive biases in trader's thinking
        """
        detected_biases = []
        text_lower = text.lower()
        
        for bias_type, patterns in self.BIAS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected_biases.append(bias_type)
                    break  # Count each bias type once
        
        # Calculate severity based on number and type of biases
        severity = 0.0
        if detected_biases:
            # Overconfidence and revenge trading are more severe
            high_severity_biases = ['overconfidence', 'revenge_trading']
            severity_weights = [0.8 if bias in high_severity_biases else 0.4 for bias in detected_biases]
            severity = min(1.0, sum(severity_weights) / 2)
        
        return {
            'biases': list(set(detected_biases)),  # Remove duplicates
            'severity': severity
        }
    
    def _assess_risk_tolerance(self, text: str) -> float:
        """
        Assess risk tolerance: 0 (risk-averse) to 1 (risk-seeking)
        """
        text_lower = text.lower()
        
        seeking_count = sum(1 for keyword in self.RISK_KEYWORDS['risk_seeking'] 
                           if keyword in text_lower)
        averse_count = sum(1 for keyword in self.RISK_KEYWORDS['risk_averse'] 
                          if keyword in text_lower)
        
        if seeking_count == 0 and averse_count == 0:
            return 0.5  # Neutral
        
        total = seeking_count + averse_count
        risk_score = seeking_count / total if total > 0 else 0.5
        
        return risk_score
    
    def _assess_patience(self, text: str) -> float:
        """
        Assess patience level: 0 (impatient) to 1 (patient)
        """
        text_lower = text.lower()
        
        patient_count = sum(1 for keyword in self.PATIENCE_KEYWORDS['patient'] 
                           if keyword in text_lower)
        impatient_count = sum(1 for keyword in self.PATIENCE_KEYWORDS['impatient'] 
                             if keyword in text_lower)
        
        if patient_count == 0 and impatient_count == 0:
            return 0.5  # Neutral
        
        total = patient_count + impatient_count
        patience_score = patient_count / total if total > 0 else 0.5
        
        return patience_score
    
    def _assess_discipline(self, text: str) -> float:
        """
        Assess discipline level: 0 (undisciplined) to 1 (disciplined)
        """
        text_lower = text.lower()
        
        # Disciplined indicators
        discipline_words = [
            'plan', 'rules', 'strategy', 'systematic', 'consistent',
            'stop loss', 'risk management', 'journal', 'review'
        ]
        
        # Undisciplined indicators
        undisciplined_words = [
            'impulse', 'random', 'guess', 'gamble', 'wing it',
            'no plan', 'ignore', 'skip', 'broke rules'
        ]
        
        discipline_count = sum(1 for word in discipline_words if word in text_lower)
        undiscipline_count = sum(1 for word in undisciplined_words if word in text_lower)
        
        if discipline_count == 0 and undiscipline_count == 0:
            return 0.5  # Neutral
        
        total = discipline_count + undiscipline_count
        discipline_score = discipline_count / total if total > 0 else 0.5
        
        return discipline_score
    
    def _get_default_result(self) -> Dict:
        """Return default result for empty/invalid input"""
        return {
            'sentiment_score': 0.0,
            'confidence_level': 0.5,
            'emotional_tone': 'neutral',
            'key_phrases': [],
            'entities': {},
            'detected_biases': [],
            'bias_severity': 0.0,
            'risk_tolerance': 0.5,
            'patience_score': 0.5,
            'discipline_score': 0.5,
        }


# Convenience function
def analyze_trader_text(text: str) -> Dict:
    """
    Analyze trader text and return psychological metrics
    
    Args:
        text: Trader's written content
        
    Returns:
        Dictionary with psychological analysis
    """
    analyzer = PsychologyAnalyzer()
    return analyzer.analyze(text)
