"""
Knowledge Query Engine
Intelligent semantic search and context retrieval for strategy-aware insights
"""
import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Q

from knowledge_base.models import KnowledgeEntry, QueryCache
from knowledge_base.kb_search import EmbeddingEngine
from .strategy_domains import STRATEGY_DOMAINS, get_strategy_info, get_related_strategies

logger = logging.getLogger(__name__)


class KnowledgeQueryEngine:
    """
    Main query interface for the Knowledge Base
    Provides semantic search, strategy context, and insight generation
    """
    
    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.cache_ttl = 3600 * 6  # 6 hours
    
    def search_concept(
        self,
        term: str,
        strategy: str = None,
        k: int = 5,
        min_quality: float = 0.5
    ) -> List[Dict]:
        """
        Search for trading concepts semantically
        
        Args:
            term: Search term or concept
            strategy: Optional strategy filter
            k: Number of results
            min_quality: Minimum quality score
            
        Returns:
            List of matching concepts with metadata
        """
        # Check cache first
        cache_key = f"kb_search:{term}:{strategy}:{k}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for: {term}")
            return cached
        
        # Generate query embedding
        query_emb = self.embedding_engine.encode_single(term)
        
        # Get all active entries
        queryset = KnowledgeEntry.objects.filter(
            is_active=True,
            quality_score__gte=min_quality
        ).exclude(embedding_full__isnull=True)
        
        if strategy:
            queryset = queryset.filter(category=strategy)
        
        # Compute similarities
        results = []
        for entry in queryset:
            try:
                emb_data = json.loads(entry.embedding_full)
                emb = np.array(emb_data)
                
                # Cosine similarity
                similarity = np.dot(query_emb, emb) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(emb)
                )
                
                results.append({
                    'entry': entry,
                    'similarity': float(similarity),
                    'term': entry.term,
                    'summary': entry.summary,
                    'definition': entry.definition,
                    'strategy': entry.category,
                    'quality': entry.quality_score,
                    'source': entry.source.name,
                    'examples': entry.examples if entry.examples else []
                })
            except Exception as e:
                logger.warning(f"Error processing entry {entry.id}: {e}")
                continue
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:k]
        
        # Cache results
        cache.set(cache_key, results, self.cache_ttl)
        
        # Update entry usage stats
        for result in results:
            result['entry'].increment_usage()
        
        logger.info(f"Found {len(results)} results for '{term}'")
        return results
    
    def strategy_context(
        self,
        strategy_name: str,
        topic: str = None,
        max_concepts: int = 10
    ) -> Dict:
        """
        Retrieve comprehensive strategy context and explanation
        
        Args:
            strategy_name: Strategy code (e.g., 'smc', 'ict')
            topic: Optional specific topic within strategy
            max_concepts: Maximum concepts to include
            
        Returns:
            Dict with strategy context, concepts, and explanations
        """
        # Get strategy metadata
        strategy_info = get_strategy_info(strategy_name)
        if not strategy_info:
            logger.warning(f"Unknown strategy: {strategy_name}")
            return {}
        
        # Build context dict
        context = {
            'strategy': strategy_name,
            'name': strategy_info['name'],
            'core_theory': {
                'aliases': strategy_info['aliases'],
                'psychology': strategy_info['psychology'],
                'risk_context': strategy_info['risk_context']
            },
            'concepts': [],
            'patterns': strategy_info['key_patterns'],
            'visual_markers': strategy_info['visual_markers'],
            'related_strategies': get_related_strategies(strategy_name)
        }
        
        # Get KB entries for this strategy
        entries = KnowledgeEntry.objects.filter(
            category=strategy_name,
            is_active=True,
            is_verified=True
        ).order_by('-quality_score')[:max_concepts]
        
        for entry in entries:
            concept_data = {
                'term': entry.term,
                'summary': entry.summary,
                'definition': entry.definition,
                'examples': self._parse_examples(entry.examples),
                'psychology': entry.psychology_context,
                'pitfalls': entry.common_pitfalls,
                'patterns': entry.market_behavior_patterns,
                'visual': entry.visual_description
            }
            
            # Filter by topic if provided
            if topic:
                if topic.lower() in entry.term.lower() or topic.lower() in entry.summary.lower():
                    context['concepts'].append(concept_data)
            else:
                context['concepts'].append(concept_data)
        
        logger.info(f"Retrieved context for {strategy_name}: {len(context['concepts'])} concepts")
        return context
    
    def generate_insight(
        self,
        context_features: Dict,
        paraphrase: bool = True
    ) -> str:
        """
        Generate intelligent market insight based on context features
        
        Args:
            context_features: Dict with signal data (strategy, behavior, session, etc.)
            paraphrase: Whether to use paraphrasing for variety
            
        Returns:
            Generated insight narrative
        """
        strategy = context_features.get('strategy', '').lower()
        behavior = context_features.get('market_behavior', '')
        session = context_features.get('session', '')
        regime = context_features.get('regime', '')
        structure = context_features.get('structure', '')
        
        # Get strategy context
        strategy_ctx = self.strategy_context(strategy) if strategy else {}
        
        # Search for relevant concepts
        concepts = []
        if behavior:
            concepts = self.search_concept(behavior, strategy=strategy, k=3)
        
        # Build insight narrative
        insight_parts = []
        
        # 1. Opening statement (contextual)
        if concepts:
            top_concept = concepts[0]
            opening = self._generate_opening(
                top_concept['term'],
                top_concept['summary'],
                strategy_ctx.get('name', ''),
                paraphrase
            )
            insight_parts.append(opening)
        
        # 2. Behavioral explanation
        if behavior and concepts:
            behavioral = self._generate_behavioral_explanation(
                behavior,
                concepts,
                strategy_ctx,
                paraphrase
            )
            if behavioral:
                insight_parts.append(behavioral)
        
        # 3. Session context
        if session:
            session_context = self._generate_session_context(
                session,
                strategy,
                regime,
                paraphrase
            )
            if session_context:
                insight_parts.append(session_context)
        
        # 4. Structure analysis
        if structure or regime:
            structure_analysis = self._generate_structure_analysis(
                structure,
                regime,
                strategy_ctx,
                paraphrase
            )
            if structure_analysis:
                insight_parts.append(structure_analysis)
        
        # Join parts
        insight = ' '.join(insight_parts)
        
        if not insight:
            insight = "Market conditions analyzed. Monitor price action for confirmation."
        
        logger.info(f"Generated insight ({len(insight)} chars)")
        return insight
    
    def get_concept_relationships(
        self,
        concept_term: str,
        relationship_type: str = None
    ) -> List[Dict]:
        """
        Get relationships for a concept
        
        Args:
            concept_term: Main concept
            relationship_type: Optional filter (prerequisite, related, opposite, example_of)
            
        Returns:
            List of relationship dicts
        """
        from knowledge_base.models import ConceptRelationship
        
        # Find the entry
        entry = KnowledgeEntry.objects.filter(
            term__iexact=concept_term,
            is_active=True
        ).first()
        
        if not entry:
            return []
        
        # Get relationships
        queryset = ConceptRelationship.objects.filter(
            Q(source_concept=entry) | Q(target_concept=entry)
        )
        
        if relationship_type:
            queryset = queryset.filter(relationship_type=relationship_type)
        
        relationships = []
        for rel in queryset:
            relationships.append({
                'source': rel.source_concept.term,
                'target': rel.target_concept.term,
                'type': rel.relationship_type,
                'strength': rel.strength,
                'bidirectional': rel.source_concept == entry
            })
        
        return relationships
    
    # Helper methods for insight generation
    
    def _generate_opening(
        self,
        concept: str,
        summary: str,
        strategy_name: str,
        paraphrase: bool
    ) -> str:
        """Generate opening statement"""
        templates = [
            f"This movement reflects {concept.lower()}, {summary.lower()}",
            f"The observed {concept.lower()} behavior indicates {summary.lower()}",
            f"Current price action shows {concept.lower()}, which means {summary.lower()}",
            f"Analysis reveals {concept.lower()} formation, characteristic of {summary.lower()}"
        ]
        
        if paraphrase:
            import random
            return random.choice(templates)
        return templates[0]
    
    def _generate_behavioral_explanation(
        self,
        behavior: str,
        concepts: List[Dict],
        strategy_ctx: Dict,
        paraphrase: bool
    ) -> str:
        """Generate behavioral explanation"""
        if not concepts:
            return ""
        
        top_concept = concepts[0]
        definition = top_concept.get('definition', '')[:200]
        
        templates = [
            f"This {behavior} pattern is typical in {strategy_ctx.get('name', 'this strategy')}, where {definition.lower()}",
            f"The {behavior} aligns with institutional behavior patterns described in {strategy_ctx.get('name', 'the framework')}",
            f"According to {strategy_ctx.get('name', 'this methodology')}, {behavior} signals {definition.lower()}"
        ]
        
        if paraphrase:
            import random
            return random.choice(templates)
        return templates[0]
    
    def _generate_session_context(
        self,
        session: str,
        strategy: str,
        regime: str,
        paraphrase: bool
    ) -> str:
        """Generate session-specific context"""
        session_info = {
            'london': 'high liquidity and institutional activity',
            'new york': 'peak volume and volatility expansion',
            'asian': 'range-bound behavior and liquidity setup',
            'tokyo': 'early positioning and range establishment'
        }
        
        session_lower = session.lower()
        info = session_info.get(session_lower, 'active trading')
        
        templates = [
            f"The {session} session amplifies this behavior due to {info}.",
            f"During {session} hours, {info} creates ideal conditions for this setup.",
            f"{session} session timing is significant as {info} dominates.",
            f"This aligns with {session} session characteristics of {info}."
        ]
        
        if paraphrase:
            import random
            return random.choice(templates)
        return templates[0]
    
    def _generate_structure_analysis(
        self,
        structure: str,
        regime: str,
        strategy_ctx: Dict,
        paraphrase: bool
    ) -> str:
        """Generate market structure analysis"""
        if not structure and not regime:
            return ""
        
        context = structure or regime
        
        templates = [
            f"The {context} structure supports continuation according to established patterns.",
            f"Market structure confirms {context} bias with multiple confluence factors.",
            f"This {context} formation aligns with historical probability zones.",
            f"{context.capitalize()} structure provides clear directional context."
        ]
        
        if paraphrase:
            import random
            return random.choice(templates)
        return templates[0]
    
    def _parse_examples(self, examples_field) -> List[str]:
        """Parse examples from JSON or text field"""
        if not examples_field:
            return []
        
        if isinstance(examples_field, list):
            return examples_field
        
        try:
            return json.loads(examples_field)
        except:
            # Split by newlines or bullet points
            return [e.strip() for e in examples_field.split('\n') if e.strip()]


