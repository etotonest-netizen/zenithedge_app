"""
Knowledge Base Integration for ZenBot
Connects the Knowledge Engine v2.0 with ZenBot for intelligent Q&A responses.
"""
import logging
from django.conf import settings
from knowledge_engine.query_engine import KnowledgeQueryEngine, StrategyCrossReferencer
from knowledge_engine.insight_builder import InsightBuilder
from knowledge_engine.strategy_domains import classify_content_by_keywords, get_strategy_info

logger = logging.getLogger('zenbot.kb')


class KBQuestionAnswerer:
    """
    Integrates Knowledge Engine v2.0 with ZenBot for intelligent Q&A.
    Provides natural language responses to trading strategy questions.
    """
    
    def __init__(self):
        self.query_engine = KnowledgeQueryEngine()
        self.insight_builder = InsightBuilder()
        self.cross_referencer = StrategyCrossReferencer()
        
        # Question type patterns
        self.question_patterns = {
            'what_is': ['what is', 'what are', 'define', 'explain', 'tell me about'],
            'how_to': ['how do i', 'how to', 'how can', 'steps to', 'guide to'],
            'when': ['when should', 'when to', 'timing', 'best time'],
            'why': ['why', 'reason', 'why does', 'why is'],
            'compare': ['difference between', 'compare', 'versus', 'vs', 'better than'],
            'example': ['example', 'show me', 'demonstrate'],
        }
    
    def answer_question(self, question, context=None):
        """
        Main entry point for answering trading questions.
        
        Args:
            question (str): User's question
            context (dict, optional): Additional context (user stats, current signal, etc.)
        
        Returns:
            dict: {
                'answer': str,
                'confidence': float,
                'sources': list,
                'related_concepts': list,
                'strategy': str or None
            }
        """
        question = question.strip()
        
        # Classify question type
        question_type = self._classify_question(question)
        
        # Detect strategy mentioned in question
        strategy_list = classify_content_by_keywords(question)
        strategy = strategy_list[0] if strategy_list else None
        
        # Extract key concepts from question
        concepts = self._extract_concepts(question)
        
        logger.info(f"KB Q&A: Type={question_type}, Strategy={strategy}, Concepts={concepts}")
        
        # Route to appropriate handler
        if question_type == 'what_is':
            return self._handle_definition_question(concepts, strategy, context)
        
        elif question_type == 'how_to':
            return self._handle_howto_question(concepts, strategy, context)
        
        elif question_type == 'when':
            return self._handle_timing_question(concepts, strategy, context)
        
        elif question_type == 'why':
            return self._handle_why_question(concepts, strategy, context)
        
        elif question_type == 'compare':
            return self._handle_comparison_question(concepts, strategy, context)
        
        elif question_type == 'example':
            return self._handle_example_question(concepts, strategy, context)
        
        else:
            # General search
            return self._handle_general_search(question, strategy, context)
    
    def _classify_question(self, question):
        """Classify question type based on patterns"""
        question_lower = question.lower()
        
        for q_type, patterns in self.question_patterns.items():
            if any(pattern in question_lower for pattern in patterns):
                return q_type
        
        return 'general'
    
    def _extract_concepts(self, question):
        """Extract key trading concepts from question"""
        # Use Knowledge Engine's concept extractor
        from knowledge_engine.advanced_nlp import StrategyConceptExtractor
        
        extractor = StrategyConceptExtractor()
        concept_dicts = extractor.extract_concepts(question)
        
        # Extract just the concept strings
        return [c['concept'] if isinstance(c, dict) else c for c in concept_dicts]
    
    def _handle_definition_question(self, concepts, strategy, context):
        """
        Handle "What is X?" questions.
        Example: "What is an order block?"
        """
        if not concepts:
            return self._no_match_response()
        
        # Search for the main concept
        main_concept = concepts[0] if concepts else None
        results = self.query_engine.search_concept(
            term=main_concept,
            strategy=strategy,
            k=3
        )
        
        if not results:
            return self._no_match_response(concept=main_concept)
        
        # Get the best match
        best_match = results[0]
        entry = best_match['entry']
        
        # Determine user level from context
        user_level = context.get('user_level', 'intermediate') if context else 'intermediate'
        
        # Build educational explanation
        explanation = self.insight_builder.build_educational_explanation(
            concept_term=entry.term,
            user_level=user_level
        )
        
        # Build full response (explanation is already a string)
        answer = explanation
        
        # Add related concepts if available
        if entry.related_concepts:
            related = entry.related_concepts[:3]
            answer += f"\n\n**Related Concepts:** {', '.join(related)}"
        
        # Add visual description if available
        if entry.visual_description:
            answer += f"\n\n**Visual Markers:** {entry.visual_description}"
        
        return {
            'answer': answer,
            'confidence': best_match['similarity'] * 100,
            'sources': [entry.source_url] if entry.source_url else [],
            'related_concepts': entry.related_concepts or [],
            'strategy': entry.category,
            'kb_trace': {
                'concepts_used': [entry.term],
                'query_type': 'definition',
                'user_level': user_level
            }
        }
    
    def _handle_howto_question(self, concepts, strategy, context):
        """
        Handle "How to X?" questions.
        Example: "How do I trade an order block?"
        """
        if not concepts:
            return self._no_match_response()
        
        main_concept = concepts[0]
        results = self.query_engine.search_concept(main_concept, strategy, k=3)
        
        if not results:
            return self._no_match_response(concept=main_concept)
        
        # Get entries
        entries = [r['entry'] for r in results]
        
        # Build step-by-step guide
        answer = f"**How to Trade {main_concept.title()}:**\n\n"
        
        # Use best match for main explanation
        best_entry = entries[0]
        
        # Step 1: Identification
        answer += "**1. Identification**\n"
        if best_entry.visual_description:
            answer += f"{best_entry.visual_description}\n\n"
        else:
            answer += f"Look for {main_concept} patterns on your chart.\n\n"
        
        # Step 2: Context
        answer += "**2. Market Context**\n"
        if best_entry.market_behavior_patterns:
            patterns = best_entry.market_behavior_patterns[:2]
            answer += f"Ensure market shows: {', '.join(patterns)}\n\n"
        else:
            answer += f"Confirm market aligns with your {strategy or 'strategy'} rules.\n\n"
        
        # Step 3: Entry Setup
        answer += "**3. Entry Setup**\n"
        if best_entry.trade_structures:
            structures = best_entry.trade_structures[:2]
            answer += f"Use structures like: {', '.join(structures)}\n\n"
        else:
            answer += "Wait for price to reach your entry zone.\n\n"
        
        # Step 4: Risk Management
        answer += "**4. Risk Management**\n"
        answer += "Set stop loss, take profit, and calculate proper position size.\n\n"
        
        # Add common pitfalls
        if best_entry.common_pitfalls:
            answer += "**⚠️ Common Pitfalls:**\n"
            for pitfall in best_entry.common_pitfalls[:3]:
                answer += f"• {pitfall}\n"
        
        return {
            'answer': answer,
            'confidence': results[0]['similarity'] * 100,
            'sources': [e.source_url for e in entries if e.source_url],
            'related_concepts': best_entry.related_concepts or [],
            'strategy': strategy,
            'kb_trace': {
                'concepts_used': [e.term for e in entries],
                'query_type': 'howto'
            }
        }
    
    def _handle_timing_question(self, concepts, strategy, context):
        """
        Handle "When to X?" questions.
        Example: "When should I enter after a liquidity sweep?"
        """
        if not concepts:
            return self._no_match_response()
        
        main_concept = concepts[0]
        results = self.query_engine.search_concept(main_concept, strategy, k=2)
        
        if not results:
            return self._no_match_response(concept=main_concept)
        
        entry = results[0]['entry']
        
        # Build timing-focused answer
        answer = f"**Timing for {main_concept.title()}:**\n\n"
        
        # Market behavior patterns indicate timing
        if entry.market_behavior_patterns:
            answer += "**Market Conditions:**\n"
            for pattern in entry.market_behavior_patterns[:3]:
                answer += f"• {pattern}\n"
            answer += "\n"
        
        # Session timing
        answer += "**Best Sessions:**\n"
        if strategy in ['smc', 'ict', 'liquidity']:
            answer += "• London open (3-5 AM EST) - High liquidity\n"
            answer += "• New York open (9:30-11 AM EST) - Major moves\n\n"
        else:
            answer += "• Trade during active market hours\n"
            answer += "• Avoid low-volume periods\n\n"
        
        # Psychology context
        if entry.psychology_context:
            answer += "**Trader Psychology:**\n"
            answer += f"{entry.psychology_context}\n\n"
        
        # Common pitfalls related to timing
        if entry.common_pitfalls:
            timing_pitfalls = [p for p in entry.common_pitfalls if any(word in p.lower() for word in ['early', 'late', 'patience', 'wait', 'timing'])]
            if timing_pitfalls:
                answer += "**Avoid These Timing Mistakes:**\n"
                for pitfall in timing_pitfalls[:2]:
                    answer += f"• {pitfall}\n"
        
        return {
            'answer': answer,
            'confidence': results[0]['similarity'] * 100,
            'sources': [entry.source_url] if entry.source_url else [],
            'related_concepts': entry.related_concepts or [],
            'strategy': entry.category,
            'kb_trace': {
                'concepts_used': [entry.term],
                'query_type': 'timing'
            }
        }
    
    def _handle_why_question(self, concepts, strategy, context):
        """
        Handle "Why X?" questions.
        Example: "Why does price respect order blocks?"
        """
        if not concepts:
            return self._no_match_response()
        
        main_concept = concepts[0]
        results = self.query_engine.search_concept(main_concept, strategy, k=2)
        
        if not results:
            return self._no_match_response(concept=main_concept)
        
        entry = results[0]['entry']
        
        # Build explanation-focused answer
        answer = f"**Why {main_concept.title()} Works:**\n\n"
        
        # Core definition
        answer += f"{entry.definition}\n\n"
        
        # Psychology context explains the "why"
        if entry.psychology_context:
            answer += "**Market Psychology:**\n"
            answer += f"{entry.psychology_context}\n\n"
        
        # Market behavior patterns
        if entry.market_behavior_patterns:
            answer += "**Market Mechanics:**\n"
            for pattern in entry.market_behavior_patterns[:3]:
                answer += f"• {pattern}\n"
            answer += "\n"
        
        # Related concepts provide deeper context
        if entry.related_concepts:
            answer += "**Connected Concepts:**\n"
            answer += f"Understanding {main_concept} requires knowledge of: {', '.join(entry.related_concepts[:3])}\n"
        
        return {
            'answer': answer,
            'confidence': results[0]['similarity'] * 100,
            'sources': [entry.source_url] if entry.source_url else [],
            'related_concepts': entry.related_concepts or [],
            'strategy': entry.category,
            'kb_trace': {
                'concepts_used': [entry.term],
                'query_type': 'why'
            }
        }
    
    def _handle_comparison_question(self, concepts, strategy, context):
        """
        Handle comparison questions.
        Example: "What's the difference between order block and supply zone?"
        """
        if len(concepts) < 2:
            # Try to infer second concept from strategy
            if concepts and strategy:
                strategy_info = get_strategy_info(strategy)
                if strategy_info and 'core_concepts' in strategy_info:
                    # Find a related concept
                    concepts.append(strategy_info['core_concepts'][0])
        
        if len(concepts) < 2:
            return {
                'answer': "To compare concepts, please mention both in your question. For example: 'What's the difference between order blocks and supply zones?'",
                'confidence': 0,
                'sources': [],
                'related_concepts': [],
                'strategy': None
            }
        
        concept_a = concepts[0]
        concept_b = concepts[1]
        
        # Build comparison narrative
        comparison = self.insight_builder.build_comparison_narrative(
            concept_a=concept_a,
            concept_b=concept_b
        )
        
        return {
            'answer': comparison,  # Returns string directly
            'confidence': 70,
            'sources': [],
            'related_concepts': [concept_a, concept_b],
            'strategy': strategy,
            'kb_trace': {
                'concepts_used': [concept_a, concept_b],
                'query_type': 'comparison'
            }
        }
    
    def _handle_example_question(self, concepts, strategy, context):
        """
        Handle example requests.
        Example: "Show me an example of a fair value gap trade"
        """
        if not concepts:
            return self._no_match_response()
        
        main_concept = concepts[0]
        results = self.query_engine.search_concept(main_concept, strategy, k=2)
        
        if not results:
            return self._no_match_response(concept=main_concept)
        
        entry = results[0]['entry']
        
        # Build example-focused answer
        answer = f"**Example: {main_concept.title()} Trade**\n\n"
        
        # Setup description
        answer += "**Setup:**\n"
        if entry.visual_description:
            answer += f"{entry.visual_description}\n\n"
        
        # Trade structure example
        if entry.trade_structures:
            answer += "**Structure:**\n"
            for structure in entry.trade_structures[:2]:
                answer += f"• {structure}\n"
            answer += "\n"
        
        # Market behavior example
        if entry.market_behavior_patterns:
            answer += "**Market Behavior:**\n"
            answer += f"Price shows: {entry.market_behavior_patterns[0]}\n\n"
        
        # Example scenario
        answer += "**Example Scenario:**\n"
        answer += f"1. Identify the {main_concept} on your chart\n"
        answer += "2. Wait for price to approach the level\n"
        answer += "3. Look for confirmation (rejection, volume, structure)\n"
        answer += "4. Enter with appropriate risk management\n\n"
        
        # Add real-world context
        if entry.psychology_context:
            answer += "**Real Trading Context:**\n"
            answer += f"{entry.psychology_context}\n"
        
        return {
            'answer': answer,
            'confidence': results[0]['similarity'] * 100,
            'sources': [entry.source_url] if entry.source_url else [],
            'related_concepts': entry.related_concepts or [],
            'strategy': entry.category,
            'kb_trace': {
                'concepts_used': [entry.term],
                'query_type': 'example'
            }
        }
    
    def _handle_general_search(self, question, strategy, context):
        """
        Handle general questions that don't fit specific patterns.
        Falls back to semantic search.
        """
        results = self.query_engine.search_concept(
            term=question,
            strategy=strategy,
            k=3
        )
        
        if not results:
            return self._no_match_response()
        
        # Build general answer from top results
        answer = "Based on your question, here's what I found:\n\n"
        
        for i, result in enumerate(results[:2], 1):
            entry = result['entry']
            answer += f"**{i}. {entry.term}**\n"
            answer += f"{entry.definition[:200]}{'...' if len(entry.definition) > 200 else ''}\n\n"
        
        # Suggest related concepts
        all_related = []
        for result in results:
            if result['entry'].related_concepts:
                all_related.extend(result['entry'].related_concepts)
        
        if all_related:
            unique_related = list(set(all_related))[:5]
            answer += f"**Related topics:** {', '.join(unique_related)}"
        
        return {
            'answer': answer,
            'confidence': results[0]['similarity'] * 100,
            'sources': [r['entry'].source_url for r in results if r['entry'].source_url],
            'related_concepts': list(set(all_related))[:5] if all_related else [],
            'strategy': results[0]['entry'].category,
            'kb_trace': {
                'concepts_used': [r['entry'].term for r in results],
                'query_type': 'general_search'
            }
        }
    
    def _no_match_response(self, concept=None):
        """Return response when no matches found"""
        if concept:
            answer = f"I couldn't find information about '{concept}' in my knowledge base. "
        else:
            answer = "I couldn't find relevant information for your question. "
        
        answer += "\n\nTry asking about:\n"
        answer += "• Order blocks, fair value gaps, liquidity sweeps\n"
        answer += "• Smart money concepts (SMC) or ICT strategies\n"
        answer += "• Trend following, breakout trading\n"
        answer += "• Risk management and trade structures"
        
        return {
            'answer': answer,
            'confidence': 0,
            'sources': [],
            'related_concepts': [],
            'strategy': None,
            'kb_trace': {
                'concepts_used': [],
                'query_type': 'no_match'
            }
        }
    
    def get_strategy_overview(self, strategy_name):
        """
        Get comprehensive overview of a trading strategy.
        
        Args:
            strategy_name (str): Strategy identifier (smc, ict, trend, etc.)
        
        Returns:
            dict: Strategy overview with concepts, patterns, psychology
        """
        strategy_context = self.query_engine.strategy_context(
            strategy_name=strategy_name,
            topic=None
        )
        
        if not strategy_context:
            return {
                'answer': f"Strategy '{strategy_name}' not found in knowledge base.",
                'confidence': 0
            }
        
        # Build comprehensive overview
        answer = f"**{strategy_context['name']}**\n\n"
        answer += f"{strategy_context['core_theory']}\n\n"
        
        # Core concepts
        if strategy_context.get('core_concepts'):
            answer += "**Core Concepts:**\n"
            for concept in strategy_context['core_concepts'][:5]:
                answer += f"• {concept}\n"
            answer += "\n"
        
        # Key patterns
        if strategy_context.get('patterns'):
            answer += "**Key Patterns:**\n"
            for pattern in strategy_context['patterns'][:5]:
                answer += f"• {pattern}\n"
            answer += "\n"
        
        # Psychology
        if strategy_context.get('psychology'):
            answer += f"**Psychology:** {strategy_context['psychology']}\n\n"
        
        # Risk context
        if strategy_context.get('risk_context'):
            answer += f"**Risk Management:** {strategy_context['risk_context']}\n\n"
        
        # KB entries
        if strategy_context.get('kb_entries'):
            answer += f"**Knowledge Base:** {len(strategy_context['kb_entries'])} concepts documented\n"
        
        return {
            'answer': answer,
            'confidence': 95,
            'sources': [],
            'related_concepts': strategy_context.get('core_concepts', []),
            'strategy': strategy_name,
            'kb_trace': {
                'query_type': 'strategy_overview',
                'strategy': strategy_name
            }
        }


