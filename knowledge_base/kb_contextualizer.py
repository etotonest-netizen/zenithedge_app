"""
Knowledge Base Integration for Contextualizer
Extends AI narrative generation with KB-powered explanations and citations
"""
import logging
from typing import Dict, List, Optional, Tuple
import random

logger = logging.getLogger(__name__)


class KBContextualizer:
    """
    Extends ContextualIntelligenceEngine with KB-powered explanations
    Provides concept definitions, examples, and source citations
    """
    
    def __init__(self, kb_search=None):
        """
        Initialize KB Contextualizer
        
        Args:
            kb_search: KnowledgeBaseSearch instance (optional, lazy-loaded)
        """
        self._kb_search = kb_search
        self._concept_cache = {}  # Cache for concept lookups
        
    @property
    def kb_search(self):
        """Lazy-load KB search to avoid circular imports"""
        if self._kb_search is None:
            try:
                from knowledge_base.kb_search import KnowledgeBaseSearch
                self._kb_search = KnowledgeBaseSearch()
                logger.info("Loaded KnowledgeBaseSearch")
            except ImportError:
                logger.warning("KB module not available")
                return None
        return self._kb_search
    
    def extract_concepts_from_signal(self, signal_data: Dict, validation_result: Dict) -> List[str]:
        """
        Extract trading concepts mentioned in signal data
        
        Args:
            signal_data: Signal data dict
            validation_result: Validation result dict
        
        Returns:
            List of concept terms to lookup in KB
        """
        concepts = []
        
        # Strategy-based concepts
        strategy = signal_data.get('strategy', '').lower()
        if strategy in ['smc', 'smart money']:
            concepts.extend(['order block', 'fair value gap', 'liquidity sweep', 'break of structure'])
        elif strategy in ['ict', 'inner circle']:
            concepts.extend(['optimal trade entry', 'kill zone', 'power of 3'])
        elif strategy == 'elliott_wave':
            concepts.extend(['elliott wave', 'fibonacci retracement', 'impulse wave'])
        
        # Regime-based concepts
        regime = signal_data.get('regime', '').lower()
        if regime == 'breakout':
            concepts.append('breakout')
        elif regime == 'trending':
            concepts.append('trend')
        elif regime == 'ranging':
            concepts.extend(['support', 'resistance', 'consolidation'])
        
        # Market structure concepts
        if 'structure' in validation_result.get('breakdown', {}).get('technical', {}).get('commentary', '').lower():
            concepts.append('market structure')
        
        # Risk management concepts
        if signal_data.get('sl') and signal_data.get('tp'):
            concepts.extend(['stop loss', 'take profit', 'risk reward'])
        
        # Deduplicate while preserving order
        seen = set()
        unique_concepts = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique_concepts.append(c)
        
        return unique_concepts[:5]  # Limit to top 5 concepts
    
    def lookup_concepts(
        self, 
        concepts: List[str],
        symbol: str = '',
        asset_class: str = 'forex'
    ) -> Dict[str, Dict]:
        """
        Lookup concepts in KB
        
        Args:
            concepts: List of concept terms
            symbol: Trading symbol for cache key
            asset_class: Asset class filter
        
        Returns:
            Dict mapping concept -> KB entry info
        """
        if not self.kb_search:
            return {}
        
        results = {}
        
        for concept in concepts:
            # Check cache
            cache_key = f"{concept}|{asset_class}"
            if cache_key in self._concept_cache:
                results[concept] = self._concept_cache[cache_key]
                continue
            
            # Search KB
            try:
                search_results = self.kb_search.search(
                    query=concept,
                    k=1,  # Top result only
                    asset_class=asset_class if asset_class != 'forex' else None,
                    use_cache=True,
                    symbol=symbol
                )
                
                if search_results:
                    best_match = search_results[0]
                    entry = best_match['entry']
                    
                    results[concept] = {
                        'term': entry.term,
                        'summary': entry.summary,
                        'definition': entry.definition[:500],  # Truncate
                        'category': entry.category,
                        'source': entry.source.name,
                        'source_url': entry.source_url,
                        'score': best_match['score'],
                        'quality': entry.quality_score
                    }
                    
                    # Cache result
                    self._concept_cache[cache_key] = results[concept]
                    
            except Exception as e:
                logger.error(f"KB lookup failed for '{concept}': {e}")
        
        return results
    
    def generate_kb_enhanced_narrative(
        self,
        signal_data: Dict,
        validation_result: Dict,
        base_narrative: str
    ) -> Tuple[str, Dict]:
        """
        Enhance base narrative with KB explanations
        
        Args:
            signal_data: Signal data dict
            validation_result: Validation result dict
            base_narrative: Original narrative from ContextualIntelligenceEngine
        
        Returns:
            Tuple of (enhanced_narrative, kb_trace)
            - enhanced_narrative: Narrative with KB explanations
            - kb_trace: Provenance data for explainability
        """
        # Extract concepts
        concepts = self.extract_concepts_from_signal(signal_data, validation_result)
        
        if not concepts:
            return base_narrative, {'concepts': [], 'sources': []}
        
        # Lookup concepts in KB
        symbol = signal_data.get('symbol', '')
        asset_class = self._detect_asset_class(symbol)
        
        kb_results = self.lookup_concepts(concepts, symbol, asset_class)
        
        if not kb_results:
            return base_narrative, {'concepts': concepts, 'sources': []}
        
        # Build KB trace for explainability
        kb_trace = {
            'concepts': concepts,
            'sources': [],
            'entries': []
        }
        
        # Compose KB explanations
        explanations = []
        
        for concept, kb_data in kb_results.items():
            # Add to trace
            kb_trace['sources'].append({
                'term': kb_data['term'],
                'source': kb_data['source'],
                'url': kb_data['source_url'],
                'score': kb_data['score']
            })
            
            kb_trace['entries'].append({
                'concept': concept,
                'term': kb_data['term'],
                'summary': kb_data['summary'],
                'category': kb_data['category']
            })
            
            # Generate explanation text
            explanation = self._compose_concept_explanation(
                concept,
                kb_data,
                signal_data
            )
            explanations.append(explanation)
        
        # Insert explanations into narrative
        enhanced_narrative = self._insert_kb_explanations(
            base_narrative,
            explanations,
            kb_trace
        )
        
        return enhanced_narrative, kb_trace
    
    def _compose_concept_explanation(
        self,
        concept: str,
        kb_data: Dict,
        signal_data: Dict
    ) -> str:
        """
        Compose explanation for a single concept
        
        Format: "Term (definition): application to current market. Source: X"
        """
        term = kb_data['term']
        summary = kb_data['summary']
        source = kb_data['source']
        
        # Contextualize to current signal
        side = signal_data.get('side', 'buy').lower()
        price = signal_data.get('price', 0)
        regime = signal_data.get('regime', 'trending')
        
        # Build contextual application
        application = self._generate_contextual_application(
            concept,
            side,
            price,
            regime,
            kb_data
        )
        
        # Compose explanation
        explanation = f"{term} ({summary}). {application} Source: {source}."
        
        return explanation
    
    def _generate_contextual_application(
        self,
        concept: str,
        side: str,
        price: float,
        regime: str,
        kb_data: Dict
    ) -> str:
        """Generate context-specific application of concept"""
        category = kb_data.get('category', '')
        
        # Application templates by category
        if category == 'smc':
            if side == 'buy':
                return f"Here, institutional demand at {price:.5f} suggests bullish continuation within {regime} structure"
            else:
                return f"Here, institutional supply at {price:.5f} suggests bearish continuation within {regime} structure"
        
        elif category == 'ict':
            if 'kill zone' in concept.lower():
                return "Current timing aligns with institutional accumulation window"
            elif 'optimal' in concept.lower():
                return f"Entry zone at {price:.5f} offers favorable risk-reward alignment"
        
        elif category == 'ta':
            if regime == 'breakout':
                return f"Price action confirms momentum beyond key level at {price:.5f}"
            elif regime == 'trending':
                return "Technical structure supports directional bias"
        
        # Generic application
        if side == 'buy':
            return f"This bullish setup at {price:.5f} reflects {regime} market conditions"
        else:
            return f"This bearish setup at {price:.5f} reflects {regime} market conditions"
    
    def _insert_kb_explanations(
        self,
        base_narrative: str,
        explanations: List[str],
        kb_trace: Dict
    ) -> str:
        """
        Insert KB explanations into base narrative
        
        Strategy: Add explanations after reasoning section
        """
        # Split narrative into parts (header, reasoning, suggestion)
        parts = base_narrative.split('\n\n')
        
        if len(parts) < 3:
            # Fallback: append explanations
            kb_section = "\n\n**Technical Context:**\n" + "\n".join(f"• {e}" for e in explanations)
            return base_narrative + kb_section
        
        header, reasoning, suggestion = parts[0], parts[1], parts[2]
        
        # Insert explanations between reasoning and suggestion
        kb_section = "\n\n**Technical Context:**\n" + "\n".join(f"• {e}" for e in explanations)
        
        enhanced = f"{header}\n\n{reasoning}{kb_section}\n\n{suggestion}"
        
        # Add source attribution
        sources = kb_trace.get('sources', [])
        if sources:
            source_names = list(set(s['source'] for s in sources))
            attribution = f"\n\n*References: {', '.join(source_names[:3])}*"
            enhanced += attribution
        
        return enhanced
    
    def _detect_asset_class(self, symbol: str) -> str:
        """Detect asset class from symbol"""
        symbol_upper = symbol.upper()
        
        # Forex pairs
        forex_keywords = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
        if any(kw in symbol_upper for kw in forex_keywords):
            return 'forex'
        
        # Crypto
        crypto_keywords = ['BTC', 'ETH', 'XRP', 'USDT', 'CRYPTO']
        if any(kw in symbol_upper for kw in crypto_keywords):
            return 'crypto'
        
        # Commodities
        commodity_keywords = ['XAU', 'XAG', 'OIL', 'GOLD', 'SILVER']
        if any(kw in symbol_upper for kw in commodity_keywords):
            return 'commodities'
        
        # Indices/Futures
        if symbol_upper in ['ES', 'NQ', 'YM', 'RTY', 'SPX', 'NDX']:
            return 'futures'
        
        # Default to stocks
        return 'stocks'
    
    def get_related_concepts(self, entry_id: int, max_related: int = 3) -> List[Dict]:
        """
        Get related concepts from knowledge graph
        
        Args:
            entry_id: KB entry ID
            max_related: Max number of related concepts
        
        Returns:
            List of related concept dicts
        """
        if not self.kb_search:
            return []
        
        try:
            from knowledge_base.models import KnowledgeEntry
            
            entry = KnowledgeEntry.objects.get(id=entry_id)
            related = self.kb_search.get_related_concepts(entry, max_depth=1)
            
            return related[:max_related]
            
        except Exception as e:
            logger.error(f"Failed to get related concepts: {e}")
            return []