class StrategyCrossReferencer:
    """
    Cross-reference concepts across multiple strategies
    Find intersections and complementary patterns
    """
    
    def __init__(self):
        self.query_engine = KnowledgeQueryEngine()
    
    def find_confluences(
        self,
        primary_strategy: str,
        context_features: Dict
    ) -> Dict:
        """
        Find confluence from multiple strategies for a setup
        
        Args:
            primary_strategy: Main strategy being used
            context_features: Signal context
            
        Returns:
            Dict with multi-strategy confluence analysis
        """
        # Get related strategies
        related = get_related_strategies(primary_strategy)
        
        confluence = {
            'primary': primary_strategy,
            'supporting_strategies': [],
            'confluence_score': 0.0,
            'aligned_concepts': []
        }
        
        # For each related strategy, find supporting concepts
        for related_strategy in related[:3]:  # Top 3
            if related_strategy == 'all':
                continue
            
            # Search for concepts in this strategy
            behavior = context_features.get('market_behavior', '')
            if behavior:
                results = self.query_engine.search_concept(
                    behavior,
                    strategy=related_strategy,
                    k=2
                )
                
                if results and results[0]['similarity'] > 0.3:
                    confluence['supporting_strategies'].append({
                        'strategy': related_strategy,
                        'concept': results[0]['term'],
                        'similarity': results[0]['similarity']
                    })
                    confluence['aligned_concepts'].append(results[0]['term'])
                    confluence['confluence_score'] += results[0]['similarity']
        
        # Normalize confluence score
        if confluence['supporting_strategies']:
            confluence['confluence_score'] /= len(confluence['supporting_strategies'])
        
        return confluence
    
    def get_multi_timeframe_context(
        self,
        strategy: str,
        htf_structure: str,
        ltf_pattern: str
    ) -> Dict:
        """
        Get multi-timeframe confluence context
        
        Args:
            strategy: Primary strategy
            htf_structure: Higher timeframe structure
            ltf_pattern: Lower timeframe pattern
            
        Returns:
            Multi-timeframe analysis dict
        """
        htf_concepts = self.query_engine.search_concept(htf_structure, k=2)
        ltf_concepts = self.query_engine.search_concept(ltf_pattern, k=2)
        
        return {
            'htf_analysis': htf_concepts[0] if htf_concepts else None,
            'ltf_analysis': ltf_concepts[0] if ltf_concepts else None,
            'alignment': htf_concepts and ltf_concepts,
            'confidence': 'high' if (htf_concepts and ltf_concepts) else 'medium'
        }


# Convenience functions
def search(term: str, strategy: str = None, k: int = 5) -> List[Dict]:
    """Quick search wrapper"""
    engine = KnowledgeQueryEngine()
    return engine.search_concept(term, strategy=strategy, k=k)


def get_strategy_explanation(strategy: str, topic: str = None) -> Dict:
    """Quick strategy context wrapper"""
    engine = KnowledgeQueryEngine()
    return engine.strategy_context(strategy, topic=topic)


def generate_market_insight(context: Dict) -> str:
    """Quick insight generation wrapper"""
    engine = KnowledgeQueryEngine()
    return engine.generate_insight(context, paraphrase=True)
