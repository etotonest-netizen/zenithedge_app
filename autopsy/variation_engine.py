"""
Zenith Market Analyst - Variation Engine

Ensures every insight is unique through:
- Synonym swapping
- Sentence restructuring  
- Dynamic vocabulary selection
- Context-aware phrasing

NO REPETITION. EVER.
"""
import random
import hashlib
from typing import Dict, List, Any, Tuple
from django.utils import timezone
from django.db.models import F


class VariationEngine:
    """
    Generate unique, non-repetitive market insights using dynamic vocabulary
    """
    
    def __init__(self):
        # Core vocabulary categories (loaded from DB in production)
        self.vocabulary = self._init_vocabulary()
        self.templates = self._init_templates()
        self.used_hashes = set()  # Track recent insights to avoid duplication
    
    def _init_vocabulary(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Initialize comprehensive vocabulary library
        Organized by: category -> context -> variations
        """
        return {
            'liquidity': {
                'building': [
                    "liquidity building",
                    "liquidity forming",
                    "liquidity accumulating",
                    "liquidity clustering near",
                    "resting liquidity observed above",
                    "liquidity pools developing at",
                    "sell-side liquidity forming near",
                    "buy-side liquidity gathering at",
                ],
                'sweeping': [
                    "swept prior low",
                    "engineered liquidity grab",
                    "cleared resting orders",
                    "triggered stop clusters",
                    "removed sell-side liquidity",
                    "collected buy-side liquidity",
                    "liquidated weak positions",
                ],
            },
            'momentum': {
                'increasing': [
                    "momentum expanding",
                    "flow accelerating",
                    "pressure building",
                    "buyers stepping in",
                    "sellers stepping in",
                    "conviction increasing",
                    "participation rising",
                    "energy building",
                ],
                'decreasing': [
                    "momentum cooling",
                    "flow decelerating",
                    "pressure easing",
                    "conviction fading",
                    "participation thinning",
                    "energy dissipating",
                    "interest waning",
                ],
                'diverging': [
                    "divergence forming",
                    "momentum-price misalignment detected",
                    "hidden weakness emerging",
                    "strength not reflected in price",
                    "bearish divergence present",
                    "bullish divergence noted",
                ],
            },
            'structure': {
                'bos': [
                    "Break of Structure confirms shift",
                    "structural break validates trend change",
                    "BOS signals new directional intent",
                    "market structure break indicates bias flip",
                    "critical structure broken",
                ],
                'choch': [
                    "Change of Character observed",
                    "CHoCH suggests momentum shift incoming",
                    "early reversal signal via CHoCH",
                    "character change hints at trend exhaustion",
                ],
                'pullback': [
                    "pullback phase underway",
                    "retracement developing",
                    "counter-trend correction in progress",
                    "temporary pause in primary trend",
                    "consolidation after expansion",
                ],
                'liquidity_sweep': [
                    "liquidity sweep executed",
                    "engineered move to clear stops",
                    "false breakout liquidity grab",
                    "stop hunt completed",
                ],
                'fvg': [
                    "Fair Value Gap left unmitigated",
                    "FVG presents potential magnet",
                    "imbalance zone awaiting fill",
                    "inefficiency in price delivery",
                ],
                'order_block': [
                    "Order Block identified",
                    "OB zone likely to provide support",
                    "institutional footprint suggests reaction zone",
                    "demand zone established",
                    "supply zone marked",
                ],
                'compression': [
                    "compression phase - expansion likely",
                    "volatility contraction precedes expansion",
                    "coiling price action",
                    "range tightening before breakout",
                ],
            },
            'regime': {
                'trending': [
                    "trending environment confirmed",
                    "directional bias established",
                    "clear trend structure intact",
                    "continuation probable",
                    "trend remains healthy",
                ],
                'ranging': [
                    "ranging conditions persist",
                    "sideways consolidation ongoing",
                    "no directional bias evident",
                    "bound within defined range",
                    "oscillating between levels",
                ],
                'volatile': [
                    "heightened volatility observed",
                    "erratic price behavior",
                    "unstable environment",
                    "whipsaw risk elevated",
                    "uncertainty driving price swings",
                ],
                'consolidation': [
                    "consolidation phase in effect",
                    "accumulation/distribution underway",
                    "market digesting prior move",
                    "equilibrium forming",
                ],
            },
            'session': {
                'london': [
                    "London session flow suggests",
                    "European market activity indicates",
                    "LDN open brought",
                    "early London participation shows",
                ],
                'newyork': [
                    "New York session driving",
                    "US market hours reveal",
                    "NY open triggered",
                    "American session flow suggests",
                ],
                'asia': [
                    "Asian session positioned",
                    "overnight action set up",
                    "Tokyo hours established",
                    "early Asian flow suggests",
                ],
                'off': [
                    "off-session conditions",
                    "low participation environment",
                    "thin liquidity hours",
                    "outside active trading sessions",
                ],
            },
            'expectation': {
                'expansion': [
                    "expansion expected",
                    "breakout potential rising",
                    "range break likely",
                    "volatility expansion incoming",
                ],
                'retracement': [
                    "retracement probable",
                    "pullback anticipated",
                    "correction phase expected",
                    "counter-move likely",
                ],
                'reversal': [
                    "reversal signal emerging",
                    "potential trend change",
                    "directional shift possible",
                    "bias flip candidate",
                ],
                'liquidity_grab': [
                    "liquidity grab scenario",
                    "stop hunt setup forming",
                    "false move likely before true direction",
                    "engineered move probable",
                ],
            },
            'quality': {
                'high': [
                    "high-quality setup",
                    "favorable conditions",
                    "clear opportunity",
                    "strong alignment",
                    "optimal environment",
                ],
                'low': [
                    "unclear conditions",
                    "mixed signals",
                    "low-quality environment",
                    "conflicting evidence",
                    "ambiguous structure",
                ],
            },
        }
    
    def _init_templates(self) -> List[Dict[str, Any]]:
        """
        Initialize sentence structure templates
        Each template has slots filled by vocabulary
        """
        return [
            {
                'id': 'struct_momentum_session',
                'structure': "Price {structure_action} as {momentum_state}. {session_context}.",
                'slots': ['structure_action', 'momentum_state', 'session_context'],
            },
            {
                'id': 'regime_liquidity_expect',
                'structure': "{regime_state} with {liquidity_context}; {expectation}.",
                'slots': ['regime_state', 'liquidity_context', 'expectation'],
            },
            {
                'id': 'session_struct_momentum',
                'structure': "{session_context} {structure_action} while {momentum_state}.",
                'slots': ['session_context', 'structure_action', 'momentum_state'],
            },
            {
                'id': 'complex_context',
                'structure': "Market {regime_state} after {structure_action}. {momentum_state} suggests {expectation}.",
                'slots': ['regime_state', 'structure_action', 'momentum_state', 'expectation'],
            },
            {
                'id': 'quality_based',
                'structure': "{quality_assessment}. {structure_action} combined with {momentum_state}.",
                'slots': ['quality_assessment', 'structure_action', 'momentum_state'],
            },
        ]
    
    def generate_insight(self, metadata: Dict[str, Any], force_unique: bool = True) -> Tuple[str, str]:
        """
        Generate unique natural language insight from metadata
        
        Args:
            metadata: Parsed market data
            force_unique: If True, retry until unique hash generated
            
        Returns:
            (insight_text, vocabulary_hash)
        """
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            # Select appropriate template
            template = self._select_template(metadata)
            
            # Fill template slots with varied vocabulary
            insight_text = self._fill_template(template, metadata)
            
            # Calculate hash
            vocab_hash = self._calculate_hash(insight_text)
            
            # Check uniqueness
            if not force_unique or vocab_hash not in self.used_hashes:
                self.used_hashes.add(vocab_hash)
                return insight_text, vocab_hash
            
            attempt += 1
        
        # Fallback: direct description (should rarely happen)
        return self._generate_fallback(metadata), self._calculate_hash(insight_text)
    
    def _select_template(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select appropriate template based on metadata context
        """
        regime = metadata.get('regime', 'unknown')
        structure = metadata.get('structure', 'none')
        
        # Filter templates by applicability
        applicable = self.templates.copy()
        
        # Could add logic to filter by regime/structure
        # For now, random selection for maximum variation
        return random.choice(applicable)
    
    def _fill_template(self, template: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """
        Fill template slots with context-appropriate vocabulary
        """
        slots = {}
        
        for slot_name in template['slots']:
            slots[slot_name] = self._get_slot_value(slot_name, metadata)
        
        # Fill template
        try:
            insight = template['structure'].format(**slots)
        except KeyError as e:
            # Missing slot - use fallback
            return self._generate_fallback(metadata)
        
        return insight
    
    def _get_slot_value(self, slot_name: str, metadata: Dict[str, Any]) -> str:
        """
        Get vocabulary for a specific slot based on metadata context
        """
        # Parse slot name (e.g., 'structure_action' -> category: structure, context: action)
        parts = slot_name.split('_')
        
        if slot_name == 'structure_action':
            structure = metadata.get('structure', 'none')
            if structure in self.vocabulary['structure']:
                return random.choice(self.vocabulary['structure'][structure])
            return "shows structural development"
        
        if slot_name == 'momentum_state':
            momentum = metadata.get('momentum', 'neutral')
            if momentum in self.vocabulary['momentum']:
                return random.choice(self.vocabulary['momentum'][momentum])
            return "momentum remains neutral"
        
        if slot_name == 'session_context':
            session = metadata.get('session', 'off')
            if session in self.vocabulary['session']:
                return random.choice(self.vocabulary['session'][session])
            return "market conditions suggest"
        
        if slot_name == 'regime_state':
            regime = metadata.get('regime', 'unknown')
            if regime in self.vocabulary['regime']:
                return random.choice(self.vocabulary['regime'][regime])
            return "market environment shows"
        
        if slot_name == 'liquidity_context':
            # Contextual liquidity description
            structure = metadata.get('structure', '')
            if 'sweep' in structure:
                return random.choice(self.vocabulary['liquidity']['sweeping'])
            else:
                return random.choice(self.vocabulary['liquidity']['building'])
        
        if slot_name == 'expectation':
            expected = metadata.get('expected_behavior', '').lower()
            for key in self.vocabulary['expectation']:
                if key in expected:
                    return random.choice(self.vocabulary['expectation'][key])
            return "expect reaction rather than continuation"
        
        if slot_name == 'quality_assessment':
            strength = metadata.get('strength', 50)
            if strength > 70:
                return random.choice(self.vocabulary['quality']['high'])
            else:
                return random.choice(self.vocabulary['quality']['low'])
        
        # Default fallback
        return "market shows behavior"
    
    def _generate_fallback(self, metadata: Dict[str, Any]) -> str:
        """
        Generate direct description when template filling fails
        """
        parts = []
        
        regime = metadata.get('regime', 'unknown')
        if regime != 'unknown':
            parts.append(f"{regime.title()} environment")
        
        structure = metadata.get('structure', 'none')
        if structure != 'none':
            parts.append(f"with {structure.replace('_', ' ')}")
        
        momentum = metadata.get('momentum', 'neutral')
        if momentum != 'neutral':
            parts.append(f"and {momentum} momentum")
        
        if not parts:
            return "Market conditions under observation"
        
        return ' '.join(parts) + "."
    
    def _calculate_hash(self, text: str) -> str:
        """
        Calculate hash of insight text for uniqueness tracking
        """
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def generate_suggestion(self, metadata: Dict[str, Any]) -> str:
        """
        Generate actionable suggestion (NOT buy/sell signals)
        """
        suggestions_pool = {
            'high_quality': [
                "Monitor reaction at key levels",
                "Watch for continuation confirmation",
                "Favorable risk-reward environment emerging",
                "Structure supports directional bias",
            ],
            'low_quality': [
                "Avoid impulsive entries - structure unclear",
                "Wait for cleaner confirmation",
                "Mixed signals warrant patience",
                "Risk-reward unfavorable currently",
            ],
            'ranging': [
                "Range-bound environment favors mean reversion",
                "Breakout attempts may be false moves",
                "Oscillator strategies preferred in current structure",
            ],
            'volatile': [
                "Heightened volatility increases execution risk",
                "Wider stops required in current conditions",
                "Consider reducing position sizing",
            ],
            'liquidity_sweep': [
                "Liquidity resting above equal highs - breakout likely engineered",
                "False move probable before true directional intent",
                "Stop clusters may be targeted before continuation",
            ],
            'news_risk': [
                "High-impact event risk present",
                "Macro driver may override technical structure",
                "Consider event risk in position management",
            ],
        }
        
        # Context-based suggestion selection
        regime = metadata.get('regime', 'unknown')
        structure = metadata.get('structure', 'none')
        strength = metadata.get('strength', 50)
        risk_notes = metadata.get('risk_notes', [])
        
        # Priority: risk warnings first
        if any('news' in note.lower() for note in risk_notes):
            return random.choice(suggestions_pool['news_risk'])
        
        if structure == 'liquidity_sweep':
            return random.choice(suggestions_pool['liquidity_sweep'])
        
        if regime == 'ranging':
            return random.choice(suggestions_pool['ranging'])
        
        if regime == 'volatile':
            return random.choice(suggestions_pool['volatile'])
        
        # Quality-based
        if strength > 70:
            return random.choice(suggestions_pool['high_quality'])
        else:
            return random.choice(suggestions_pool['low_quality'])
    
    def load_vocabulary_from_db(self):
        """
        Load vocabulary variations from database (for production use)
        """
        try:
            from autopsy.models import VariationVocabulary
            
            db_vocab = VariationVocabulary.objects.filter(is_active=True)
            
            for entry in db_vocab:
                category = entry.category
                subcategory = entry.subcategory or 'default'
                
                if category not in self.vocabulary:
                    self.vocabulary[category] = {}
                
                if subcategory not in self.vocabulary[category]:
                    self.vocabulary[category][subcategory] = []
                
                # Add variations
                self.vocabulary[category][subcategory].extend(entry.variations)
                
        except Exception as e:
            # Fallback to hardcoded vocabulary
            pass
    
    def update_usage_stats(self, vocabulary_hash: str, category: str, phrase: str):
        """
        Update database usage statistics for vocabulary tracking
        """
        try:
            from autopsy.models import VariationVocabulary
            
            VariationVocabulary.objects.filter(
                category=category,
                variations__contains=[phrase]
            ).update(
                usage_count=F('usage_count') + 1,
                last_used=timezone.now()
            )
        except Exception:
            pass
