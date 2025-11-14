"""
Contextual Intelligence Engine for ZenithEdge Trading Hub

This module transforms validated trading signals into human-readable narratives
that provide context, reasoning, and actionable insights for traders.

Uses NLP (spaCy, TextBlob) to analyze signal patterns and generate
professional trading insights with proper context and risk management guidance.

Author: ZenithEdge Team
Version: 1.0
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from textblob import TextBlob

logger = logging.getLogger(__name__)


class ContextualIntelligenceEngine:
    """
    NLP-powered narrative generator for trading signals.
    
    Transforms technical signal data and validation results into
    contextualized insights that traders can understand and act upon.
    
    Features:
    - 3-part narrative structure (header, reasoning, suggestion)
    - Strategy-aware language (SMC, ICT, Elliott Wave, etc.)
    - Session-aware timing context (London, NY, Asia)
    - Sentiment integration from news events
    - Risk management guidance based on validation scores
    - Adaptive tone (analytical, brief, confident)
    """
    
    # Strategy-specific terminology
    STRATEGY_LANGUAGE = {
        'smc': {
            'keywords': ['CHoCH', 'BOS', 'Fair Value Gap', 'Order Block', 'Liquidity Sweep'],
            'concepts': ['market structure', 'supply/demand zones', 'institutional behavior']
        },
        'ict': {
            'keywords': ['Kill Zone', 'Power of 3', 'Balanced Price Range', 'PD Array'],
            'concepts': ['institutional timing', 'algorithmic entries', 'manipulation']
        },
        'elliott_wave': {
            'keywords': ['Wave 3', 'Impulse', 'Corrective', 'Fibonacci'],
            'concepts': ['wave structure', 'retracement levels', 'cycle analysis']
        },
        'price_action': {
            'keywords': ['Support', 'Resistance', 'Breakout', 'Reversal Pattern'],
            'concepts': ['key levels', 'chart patterns', 'momentum']
        },
        'default': {
            'keywords': ['Setup', 'Signal', 'Entry', 'Target'],
            'concepts': ['technical analysis', 'risk management', 'market conditions']
        }
    }
    
    # Session timing context
    SESSION_CONTEXT = {
        'london': {'start': 8, 'end': 16, 'description': 'London session volatility'},
        'newyork': {'start': 13, 'end': 21, 'description': 'New York session liquidity'},
        'asia': {'start': 0, 'end': 8, 'description': 'Asian session consolidation'},
        'overlap': {'start': 13, 'end': 16, 'description': 'London-NY overlap (high liquidity)'}
    }
    
    # Regime descriptions
    REGIME_CONTEXT = {
        'trending': 'strong directional bias',
        'ranging': 'consolidating within range',
        'volatile': 'high volatility environment',
        'breakout': 'breakout momentum building',
        'reversal': 'potential reversal forming'
    }
    
    def __init__(self):
        """Initialize the contextualizer."""
        logger.info("Contextual Intelligence Engine initialized")
    
    def generate_narrative(self, signal_data: Dict, validation_result: Dict) -> str:
        """
        Generate a comprehensive narrative for a validated signal.
        
        Args:
            signal_data: Raw signal data from webhook
            validation_result: Output from validation_engine.validate_signal()
        
        Returns:
            Human-readable narrative string with 3 parts:
            1. Header: Symbol, confidence, strategy
            2. Reasoning: Why this signal matters (context)
            3. Suggestion: Actionable guidance with risk management
        
        Example Output:
            "EURUSD setup detected — 83/100 confidence (SMC)
            
            CHoCH and Fair Value Gap alignment during London session with 
            bullish sentiment from recent ECB data. Market structure shows 
            strong directional bias with low recent drawdown.
            
            Long bias valid above 1.0850; consider partials near 1.0910. 
            Risk < 1.5%. Watch for liquidity sweeps near entry."
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
            
            truth_index = validation_result.get('truth_index', 0)
            breakdown = validation_result.get('breakdown', {})
            status = validation_result.get('status', 'unknown')
            
            # Build narrative parts
            header = self._build_header(symbol, truth_index, strategy, side)
            reasoning = self._build_reasoning(
                signal_data, validation_result, breakdown
            )
            suggestion = self._build_suggestion(
                signal_data, truth_index, status
            )
            
            # Combine into full narrative
            narrative = f"{header}\n\n{reasoning}\n\n{suggestion}"
            
            logger.info(f"Generated narrative for {symbol} ({truth_index:.1f}/100)")
            return narrative
            
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return self._fallback_narrative(signal_data, validation_result)
    
    def _build_header(self, symbol: str, truth_index: float, 
                      strategy: str, side: str) -> str:
        """
        Build concise header with essential info.
        
        Format: "SYMBOL setup detected — XX/100 confidence (STRATEGY)"
        """
        strategy_display = strategy.upper() if strategy != 'default' else 'Technical'
        direction = "LONG" if side == "BUY" else "SHORT"
        
        # Add quality indicator
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
    
    def _build_reasoning(self, signal_data: Dict, validation_result: Dict,
                        breakdown: Dict) -> str:
        """
        Build contextual reasoning section explaining WHY this signal matters.
        
        Incorporates:
        - Strategy-specific language
        - Session timing context
        - Market regime
        - Sentiment alignment
        - Technical validation scores
        """
        reasoning_parts = []
        
        strategy = signal_data.get('strategy', 'default').lower()
        regime = signal_data.get('regime', 'trending').lower()
        
        # 1. Strategy context
        strategy_lang = self.STRATEGY_LANGUAGE.get(
            strategy, self.STRATEGY_LANGUAGE['default']
        )
        
        if breakdown.get('technical_integrity', 0) >= 0.80:
            # Strong technical setup
            keywords = strategy_lang['keywords'][:2]  # Use first 2 keywords
            reasoning_parts.append(
                f"{' and '.join(keywords)} alignment "
                f"showing {self.REGIME_CONTEXT.get(regime, 'market conditions')}"
            )
        else:
            # Weaker technical - generic description
            reasoning_parts.append(
                f"Setup forming with {self.REGIME_CONTEXT.get(regime, 'current conditions')}"
            )
        
        # 2. Session timing
        session = self._get_current_session()
        if session:
            session_info = self.SESSION_CONTEXT.get(session, {})
            reasoning_parts.append(
                f"during {session_info.get('description', 'current session')}"
            )
        
        # 3. Sentiment context
        sentiment_score = breakdown.get('sentiment_coherence', 0)
        if sentiment_score >= 0.85:
            reasoning_parts.append(
                "with supportive news sentiment and fundamental alignment"
            )
        elif sentiment_score >= 0.70:
            reasoning_parts.append("with neutral market backdrop")
        elif sentiment_score < 0.50:
            reasoning_parts.append(
                "despite conflicting news sentiment (caution advised)"
            )
        
        # 4. Historical reliability
        historical_score = breakdown.get('historical_reliability', 0)
        if historical_score >= 0.85:
            reasoning_parts.append(
                "Strategy has strong historical performance (>60% win rate)"
            )
        elif historical_score >= 0.70:
            reasoning_parts.append("Strategy shows consistent reliability")
        
        # 5. Volatility conditions
        volatility_score = breakdown.get('volatility_filter', 0)
        if volatility_score >= 0.85:
            reasoning_parts.append("Low volatility environment favors controlled risk")
        elif volatility_score < 0.60:
            reasoning_parts.append("Elevated volatility requires wider stops")
        
        # 6. Psychological factors
        psych_score = breakdown.get('psychological_safety', 0)
        if psych_score >= 0.85:
            reasoning_parts.append("Trading frequency within healthy limits")
        elif psych_score < 0.70:
            reasoning_parts.append("⚠️ Recent overtrading detected - consider reducing size")
        
        # Combine reasoning parts into coherent paragraph
        reasoning = ". ".join(reasoning_parts) + "."
        return reasoning
    
    def _build_suggestion(self, signal_data: Dict, truth_index: float,
                         status: str) -> str:
        """
        Build actionable suggestion with entry, targets, and risk management.
        
        Format:
        - Entry bias and level
        - Target considerations
        - Risk percentage
        - Additional cautions or confirmations
        """
        side = signal_data.get('side', 'buy').lower()
        price = float(signal_data.get('price', 0))
        sl = float(signal_data.get('sl', 0))
        tp = float(signal_data.get('tp', 0))
        
        # Calculate R:R ratio
        risk = abs(price - sl)
        reward = abs(tp - price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        # Calculate risk percentage (assuming standard position sizing)
        risk_pct = (risk / price) * 100 if price > 0 else 0
        
        suggestion_parts = []
        
        # 1. Entry guidance
        direction = "Long" if side == "buy" else "Short"
        entry_verb = "above" if side == "buy" else "below"
        
        if status == 'approved' and truth_index >= 80:
            suggestion_parts.append(
                f"✅ {direction} bias validated {entry_verb} {price:.5f}"
            )
        elif status == 'conditional':
            suggestion_parts.append(
                f"⚠️ {direction} bias conditional {entry_verb} {price:.5f} "
                f"(await confirmation)"
            )
        else:
            suggestion_parts.append(
                f"❌ Setup does not meet validation criteria"
            )
        
        # 2. Target strategy
        if rr_ratio >= 2.0:
            suggestion_parts.append(
                f"Consider scaling out: partials near {(price + (tp - price) * 0.5):.5f}, "
                f"final target {tp:.5f}"
            )
        elif rr_ratio >= 1.5:
            suggestion_parts.append(
                f"Target {tp:.5f} with {rr_ratio:.1f}:1 R:R"
            )
        else:
            suggestion_parts.append(
                f"⚠️ Suboptimal R:R ({rr_ratio:.1f}:1) - consider adjusting targets"
            )
        
        # 3. Risk management
        if risk_pct < 1.0:
            suggestion_parts.append(f"Risk < {risk_pct:.1f}% (conservative)")
        elif risk_pct < 2.0:
            suggestion_parts.append(f"Risk ~{risk_pct:.1f}% (standard)")
        else:
            suggestion_parts.append(
                f"⚠️ Risk {risk_pct:.1f}% (high) - reduce position size"
            )
        
        # 4. Additional context based on strategy
        strategy = signal_data.get('strategy', 'default').lower()
        if strategy == 'smc':
            suggestion_parts.append(
                "Watch for liquidity sweeps and order block reactions"
            )
        elif strategy == 'ict':
            suggestion_parts.append(
                "Monitor Kill Zone timing and institutional behavior"
            )
        elif strategy == 'elliott_wave':
            suggestion_parts.append(
                "Confirm wave structure before full commitment"
            )
        
        # 5. Validation-based cautions
        if truth_index < 75:
            suggestion_parts.append(
                "⚠️ Lower confidence - reduce size or skip if uncertain"
            )
        
        # Combine suggestion parts
        suggestion = ". ".join(suggestion_parts) + "."
        return suggestion
    
    def _get_current_session(self) -> Optional[str]:
        """
        Determine current trading session based on UTC time.
        
        Returns:
            'london', 'newyork', 'asia', 'overlap', or None
        """
        try:
            now = timezone.now()
            hour_utc = now.hour
            
            # Check for overlap first (13:00-16:00 UTC)
            if 13 <= hour_utc < 16:
                return 'overlap'
            
            # Check other sessions
            for session, times in self.SESSION_CONTEXT.items():
                if session == 'overlap':
                    continue
                if times['start'] <= hour_utc < times['end']:
                    return session
            
            return None
            
        except Exception as e:
            logger.warning(f"Error determining session: {e}")
            return None
    
    def _fallback_narrative(self, signal_data: Dict, 
                           validation_result: Dict) -> str:
        """
        Generate simplified narrative if main generation fails.
        """
        symbol = signal_data.get('symbol', 'UNKNOWN')
        side = signal_data.get('side', 'buy').upper()
        truth_index = validation_result.get('truth_index', 0)
        status = validation_result.get('status', 'unknown')
        
        if status == 'approved':
            return (f"📊 {symbol} {side} signal validated ({truth_index:.0f}/100). "
                   f"Review full details and proceed with standard risk management.")
        elif status == 'conditional':
            return (f"⚠️ {symbol} {side} signal conditional ({truth_index:.0f}/100). "
                   f"Await additional confirmation before entry.")
        else:
            return (f"❌ {symbol} {side} signal rejected ({truth_index:.0f}/100). "
                   f"Does not meet validation criteria.")
    
    def detect_market_bias(self, signal_data: Dict, validation_result: Dict) -> str:
        """
        Detect market bias from signal data and validation (NO TRADE DIRECTION).
        
        Args:
            signal_data: Raw signal data
            validation_result: Validation result with breakdown
            
        Returns:
            'bearish', 'neutral', or 'bullish' (market interpretation, NOT trade instruction)
        """
        try:
            side = signal_data.get('side', 'unknown').lower()
            truth_index = validation_result.get('truth_index', 50)
            
            # If low confidence, default to neutral
            if truth_index < 60:
                return 'neutral'
            
            # Map trade direction to market bias interpretation
            if side == 'buy':
                return 'bullish'
            elif side == 'sell':
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Error detecting market bias: {e}")
            return 'neutral'
    
    def detect_market_phase(self, signal_data: Dict, validation_result: Dict) -> str:
        """
        Detect market phase from signal characteristics.
        
        Phases:
        - accumulation: Low volatility, consolidation, building position
        - expansion: High momentum, trending, breakout
        - manipulation: Fake-out, stop hunt, liquidity grab
        - distribution: Top/bottom forming, reversal signals
        
        Args:
            signal_data: Raw signal data
            validation_result: Validation result
            
        Returns:
            Market phase string
        """
        try:
            regime = signal_data.get('regime', '').lower()
            confidence = validation_result.get('truth_index', 50)
            breakdown = validation_result.get('breakdown', {})
            volatility = breakdown.get('volatility_filter', 50)
            
            # Expansion phase: High confidence trending/breakout
            if regime in ['trend', 'breakout'] and confidence >= 75:
                return 'expansion'
            
            # Manipulation: Low confidence, potential trap
            elif confidence < 55 and volatility > 70:
                return 'manipulation'
            
            # Distribution: Mean reversion setups
            elif regime == 'meanreversion':
                return 'distribution'
            
            # Accumulation: Low volatility consolidation
            elif volatility < 40:
                return 'accumulation'
            
            # Default to expansion for trending markets
            else:
                return 'expansion'
                
        except Exception as e:
            logger.error(f"Error detecting market phase: {e}")
            return 'expansion'
    
    def generate_ai_narrative(self, signal_data: Dict, validation_result: Dict, 
                              bias: str, market_phase: str) -> str:
        """
        Generate AI-powered market interpretation narrative (NO TRADING INSTRUCTIONS).
        
        This replaces the old "signal approval" messaging with intelligent market analysis.
        Focus on WHY and context, not WHAT TO DO.
        
        Args:
            signal_data: Raw signal data
            validation_result: Validation result
            bias: Market bias (bearish/neutral/bullish)
            market_phase: Market phase (accumulation/expansion/manipulation/distribution)
            
        Returns:
            2-3 sentence narrative explaining market context
        """
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            timeframe = signal_data.get('timeframe', 'unknown')
            regime = signal_data.get('regime', 'unknown')
            session = signal_data.get('session', 'unknown')
            confidence = validation_result.get('truth_index', 50)
            breakdown = validation_result.get('breakdown', {})
            
            # Get key validation metrics
            technical = breakdown.get('technical_integrity', 50)
            volatility = breakdown.get('volatility_filter', 50)
            regime_align = breakdown.get('regime_alignment', 50)
            
            # Build narrative based on market phase
            narratives = {
                'expansion': self._narrative_expansion(symbol, regime, session, bias, confidence, technical),
                'manipulation': self._narrative_manipulation(symbol, regime, bias, volatility),
                'accumulation': self._narrative_accumulation(symbol, regime, session, volatility),
                'distribution': self._narrative_distribution(symbol, bias, technical, regime_align),
            }
            
            return narratives.get(market_phase, self._narrative_default(symbol, bias, confidence))
            
        except Exception as e:
            logger.error(f"Error generating AI narrative: {e}")
            return f"Market analysis for {signal_data.get('symbol', 'UNKNOWN')} - {bias} bias detected."
    
    def _narrative_expansion(self, symbol: str, regime: str, session: str, 
                             bias: str, confidence: float, technical: float) -> str:
        """Generate narrative for expansion phase"""
        direction = "upside" if bias == 'bullish' else "downside" if bias == 'bearish' else "price"
        
        if confidence >= 80:
            return (f"Price showing strong {direction} continuation within a {regime.lower()} regime during "
                   f"{session} session. Technical structure indicates high conviction ({technical:.0f}/100) "
                   f"with aligned market dynamics supporting further {bias} development.")
        elif confidence >= 65:
            return (f"Price displaying {direction} potential in {regime.lower()} regime. "
                   f"{session} session liquidity appears supportive. Technical alignment moderate "
                   f"({technical:.0f}/100) - confirmation on next timeframe close recommended.")
        else:
            return (f"Early {direction} signals emerging in {regime.lower()} environment during {session}. "
                   f"Technical conviction modest ({technical:.0f}/100) - observe for stronger confirmation "
                   f"before interpreting as high-probability setup.")
    
    def _narrative_manipulation(self, symbol: str, regime: str, bias: str, volatility: float) -> str:
        """Generate narrative for manipulation phase"""
        return (f"Price action showing potential liquidity manipulation in {regime.lower()} regime. "
               f"High volatility ({volatility:.0f}/100) with mixed structural signals suggests stop hunt "
               f"or false breakout risk. Recommend observing reaction to key levels before forming conviction "
               f"on {bias} bias sustainability.")
    
    def _narrative_accumulation(self, symbol: str, regime: str, session: str, volatility: float) -> str:
        """Generate narrative for accumulation phase"""
        return (f"Price consolidating within low-volatility {regime.lower()} range during {session} session. "
               f"Accumulation phase indicated by reduced volatility ({volatility:.0f}/100) and indecisive structure. "
               f"Typically precedes expansion - monitor for breakout confirmation on higher timeframe.")
    
    def _narrative_distribution(self, symbol: str, bias: str, technical: float, regime_align: float) -> str:
        """Generate narrative for distribution phase"""
        direction = "bearish" if bias == 'bearish' else "bullish" if bias == 'bullish' else "neutral"
        return (f"Price displaying potential distribution characteristics with {direction} undertones. "
               f"Mean reversion signals forming - technical structure ({technical:.0f}/100) and regime "
               f"alignment ({regime_align:.0f}/100) suggest exhaustion phase. Watch for reversal confirmation "
               f"or continuation failure signals.")
    
    def _narrative_default(self, symbol: str, bias: str, confidence: float) -> str:
        """Default narrative fallback"""
        return (f"Market analysis indicates {bias} bias for {symbol}. "
               f"AI conviction at {confidence:.0f}/100. Review full context and price action "
               f"for complete market picture before forming trading decisions.")
    
    def generate_follow_up_cue(self, signal_data: Dict, validation_result: Dict) -> str:
        """
        Generate optional follow-up observation suggestion (NO TRADE INSTRUCTION).
        
        Args:
            signal_data: Raw signal data
            validation_result: Validation result
            
        Returns:
            Suggestion for what to observe (e.g., "watch for liquidity retest near 185.30")
        """
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            price = signal_data.get('price')
            sl = signal_data.get('sl')
            tp = signal_data.get('tp')
            confidence = validation_result.get('truth_index', 50)
            
            if confidence >= 80:
                if tp:
                    return f"Observe reaction near {float(tp):.5f} zone for potential continuation signals."
                else:
                    return f"Monitor price action at current levels for structural development."
            
            elif confidence >= 65:
                if sl:
                    return f"Watch for liquidity interaction near {float(sl):.5f} - key structural zone."
                else:
                    return f"Observe next {signal_data.get('timeframe', 'H4')} close for directional confirmation."
            
            else:
                return f"Recommend awaiting stronger confirmation signals before forming high-conviction analysis."
                
        except Exception as e:
            logger.error(f"Error generating follow-up cue: {e}")
            return "Continue monitoring price action for structural clarity."
    
    def generate_batch_summary(self, signals: List[Dict]) -> str:
        """
        Generate summary narrative for multiple signals (e.g., daily recap).
        
        Args:
            signals: List of validated signals with narratives
        
        Returns:
            Summary paragraph highlighting key opportunities and patterns
        """
        try:
            if not signals:
                return "No validated signals for this period."
            
            total = len(signals)
            approved = len([s for s in signals if s.get('status') == 'approved'])
            conditional = len([s for s in signals if s.get('status') == 'conditional'])
            
            avg_truth = sum(s.get('truth_index', 0) for s in signals) / total
            
            # Find strongest signal
            strongest = max(signals, key=lambda s: s.get('truth_index', 0))
            strongest_symbol = strongest.get('symbol', 'UNKNOWN')
            strongest_score = strongest.get('truth_index', 0)
            
            summary = (
                f"📈 Daily Signal Summary: {total} signals analyzed. "
                f"{approved} approved, {conditional} conditional. "
                f"Average confidence: {avg_truth:.0f}/100. "
                f"Strongest setup: {strongest_symbol} ({strongest_score:.0f}/100)."
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating batch summary: {e}")
            return f"Summary generated for {len(signals)} signals."


# Global contextualizer instance
contextualizer = ContextualIntelligenceEngine()


def generate_narrative(signal_data: Dict, validation_result: Dict) -> str:
    """
    Convenience function to generate narrative for a signal.
    
    Usage:
        from zenbot.contextualizer import generate_narrative
        
        narrative = generate_narrative(
            signal_data={'symbol': 'EURUSD', 'side': 'buy', ...},
            validation_result={'truth_index': 83.5, 'status': 'approved', ...}
        )
    
    Args:
        signal_data: Raw signal data from webhook
        validation_result: Output from validation_engine.validate_signal()
    
    Returns:
        Human-readable narrative string
    """
    return contextualizer.generate_narrative(signal_data, validation_result)


def generate_batch_summary(signals: List[Dict]) -> str:
    """
    Convenience function to generate summary for multiple signals.
    
    Usage:
        from zenbot.contextualizer import generate_batch_summary
        
        summary = generate_batch_summary([
            {'symbol': 'EURUSD', 'truth_index': 85, 'status': 'approved'},
            {'symbol': 'GBPUSD', 'truth_index': 72, 'status': 'conditional'},
        ])
    
    Args:
        signals: List of validated signals
    
    Returns:
        Summary paragraph
    """
    return contextualizer.generate_batch_summary(signals)