# =============================================================================
# Public API Functions
# =============================================================================

def answer_trading_question(question, context=None):
    """
    Public API for answering trading questions using Knowledge Engine.
    
    Args:
        question (str): User's question
        context (dict, optional): Additional context
    
    Returns:
        dict: Answer with confidence, sources, related concepts
    
    Example:
        >>> result = answer_trading_question("What is an order block?")
        >>> print(result['answer'])
        >>> print(f"Confidence: {result['confidence']}%")
    """
    qa = KBQuestionAnswerer()
    return qa.answer_question(question, context)


def get_strategy_explanation(strategy_name):
    """
    Get comprehensive explanation of a trading strategy.
    
    Args:
        strategy_name (str): Strategy identifier (smc, ict, trend, etc.)
    
    Returns:
        dict: Strategy overview
    
    Example:
        >>> result = get_strategy_explanation('smc')
        >>> print(result['answer'])
    """
    qa = KBQuestionAnswerer()
    return qa.get_strategy_overview(strategy_name)


def search_knowledge_base(search_term, strategy_filter=None, limit=5):
    """
    Direct search of knowledge base.
    
    Args:
        search_term (str): Search query
        strategy_filter (str, optional): Filter by strategy
        limit (int): Maximum results
    
    Returns:
        list: List of matching entries with similarity scores
    
    Example:
        >>> results = search_knowledge_base("liquidity", strategy_filter="smc")
        >>> for r in results:
        >>>     print(f"{r['entry'].term}: {r['similarity']:.2f}")
    """
    engine = KnowledgeQueryEngine()
    return engine.search_concept(search_term, strategy=strategy_filter, k=limit)
