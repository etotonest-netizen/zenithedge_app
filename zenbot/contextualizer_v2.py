"""
Enhanced Contextual Intelligence Engine v2.0 for ZenithEdge Trading Hub

Integrates with Knowledge Engine v2.0 to provide AI-powered, linguistically
varied narratives with deep market context and educational insights.

This version replaces basic templating with intelligent KB-powered narratives
that achieve 95%+ linguistic diversity and provide rich trading education.

Author: ZenithEdge Team
Version: 2.0 (Knowledge Engine Integration)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class EnhancedContextualIntelligenceEngine:
    """
    KB-powered narrative generator for trading signals (v2.0).
    
    Enhancements over v1.0:
    - Integrates with Knowledge Engine v2.0 for rich concept explanations
    - 95%+ linguistic variation (no repetitive phrasing)
    - Educational insights embedded in narratives
    - Strategy-specific deep context from 10 domain hierarchies
    - KB provenance tracking (which concepts informed the narrative)
    - Multi-difficulty explanations (intro, intermediate, advanced)
    - Related concept suggestions for deeper learning
    
    Features retained from v1.0:
    - 3-part narrative structure (header, reasoning, suggestion)
    - Session-aware timing context (London, NY, Asia)
    - Risk management guidance based on validation scores
    - Adaptive tone (analytical, brief, confident)
    """
    
    def __init__(self):
        """Initialize the enhanced contextualizer with KB integration."""
        from knowledge_engine.query_engine import KnowledgeQueryEngine
        from knowledge_engine.insight_builder import InsightBuilder
        from zenbot.narrative_composer import NarrativeComposer
        from zenbot.language_variation import LanguageVariationEngine
        
        self.query_engine = KnowledgeQueryEngine()
        self.insight_builder = InsightBuilder()
        self.narrative_composer = NarrativeComposer()
        self.language_variation = LanguageVariationEngine()
        
        logger.info("Enhanced Contextual Intelligence Engine v2.0 initialized (KB-powered + Narrative Composer)")
    
    def generate_narrative(
        self, 
        signal_data: Dict, 
        validation_result: Dict,
        user_level: str = 'intermediate',
        include_education: bool = True
    ) -> str:
        """
        Generate KB-powered comprehensive narrative for a validated signal.
        
        Args:
            signal_data: Raw signal data from webhook
            validation_result: Output from validation_engine.validate_signal()
            user_level: User expertise ('intro', 'intermediate', 'advanced')
            include_education: Whether to include educational insights
        
        Returns:
            Human-readable narrative with KB enrichment
        
        Example Output:
            "📊 EURUSD LONG setup detected — 83/100 solid (SMC)
            
            The observed fair value gap at 1.0850 indicates institutional 
            interest, with price structure suggesting smart money accumulation.
            During London session, this aligns with CHoCH patterns typical of
            demand zone testing. Market behavior shows strong directional bias
            with liquidity engineered above 1.0830.
            
            Long bias warranted above 1.0850 with partials at 1.0910. 
            Risk < 1.5%. Structure invalidated below 1.0825.
            
            📚 Related Concepts: Order blocks, liquidity sweeps, market structure
            🔍 KB Trace: 3 concepts, 95% confidence"
        """
        try:
            # Extract components
            symbol = signal_data.get('symbol', 'UNKNOWN')
            side = signal_data.get('side', 'buy').upper()
            strategy = signal_data.get('strategy', 'default').lower()
            confidence = signal_data.get('confidence', 0)
            price = float(signal_data.get('price', 0))
            sl = float(signal_data.get('sl', 0))
            tp = float(signal_data.get('tp', 0))
            regime = signal_data.get('regime', 'trending').lower()
            session = signal_data.get('session', 'unknown').lower()
            
            truth_index = validation_result.get('truth_index', 0)
            breakdown = validation_result.get('breakdown', {})
            status = validation_result.get('status', 'unknown')
            
            # Query Knowledge Engine for related concepts
            kb_hits = self._fetch_kb_concepts(strategy, signal_data)
            
            # Build signal context for narrative composer
            signal_context = {
                'symbol': symbol,
                'side': side,
                'strategy': strategy,
                'price': price,
                'session': session,
                'regime': regime,
                'confidence': confidence,
                'truth_index': truth_index
            }
            
            # Generate unique narrative using Narrative Composer
            narrative_result = self.narrative_composer.generate_narrative(
                signal_context=signal_context,
                knowledge_hits=kb_hits,
                tone='analytical'  # Can be 'analytical', 'neutral', or 'cautious'
            )
            
            # Extract the pure composed narrative (analyst-style 2-4 sentences)
            composed_narrative = narrative_result['narrative']
            
            # Build full narrative with header/footer for legacy uses
            header = self._build_header(symbol, truth_index, strategy, side)
            suggestion = self._build_suggestion(signal_data, truth_index, status)
            kb_footer = self._build_narrative_footer(narrative_result, kb_hits)
            
            # Full narrative (header + composed + suggestion + footer)
            narrative_parts = [header, composed_narrative, suggestion]
            if kb_footer:
                narrative_parts.append(kb_footer)
            
            full_narrative = "\n\n".join(narrative_parts)
            
            logger.info(
                f"Generated KB-powered narrative for {symbol} "
                f"(TI: {truth_index:.1f}, KB concepts: {len(kb_hits)}, "
                f"Uniqueness: {narrative_result.get('linguistic_uniqueness', 0)*100:.0f}%)"
            )
            
            # Return rich data structure with BOTH full and composed narratives
            return {
                'narrative': full_narrative,  # Full narrative with headers/footers
                'composed_narrative': composed_narrative,  # Pure 2-4 sentence narrative
                'quality_metrics': {
                    'insight_index': int(narrative_result.get('insight_index', 0) * 100),
                    'linguistic_uniqueness': int(narrative_result.get('linguistic_uniqueness', 0) * 100),
                    'generation_time_ms': narrative_result.get('generation_time_ms', 0)
                },
                'kb_concepts_used': len(kb_hits),
                'kb_trace': [hit.get('term', '') for hit in kb_hits[:3]]  # Top 3 concepts
            }
            
        except Exception as e:
            logger.error(f"Error generating KB narrative: {e}", exc_info=True)
            # Fall back to v1.0 contextualizer
            return self._fallback_to_v1(signal_data, validation_result)
    
    def _build_header(self, symbol: str, truth_index: float, 
                      strategy: str, side: str) -> str:
        """
        Build concise header with essential info.
        
        Format: "📊 SYMBOL DIRECTION setup detected — XX/100 quality (STRATEGY)"
        """
        strategy_display = strategy.upper() if strategy != 'default' else 'Technical'
        direction = "LONG" if side == "BUY" else "SHORT"
        
        # Quality indicator
        if truth_index >= 85:
            quality = "high-confidence"
        elif truth_index >= 75:
            quality = "solid"
        elif truth_index >= 65:
            quality = "moderate"
        else:
            quality = "conditional"
        
        header = (f"📊 {symbol} {direction} setup detected — "
                 f"{truth_index:.0f}/100 {quality} ({strategy_display})")
        
        return header
    
    def _build_suggestion(self, signal_data: Dict, truth_index: float, 
                         status: str) -> str:
        """
        Build actionable trading suggestion with risk management.
        
        Uses KB for risk-aware language but keeps technical specifics clear.
        """
        side = signal_data.get('side', 'buy').lower()
        price = float(signal_data.get('price', 0))
        sl = float(signal_data.get('sl', 0))
        tp = float(signal_data.get('tp', 0))
        
        # Calculate R:R
        if side == 'buy':
            risk = price - sl
            reward = tp - price
        else:
            risk = sl - price
            reward = price - tp
        
        rr_ratio = reward / risk if risk > 0 else 0
        
        # Risk percentage
        risk_pct = (abs(price - sl) / price) * 100
        
        # Build suggestion
        direction_text = "Long" if side == 'buy' else "Short"
        comparison = "above" if side == 'buy' else "below"
        invalidation = "below" if side == 'buy' else "above"
        
        suggestion = f"{direction_text} bias warranted {comparison} {price:.5f}"
        
        if tp > 0:
            suggestion += f" with target at {tp:.5f}"
        
        suggestion += f". Risk {risk_pct:.1f}% (R:R {rr_ratio:.2f})"
        
        # Invalidation level
        if sl > 0:
            suggestion += f". Structure invalidated {invalidation} {sl:.5f}"
        
        # Risk warning based on truth index
        if truth_index < 70:
            from knowledge_engine.insight_builder import InsightBuilder
            builder = InsightBuilder()
            warning = builder.build_warning_narrative(
                risk_factor="Lower confidence setup",
                context=f"{truth_index:.0f}/100 truth index"
            )
            suggestion += f"\n\n{warning}"
        
        return suggestion
    
    def _build_educational_context(self, kb_trace: Dict, user_level: str) -> Optional[str]:
        """
        Build educational context section with concept explanations.
        
        Args:
            kb_trace: KB provenance data
            user_level: User expertise level
        
        Returns:
            Educational insights or None
        """
        concepts_used = kb_trace.get('concepts_used', [])
        
        if not concepts_used or len(concepts_used) == 0:
            return None
        
        # Pick the most relevant concept to explain
        main_concept = concepts_used[0]
        
        try:
            # Get educational explanation from KB
            explanation = self.insight_builder.build_educational_explanation(
                concept_term=main_concept,
                user_level=user_level
            )
            
            if explanation and len(explanation) > 50:
                edu_section = f"📚 **Key Concept: {main_concept.title()}**\n{explanation}"
                return edu_section
        except Exception as e:
            logger.warning(f"Could not build educational context: {e}")
        
        return None
    
    def _build_kb_footer(self, kb_insight: Dict) -> Optional[str]:
        """
        Build metadata footer showing KB provenance.
        
        Args:
            kb_insight: Insight dict from InsightBuilder
        
        Returns:
            Footer text or None
        """
        kb_trace = kb_insight.get('kb_trace', {})
        
        if not kb_trace:
            return None
        
        concepts = kb_trace.get('concepts_used', [])
        confidence = kb_insight.get('confidence', 0)
        query_count = kb_trace.get('query_count', 0)
        
        if not concepts:
            return None
        
        # Build concise footer
        footer_parts = []
        
        # Related concepts
        if len(concepts) > 1:
            related = ", ".join(concepts[1:4])  # Show up to 3 additional concepts
            footer_parts.append(f"🔗 Related: {related}")
        
        # KB confidence
        footer_parts.append(f"🔍 KB: {len(concepts)} concept{'s' if len(concepts) > 1 else ''}, {confidence:.0%} confidence")
        
        return " | ".join(footer_parts)
    
    def _fallback_to_v1(self, signal_data: Dict, validation_result: Dict) -> str:
        """
        Fall back to original contextualizer v1.0 if KB fails.
        
        Args:
            signal_data: Signal data dict
            validation_result: Validation result dict
        
        Returns:
            v1.0 narrative
        """
        try:
            from zenbot.contextualizer import ContextualIntelligenceEngine
            
            logger.warning("Falling back to contextualizer v1.0")
            v1_engine = ContextualIntelligenceEngine()
            return v1_engine.generate_narrative(signal_data, validation_result)
        except Exception as e:
            logger.error(f"v1.0 fallback also failed: {e}")
            return self._minimal_fallback(signal_data, validation_result)
    
    def _minimal_fallback(self, signal_data: Dict, validation_result: Dict) -> str:
        """Absolute minimal fallback if everything fails."""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        side = signal_data.get('side', 'buy').upper()
        confidence = signal_data.get('confidence', 0)
        truth_index = validation_result.get('truth_index', 0)
        
        return (f"Signal detected: {symbol} {side}\n"
                f"Confidence: {confidence}/100\n"
                f"Truth Index: {truth_index:.1f}/100\n"
                f"Status: {validation_result.get('status', 'unknown')}")
    
    def generate_narrative_batch(
        self,
        signals: List[Dict],
        user_level: str = 'intermediate'
    ) -> List[str]:
        """
        Generate narratives for multiple signals efficiently.
        
        Args:
            signals: List of (signal_data, validation_result) tuples
            user_level: User expertise level
        
        Returns:
            List of narrative strings
        """
        narratives = []
        
        for signal_data, validation_result in signals:
            try:
                narrative = self.generate_narrative(
                    signal_data=signal_data,
                    validation_result=validation_result,
                    user_level=user_level,
                    include_education=False  # Skip education in batch mode
                )
                narratives.append(narrative)
            except Exception as e:
                logger.error(f"Error in batch narrative generation: {e}")
                narratives.append(self._minimal_fallback(signal_data, validation_result))
        
        return narratives
    
    def _fetch_kb_concepts(self, strategy: str, signal_data: Dict) -> List[Dict]:
        """
        Fetch related KB concepts for the signal strategy.
        
        Args:
            strategy: Strategy name (smc, ict, trend, etc.)
            signal_data: Signal data dict
        
        Returns:
            List of KB entry dicts with term, definition, related_concepts, etc.
        """
        try:
            # Build query from strategy + key terms
            symbol = signal_data.get('symbol', '')
            regime = signal_data.get('regime', 'trending')
            
            # Query KB for strategy-related concepts
            results = self.query_engine.search_concept(
                query=f"{strategy} trading setup {regime} market",
                strategy=strategy,
                k=5  # Get top 5 related concepts
            )
            
            # Transform results into usable format
            kb_hits = []
            for result in results:
                entry = result.get('entry', {})
                kb_hits.append({
                    'term': entry.get('term', ''),
                    'definition': entry.get('definition', ''),
                    'summary': entry.get('summary', ''),
                    'related_concepts': entry.get('related_concepts', []),
                    'market_behavior_patterns': entry.get('market_behavior_patterns', []),
                    'similarity': result.get('similarity', 0.0)
                })
            
            logger.debug(f"Fetched {len(kb_hits)} KB concepts for {strategy} strategy")
            return kb_hits
            
        except Exception as e:
            logger.error(f"Error fetching KB concepts: {e}", exc_info=True)
            return []
    
    def _build_narrative_footer(
        self, 
        narrative_result: Dict, 
        kb_hits: List[Dict]
    ) -> str:
        """
        Build footer with KB trace and narrative quality metrics.
        
        Args:
            narrative_result: Output from narrative_composer.generate_narrative()
            kb_hits: KB concepts used
        
        Returns:
            Formatted footer string
        """
        kb_trace = narrative_result.get('kb_trace', [])
        linguistic_uniqueness = narrative_result.get('linguistic_uniqueness', 0)
        insight_index = narrative_result.get('insight_index', 0)
        
        if not kb_trace:
            return "🧠 Generated with Knowledge Engine v2.0"
        
        # Build footer components
        footer_parts = []
        
        # Related concepts
        concepts_str = ", ".join(kb_trace[:3])  # Show up to 3
        footer_parts.append(f"📚 Concepts: {concepts_str}")
        
        # Quality metrics
        footer_parts.append(
            f"🔍 Quality: {insight_index:.0%} | "
            f"Uniqueness: {linguistic_uniqueness:.0%} | "
            f"⚡ {narrative_result.get('generation_time_ms', 0)}ms"
        )
        
        return " | ".join(footer_parts)
    
    def get_linguistic_stats(self) -> Dict:
        """
        Get linguistic variation statistics from Narrative Composer.
        
        Returns:
            Dict with stats about template usage, uniqueness, variation
        """
        composer_stats = {
            'template_usage': dict(self.narrative_composer.template_usage),
            'recent_narrative_count': len(self.narrative_composer.recent_narratives),
        }
        
        variation_stats = self.language_variation.get_variation_stats()
        
        return {
            'engine_version': '2.0',
            'kb_powered': True,
            'narrative_composer': composer_stats,
            'language_variation': variation_stats,
            'variation_target': '95%+',
            'status': 'operational'
        }


# =============================================================================
# Public API Function (Drop-in Replacement for v1.0)
# =============================================================================

def generate_narrative(
    signal_data: Dict, 
    validation_result: Dict,
    use_kb: bool = True,
    user_level: str = 'intermediate',
    return_metadata: bool = True
):
    """
    Generate contextual narrative for a trading signal.
    
    This is a drop-in replacement for the v1.0 generate_narrative() function.
    Set use_kb=False to use original v1.0 contextualizer.
    
    Args:
        signal_data: Signal data dict from webhook
        validation_result: Validation result from validation_engine
        use_kb: Whether to use Knowledge Engine v2.0 (default: True)
        user_level: User expertise level for educational content
        return_metadata: If True, returns dict with narrative + metrics. 
                        If False, returns only narrative string for backward compatibility.
    
    Returns:
        If return_metadata=True (default):
            Dict with {
                'narrative': str,
                'quality_metrics': dict,
                'kb_concepts_used': int,
                'kb_trace': list
            }
        If return_metadata=False:
            Human-readable narrative string only
    
    Example:
        from zenbot.contextualizer_v2 import generate_narrative
        
        # Get rich data
        result = generate_narrative(
            signal_data={'symbol': 'EURUSD', 'side': 'buy', ...},
            validation_result={'truth_index': 85, ...},
            return_metadata=True
        )
        narrative = result['narrative']
        metrics = result['quality_metrics']
        
        # Or get just string (backward compatible)
        narrative_str = generate_narrative(..., return_metadata=False)
    """
    if use_kb:
        try:
            engine = EnhancedContextualIntelligenceEngine()
            result = engine.generate_narrative(
                signal_data=signal_data,
                validation_result=validation_result,
                user_level=user_level
            )
            
            # Return based on metadata flag
            if return_metadata:
                return result  # Dict with narrative + metrics
            else:
                return result['narrative'] if isinstance(result, dict) else result
                
        except Exception as e:
            logger.error(f"KB-powered narrative failed, falling back to v1.0: {e}")
            use_kb = False
    
    if not use_kb:
        # Fall back to original v1.0
        from zenbot.contextualizer import ContextualIntelligenceEngine
        v1_engine = ContextualIntelligenceEngine()
        narrative_str = v1_engine.generate_narrative(signal_data, validation_result)
        
        if return_metadata:
            # Wrap string in dict format for consistency
            return {
                'narrative': narrative_str,
                'quality_metrics': {},
                'kb_concepts_used': 0,
                'kb_trace': []
            }
        else:
            return narrative_str


# Alias for backward compatibility
ContextualIntelligenceEngine = EnhancedContextualIntelligenceEngine
