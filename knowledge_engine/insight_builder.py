"""
Insight Builder - Professional Market Narrative Generator
Generates unique, context-aware trading insights with linguistic variation
"""
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .query_engine import KnowledgeQueryEngine
from .strategy_domains import STRATEGY_DOMAINS

logger = logging.getLogger(__name__)


class InsightBuilder:
    """
    Build professional, varied market insights using KB knowledge
    Prevents repetition through template variation and paraphrasing
    """
    
    def __init__(self):
        self.query_engine = KnowledgeQueryEngine()
        self.recent_templates = []  # Track to avoid repetition
        self.max_template_memory = 10
    
    def build_comprehensive_insight(
        self,
        signal_data: Dict,
        validation_result: Dict = None
    ) -> Dict:
        """
        Build comprehensive market insight with KB enrichment
        
        Args:
            signal_data: Signal information (symbol, strategy, action, etc.)
            validation_result: Optional validation/analysis data
            
        Returns:
            Dict with narrative, kb_trace, and metadata
        """
        strategy = signal_data.get('strategy', '').lower()
        symbol = signal_data.get('symbol', '')
        timeframe = signal_data.get('timeframe', '')
        regime = signal_data.get('regime', '')
        session = signal_data.get('session', '')
        
        # Build context for insight generation
        context_features = {
            'strategy': strategy,
            'market_behavior': self._extract_behavior(signal_data, validation_result),
            'session': session,
            'regime': regime,
            'structure': validation_result.get('breakdown', {}).get('technical', {}).get('commentary', '') if validation_result else '',
            'symbol': symbol,
            'timeframe': timeframe
        }
        
        # Search KB for relevant concepts
        concepts_used = []
        kb_sources = []
        
        behavior = context_features['market_behavior']
        if behavior:
            search_results = self.query_engine.search_concept(behavior, strategy=strategy, k=3)
            
            for result in search_results:
                concepts_used.append(result['term'])
                kb_sources.append({
                    'concept': result['term'],
                    'source': result['source'],
                    'similarity': result['similarity']
                })
        
        # Generate base narrative
        narrative = self.query_engine.generate_insight(context_features, paraphrase=True)
        
        # Enhance with specific details
        narrative = self._enhance_with_specifics(
            narrative,
            signal_data,
            validation_result,
            kb_sources
        )
        
        # Build KB trace for provenance
        kb_trace = {
            'concepts': concepts_used,
            'sources': kb_sources,
            'strategy': strategy,
            'query_count': len(search_results) if behavior else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'narrative': narrative,
            'kb_trace': kb_trace,
            'confidence': self._calculate_confidence(kb_sources),
            'linguistic_hash': hash(narrative)  # Track uniqueness
        }
    
    def generate_varied_narrative(
        self,
        concept: str,
        context: str,
        narrative_type: str = 'explanation'
    ) -> str:
        """
        Generate varied narrative for a concept
        
        Args:
            concept: Main trading concept
            context: Context information
            narrative_type: Type of narrative (explanation, warning, opportunity)
            
        Returns:
            Generated narrative text
        """
        templates = self._get_templates(narrative_type)
        
        # Filter out recently used templates
        available_templates = [t for t in templates if t not in self.recent_templates]
        if not available_templates:
            available_templates = templates
            self.recent_templates = []
        
        # Select template
        template = random.choice(available_templates)
        self.recent_templates.append(template)
        
        # Keep memory limited
        if len(self.recent_templates) > self.max_template_memory:
            self.recent_templates.pop(0)
        
        # Fill template
        try:
            narrative = template.format(concept=concept, context=context)
        except KeyError:
            narrative = f"{concept} observed in current market conditions. {context}"
        
        return narrative
    
    def build_educational_explanation(
        self,
        concept_term: str,
        user_level: str = 'intermediate'
    ) -> str:
        """
        Build educational explanation for a concept
        
        Args:
            concept_term: Concept to explain
            user_level: User expertise level (intro, intermediate, advanced, expert)
            
        Returns:
            Educational explanation text
        """
        # Search for concept
        results = self.query_engine.search_concept(concept_term, k=1)
        
        if not results:
            return f"No information found for '{concept_term}'."
        
        concept_data = results[0]
        
        # Build explanation based on user level
        if user_level == 'intro':
            explanation = self._build_intro_explanation(concept_data)
        elif user_level == 'advanced' or user_level == 'expert':
            explanation = self._build_advanced_explanation(concept_data)
        else:  # intermediate
            explanation = self._build_intermediate_explanation(concept_data)
        
        return explanation
    
    def build_comparison_narrative(
        self,
        concept_a: str,
        concept_b: str
    ) -> str:
        """
        Build narrative comparing two concepts
        
        Args:
            concept_a: First concept
            concept_b: Second concept
            
        Returns:
            Comparison narrative
        """
        results_a = self.query_engine.search_concept(concept_a, k=1)
        results_b = self.query_engine.search_concept(concept_b, k=1)
        
        if not results_a or not results_b:
            return f"Insufficient data to compare {concept_a} and {concept_b}."
        
        data_a = results_a[0]
        data_b = results_b[0]
        
        templates = [
            f"{data_a['term']} and {data_b['term']} both serve important roles in trading. "
            f"{data_a['term']} focuses on {data_a['summary'].lower()}, "
            f"while {data_b['term']} emphasizes {data_b['summary'].lower()}. "
            f"Traders often use them together for confluence.",
            
            f"While {data_a['term']} involves {data_a['summary'].lower()}, "
            f"{data_b['term']} deals with {data_b['summary'].lower()}. "
            f"Understanding both concepts provides a more complete market perspective.",
            
            f"Comparing {data_a['term']} with {data_b['term']}: "
            f"The former indicates {data_a['summary'].lower()}, "
            f"whereas the latter suggests {data_b['summary'].lower()}. "
            f"Each has its place depending on market conditions."
        ]
        
        return random.choice(templates)
    
    def build_warning_narrative(
        self,
        risk_factor: str,
        context: Dict
    ) -> str:
        """
        Build risk warning narrative
        
        Args:
            risk_factor: Identified risk
            context: Context information
            
        Returns:
            Warning narrative
        """
        templates = [
            f"⚠️ Exercise caution: {risk_factor}. Consider reducing position size or waiting for better confirmation.",
            f"⚠️ Note the elevated risk: {risk_factor}. This setup requires additional validation before entry.",
            f"⚠️ Risk alert: {risk_factor}. Professional traders would wait for stronger confluence in these conditions.",
            f"⚠️ Proceed carefully: {risk_factor}. The current environment suggests a more conservative approach."
        ]
        
        return random.choice(templates)
    
    # Helper methods
    
    def _extract_behavior(self, signal_data: Dict, validation_result: Dict = None) -> str:
        """Extract market behavior from signal and validation data"""
        # Try to get from validation
        if validation_result:
            commentary = validation_result.get('breakdown', {}).get('technical', {}).get('commentary', '')
            if commentary:
                # Extract key phrases
                phrases = ['liquidity sweep', 'order block', 'fair value gap', 'breakout', 
                          'reversal', 'continuation', 'squeeze', 'expansion']
                for phrase in phrases:
                    if phrase in commentary.lower():
                        return phrase
        
        # Fallback to strategy and regime
        strategy = signal_data.get('strategy', '')
        regime = signal_data.get('regime', '')
        
        if regime:
            return regime.lower()
        elif strategy:
            strategy_info = STRATEGY_DOMAINS.get(strategy.lower(), {})
            if strategy_info and strategy_info.get('core_concepts'):
                return strategy_info['core_concepts'][0]
        
        return 'price action'
    
    def _enhance_with_specifics(
        self,
        base_narrative: str,
        signal_data: Dict,
        validation_result: Dict,
        kb_sources: List[Dict]
    ) -> str:
        """Enhance narrative with specific signal details"""
        # Add specific levels if available
        entry = signal_data.get('entry')
        sl = signal_data.get('sl')
        tp = signal_data.get('tp')
        
        if entry and sl and tp:
            # Calculate R:R
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= 2.0:
                base_narrative += f" The setup offers favorable {rr_ratio:.1f}:1 risk-reward profile."
        
        # Add confidence qualifier if low KB match
        if kb_sources and kb_sources[0]['similarity'] < 0.5:
            base_narrative += " Monitor for additional confirmation signals."
        
        return base_narrative
    
    def _calculate_confidence(self, kb_sources: List[Dict]) -> float:
        """Calculate confidence score based on KB matches"""
        if not kb_sources:
            return 0.5
        
        # Average similarity scores
        avg_similarity = sum(s['similarity'] for s in kb_sources) / len(kb_sources)
        
        # Boost if multiple sources agree
        if len(kb_sources) >= 2:
            avg_similarity = min(1.0, avg_similarity * 1.2)
        
        return float(avg_similarity)
    
    def _get_templates(self, narrative_type: str) -> List[str]:
        """Get templates for narrative type"""
        templates = {
            'explanation': [
                "{concept} is evident in the current formation. {context}",
                "Analysis reveals {concept} structure. {context}",
                "The observed pattern shows {concept}. {context}",
                "Current conditions align with {concept}. {context}",
                "Market behavior displays {concept} characteristics. {context}"
            ],
            'warning': [
                "⚠️ {concept} suggests elevated risk. {context}",
                "⚠️ Caution: {concept} detected. {context}",
                "⚠️ Note the {concept} signal. {context}",
                "⚠️ Be aware of {concept}. {context}"
            ],
            'opportunity': [
                "✨ {concept} presents opportunity. {context}",
                "✨ Favorable {concept} setup forming. {context}",
                "✨ Strong {concept} alignment detected. {context}",
                "✨ High-probability {concept} signal. {context}"
            ]
        }
        
        return templates.get(narrative_type, templates['explanation'])
    
    def _build_intro_explanation(self, concept_data: Dict) -> str:
        """Build beginner-friendly explanation"""
        term = concept_data['term']
        summary = concept_data['summary']
        
        return f"{term}: {summary} This is a fundamental concept that helps traders identify potential trade opportunities."
    
    def _build_intermediate_explanation(self, concept_data: Dict) -> str:
        """Build intermediate explanation"""
        term = concept_data['term']
        summary = concept_data['summary']
        definition = concept_data['definition'][:300]
        
        explanation = f"{term}: {summary}\n\n{definition}"
        
        examples = concept_data.get('examples', [])
        if examples and isinstance(examples, list):
            explanation += f"\n\nExample: {examples[0]}"
        
        return explanation
    
    def _build_advanced_explanation(self, concept_data: Dict) -> str:
        """Build advanced explanation with full details"""
        term = concept_data['term']
        definition = concept_data['definition']
        
        explanation = f"{term}\n\n{definition}"
        
        # Add advanced details
        strategy = concept_data.get('strategy', '')
        if strategy:
            strategy_info = STRATEGY_DOMAINS.get(strategy, {})
            if strategy_info:
                explanation += f"\n\nStrategy Context: {strategy_info.get('psychology', '')}"
        
        return explanation


# Convenience functions
def build_insight(signal_data: Dict, validation_result: Dict = None) -> Dict:
    """Quick insight builder wrapper"""
    builder = InsightBuilder()
    return builder.build_comprehensive_insight(signal_data, validation_result)


def explain_concept(concept: str, level: str = 'intermediate') -> str:
    """Quick concept explanation wrapper"""
    builder = InsightBuilder()
    return builder.build_educational_explanation(concept, level)


def compare_concepts(concept_a: str, concept_b: str) -> str:
    """Quick concept comparison wrapper"""
    builder = InsightBuilder()
    return builder.build_comparison_narrative(concept_a, concept_b)
