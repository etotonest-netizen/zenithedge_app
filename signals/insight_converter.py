"""
Signal to MarketInsight Conversion Utility

Helper functions to transform legacy Signal objects into MarketInsight objects
during the migration period. This allows both models to coexist while we
transition from "signal vendor" to "AI Decision Intelligence Console".

Usage:
    from signals.insight_converter import convert_signal_to_insight
    
    insight = convert_signal_to_insight(signal, validation_result)
"""

import logging
from typing import Dict, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


def convert_signal_to_insight(signal, validation_result: Optional[Dict] = None):
    """
    Convert a Signal object to a MarketInsight object.
    
    Args:
        signal: Signal model instance
        validation_result: Optional validation result dict with truth_index, breakdown, etc.
        
    Returns:
        MarketInsight instance (unsaved)
    """
    from signals.models import MarketInsight
    from zenbot.contextualizer import contextualizer
    
    try:
        # Prepare signal data for contextualizer
        signal_data = {
            'symbol': signal.symbol,
            'timeframe': signal.timeframe,
            'side': signal.side,
            'sl': signal.sl,
            'tp': signal.tp,
            'confidence': signal.confidence,
            'strategy': signal.strategy,
            'regime': signal.regime,
            'session': signal.session,
            'price': signal.price,
            'timestamp': signal.timestamp,
        }
        
        # Use validation result or create default
        if not validation_result:
            validation_result = {
                'truth_index': signal.confidence,
                'status': 'approved' if signal.is_allowed else 'rejected',
                'breakdown': {
                    'technical_integrity': signal.confidence,
                    'volatility_filter': 70.0,
                    'regime_alignment': signal.confidence,
                    'sentiment_coherence': 70.0,
                    'historical_reliability': 70.0,
                    'psychological_safety': 70.0,
                }
            }
        
        # Detect intelligence fields using contextualizer
        bias = contextualizer.detect_market_bias(signal_data, validation_result)
        market_phase = contextualizer.detect_market_phase(signal_data, validation_result)
        narrative = contextualizer.generate_ai_narrative(
            signal_data, validation_result, bias, market_phase
        )
        follow_up_cue = contextualizer.generate_follow_up_cue(signal_data, validation_result)
        
        # Get insight index (AI reasoning quality score)
        truth_index = validation_result.get('truth_index', signal.confidence)
        
        # Create MarketInsight instance (unsaved)
        insight = MarketInsight(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            regime=signal.regime,
            session=signal.session or MarketInsight.detect_session(signal.received_at),
            
            # NEW: Intelligence fields
            bias=bias,
            narrative=narrative,
            market_phase=market_phase,
            insight_index=truth_index,
            confidence_score=signal.confidence,
            follow_up_cue=follow_up_cue,
            
            # Context fields
            strategy=signal.strategy,
            observation_price=signal.price,
            
            # Legacy compatibility (deprecated)
            legacy_side=signal.side,
            legacy_sl=signal.sl,
            legacy_tp=signal.tp,
            
            # Metadata
            timestamp=signal.timestamp,
            received_at=signal.received_at,
            user=signal.user,
            
            # Quality
            is_high_quality=(truth_index >= 70),
            quality_notes='',
            
            # Link to original signal
            original_signal=signal,
        )
        
        return insight
        
    except Exception as e:
        logger.error(f"Error converting signal to insight: {e}")
        raise


def bulk_convert_signals_to_insights(signals, validation_results: Optional[Dict] = None):
    """
    Convert multiple Signal objects to MarketInsight objects.
    
    Args:
        signals: QuerySet or list of Signal instances
        validation_results: Optional dict mapping signal.id -> validation_result
        
    Returns:
        List of MarketInsight instances (unsaved)
    """
    insights = []
    
    for signal in signals:
        try:
            validation_result = None
            if validation_results:
                validation_result = validation_results.get(signal.id)
            
            insight = convert_signal_to_insight(signal, validation_result)
            insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error converting signal {signal.id}: {e}")
            continue
    
    return insights


def create_insight_from_webhook(webhook_data: Dict, validation_result: Dict):
    """
    Create MarketInsight directly from webhook data (bypassing Signal model).
    
    This is the NEW flow for future webhooks - create MarketInsight directly
    instead of creating Signal first.
    
    Args:
        webhook_data: Raw webhook payload
        validation_result: Validation result from validation_engine
        
    Returns:
        MarketInsight instance (unsaved)
    """
    from signals.models import MarketInsight
    from zenbot.contextualizer import contextualizer
    
    try:
        # Detect intelligence fields
        bias = contextualizer.detect_market_bias(webhook_data, validation_result)
        market_phase = contextualizer.detect_market_phase(webhook_data, validation_result)
        narrative = contextualizer.generate_ai_narrative(
            webhook_data, validation_result, bias, market_phase
        )
        follow_up_cue = contextualizer.generate_follow_up_cue(webhook_data, validation_result)
        
        # Extract data
        truth_index = validation_result.get('truth_index', 50)
        
        insight = MarketInsight(
            symbol=webhook_data.get('symbol'),
            timeframe=webhook_data.get('timeframe'),
            regime=webhook_data.get('regime'),
            session=webhook_data.get('session'),
            
            # Intelligence fields
            bias=bias,
            narrative=narrative,
            market_phase=market_phase,
            insight_index=truth_index,
            confidence_score=webhook_data.get('confidence', 50),
            follow_up_cue=follow_up_cue,
            
            # Context
            strategy=webhook_data.get('strategy'),
            observation_price=webhook_data.get('price'),
            
            # Legacy (for transition period)
            legacy_side=webhook_data.get('side'),
            legacy_sl=webhook_data.get('sl'),
            legacy_tp=webhook_data.get('tp'),
            
            # Metadata
            timestamp=webhook_data.get('timestamp'),
            
            # Quality
            is_high_quality=(truth_index >= 70),
        )
        
        return insight
        
    except Exception as e:
        logger.error(f"Error creating insight from webhook: {e}")
        raise
