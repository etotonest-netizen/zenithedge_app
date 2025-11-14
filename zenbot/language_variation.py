"""
Language Variation Engine for ZenithEdge Narratives

Provides advanced linguistic transformation capabilities to ensure
every generated narrative is unique in structure, tone, and phrasing.

Capabilities:
- Sentence structure mutation (subject/object swapping)
- Synonym rotation using WordNet
- Tone modulation (analytical → neutral → cautious)
- Sentence ordering shuffles
- Lexical diversity scoring

Author: ZenithEdge Team
Version: 1.0
"""

import logging
import random
import re
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class LanguageVariationEngine:
    """
    Advanced linguistic transformation for narrative uniqueness.
    
    Transforms sentences while preserving semantic meaning to achieve
    95%+ linguistic diversity across generated narratives.
    """
    
    # Comprehensive synonym mappings (WordNet-inspired)
    SYNONYM_SETS = {
        # Market behavior verbs
        'shows': ['displays', 'exhibits', 'demonstrates', 'reveals', 'indicates', 'suggests'],
        'suggests': ['indicates', 'implies', 'hints at', 'points to', 'signals'],
        'indicates': ['shows', 'demonstrates', 'reveals', 'points to', 'suggests'],
        'emerges': ['develops', 'materializes', 'appears', 'surfaces', 'arises'],
        'forms': ['develops', 'materializes', 'takes shape', 'crystallizes', 'coalesces'],
        
        # Intensity adjectives
        'strong': ['robust', 'solid', 'firm', 'pronounced', 'notable'],
        'weak': ['soft', 'muted', 'subdued', 'tepid', 'modest'],
        'building': ['developing', 'emerging', 'growing', 'intensifying', 'strengthening'],
        'fading': ['waning', 'diminishing', 'weakening', 'subsiding', 'receding'],
        
        # Structural nouns
        'pattern': ['structure', 'formation', 'configuration', 'setup', 'arrangement'],
        'zone': ['area', 'region', 'level', 'territory', 'domain'],
        'level': ['reference', 'zone', 'pivot', 'mark', 'threshold'],
        'behavior': ['activity', 'action', 'movement', 'dynamics', 'conduct'],
        
        # Temporal adverbs
        'often': ['frequently', 'commonly', 'typically', 'regularly', 'generally'],
        'typically': ['usually', 'commonly', 'generally', 'ordinarily', 'normally'],
        'historically': ['traditionally', 'previously', 'in the past', 'conventionally'],
        
        # Causal conjunctions
        'when': ['as', 'while', 'during', 'whenever', 'at the point when'],
        'during': ['throughout', 'amid', 'in the course of', 'while', 'within'],
        'before': ['ahead of', 'prior to', 'in advance of', 'preceding'],
        
        # Quality adjectives
        'key': ['critical', 'important', 'significant', 'vital', 'essential'],
        'notable': ['significant', 'meaningful', 'important', 'relevant', 'material'],
        'critical': ['crucial', 'vital', 'essential', 'key', 'pivotal'],
        
        # Market state descriptors
        'compression': ['contraction', 'coiling', 'consolidation', 'tightening', 'squeeze'],
        'expansion': ['extension', 'broadening', 'widening', 'amplification', 'growth'],
        'accumulation': ['building', 'gathering', 'amassing', 'collecting', 'positioning'],
        'distribution': ['dispersal', 'offloading', 'unwinding', 'liquidation', 'repositioning'],
        
        # Direction words
        'upward': ['higher', 'ascending', 'rising', 'bullish', 'elevated'],
        'downward': ['lower', 'descending', 'declining', 'bearish', 'depressed'],
        
        # Probability language
        'likely': ['probable', 'expected', 'anticipated', 'foreseeable', 'plausible'],
        'possible': ['potential', 'conceivable', 'feasible', 'plausible', 'imaginable'],
        'could': ['may', 'might', 'can potentially', 'has potential to', 'is positioned to'],
        
        # Continuation words
        'continuation': ['extension', 'persistence', 'carry-forward', 'progression', 'advance'],
        'reversion': ['return', 'regression', 'snap-back', 'correction', 'reversal'],
    }
    
    # Sentence structure transformation patterns
    RESTRUCTURE_PATTERNS = [
        # Active to passive-like
        (r'(\w+) (shows|indicates|suggests) (.+)', r'\3 is shown by \1'),
        (r'(\w+) (creates|forms|builds) (.+)', r'\3 emerges from \1'),
        
        # Add qualifier phrases
        (r'^([A-Z].+)', r'Evidence suggests \1'),
        (r'^([A-Z].+)', r'Analysis indicates \1'),
        (r'^([A-Z].+)', r'Observation reveals \1'),
    ]
    
    def __init__(self):
        """Initialize language variation engine."""
        self.variation_count = defaultdict(int)
        logger.info("Language Variation Engine initialized")
    
    def mutate_sentence_structure(self, text: str, mutation_prob: float = 0.3) -> str:
        """
        Mutate sentence structure while preserving meaning.
        
        Applies transformations like:
        - Subject/object swapping
        - Active/passive voice changes
        - Clause reordering
        
        Args:
            text: Original sentence
            mutation_prob: Probability of applying each transformation
        
        Returns:
            Transformed sentence
        """
        sentences = text.split('. ')
        mutated_sentences = []
        
        for sentence in sentences:
            if random.random() < mutation_prob:
                # Try structure patterns
                for pattern, replacement in self.RESTRUCTURE_PATTERNS:
                    if re.match(pattern, sentence):
                        sentence = re.sub(pattern, replacement, sentence)
                        break
            
            mutated_sentences.append(sentence)
        
        return '. '.join(mutated_sentences)
    
    def apply_synonym_rotation(self, text: str, rotation_rate: float = 0.4) -> str:
        """
        Replace words with synonyms for lexical diversity.
        
        Args:
            text: Original text
            rotation_rate: Probability of replacing each eligible word
        
        Returns:
            Text with synonyms substituted
        """
        words = text.split()
        transformed_words = []
        
        for word in words:
            # Check if word (lowercase) has synonyms
            word_lower = word.lower().strip('.,!?;:')
            
            if word_lower in self.SYNONYM_SETS and random.random() < rotation_rate:
                synonyms = self.SYNONYM_SETS[word_lower]
                replacement = random.choice(synonyms)
                
                # Preserve capitalization
                if word[0].isupper():
                    replacement = replacement.capitalize()
                
                # Preserve punctuation
                punctuation = ''
                if word[-1] in '.,!?;:':
                    punctuation = word[-1]
                
                transformed_words.append(replacement + punctuation)
                self.variation_count[word_lower] += 1
            else:
                transformed_words.append(word)
        
        return ' '.join(transformed_words)
    
    def introduce_tone_modulation(
        self,
        text: str,
        target_tone: str = 'analytical'
    ) -> str:
        """
        Modulate text tone between analytical, neutral, and cautious.
        
        Args:
            text: Original text
            target_tone: 'analytical', 'neutral', or 'cautious'
        
        Returns:
            Text with adjusted tone
        """
        tone_transformations = {
            'analytical': {
                # More assertive, technical language
                'may': 'typically',
                'could': 'often',
                'might': 'frequently',
                'seems to': 'demonstrates',
                'appears to': 'exhibits',
                'looks like': 'indicates',
            },
            'neutral': {
                # Balanced, observational language
                'typically': 'generally',
                'frequently': 'commonly',
                'demonstrates': 'shows',
                'exhibits': 'displays',
                'indicates': 'suggests',
            },
            'cautious': {
                # More hedged, uncertain language
                'typically': 'may',
                'often': 'could',
                'shows': 'seems to show',
                'indicates': 'may indicate',
                'suggests': 'could suggest',
                'is': 'appears to be',
                'reveals': 'may reveal',
            }
        }
        
        transformations = tone_transformations.get(target_tone, {})
        
        for original, replacement in transformations.items():
            # Case-insensitive replacement
            pattern = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
            text = pattern.sub(replacement, text)
        
        return text
    
    def sentence_shuffle(
        self,
        candidates: List[str],
        shuffle_prob: float = 0.5
    ) -> List[str]:
        """
        Randomize sentence order within narrative components.
        
        Args:
            candidates: List of sentence candidates
            shuffle_prob: Probability of shuffling
        
        Returns:
            Potentially shuffled list
        """
        if len(candidates) <= 1 or random.random() > shuffle_prob:
            return candidates
        
        shuffled = candidates.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def calculate_lexical_diversity(self, text: str) -> float:
        """
        Calculate type-token ratio (lexical diversity).
        
        Higher values indicate more varied vocabulary.
        
        Args:
            text: Text to analyze
        
        Returns:
            Diversity score (0-1)
        """
        words = [w.lower() for w in re.findall(r'\w+', text)]
        
        if not words:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        
        # Type-token ratio
        return unique_words / total_words
    
    def enhance_variety(
        self,
        text: str,
        target_tone: str = 'analytical',
        aggressiveness: float = 0.5
    ) -> Tuple[str, Dict]:
        """
        Apply full variation pipeline to maximize uniqueness.
        
        Args:
            text: Original text
            target_tone: Desired tone
            aggressiveness: How much variation to apply (0-1)
        
        Returns:
            (enhanced_text, metrics_dict)
        """
        # Calculate baseline diversity
        baseline_diversity = self.calculate_lexical_diversity(text)
        
        # Apply transformations
        text = self.apply_synonym_rotation(text, rotation_rate=aggressiveness)
        text = self.mutate_sentence_structure(text, mutation_prob=aggressiveness * 0.6)
        text = self.introduce_tone_modulation(text, target_tone)
        
        # Calculate final diversity
        final_diversity = self.calculate_lexical_diversity(text)
        
        metrics = {
            'baseline_diversity': baseline_diversity,
            'final_diversity': final_diversity,
            'improvement': final_diversity - baseline_diversity,
            'tone': target_tone,
            'aggressiveness': aggressiveness
        }
        
        logger.debug(f"Variation applied - diversity: {baseline_diversity:.2f} → {final_diversity:.2f}")
        
        return text, metrics
    
    def generate_alternative_phrasings(
        self,
        text: str,
        count: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Generate multiple alternative phrasings with diversity scores.
        
        Args:
            text: Original text
            count: Number of alternatives to generate
        
        Returns:
            List of (alternative_text, diversity_score) tuples
        """
        alternatives = []
        
        for i in range(count):
            # Vary aggressiveness for each alternative
            aggressiveness = 0.3 + (i * 0.2)  # 0.3, 0.5, 0.7, etc.
            
            # Rotate through tones
            tones = ['analytical', 'neutral', 'cautious']
            tone = tones[i % len(tones)]
            
            # Generate alternative
            alt_text, metrics = self.enhance_variety(text, tone, aggressiveness)
            diversity = metrics['final_diversity']
            
            alternatives.append((alt_text, diversity))
        
        # Sort by diversity (highest first)
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return alternatives
    
    def get_variation_stats(self) -> Dict:
        """Get statistics on variation usage."""
        return {
            'total_variations': sum(self.variation_count.values()),
            'unique_words_varied': len(self.variation_count),
            'most_varied_words': sorted(
                self.variation_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


# Backward compatibility
from collections import defaultdict
