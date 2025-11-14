"""
Engine Scoring Module
=====================
Integrates ZenBot AI scoring with engine-generated signals.

This module:
1. Loads the ZenBot XGBoost model (or uses fallback rules)
2. Converts engine signal metadata to scoring features
3. Creates TradeScore entries linked to Signal objects
4. Provides scoring API for real-time and backtesting modes
"""

import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


def score_engine_signal(signal_obj, strategy_metadata: Dict) -> Tuple[int, Dict]:
    """
    Score an engine-generated signal using ZenBot AI.
    
    Args:
        signal_obj: Signal model instance (from signals.models.Signal)
        strategy_metadata: Dict from strategy detector containing:
            - confidence: float (0-100)
            - strategy: str (strategy name)
            - regime: str (market condition)
            - entry_reason: str (explanation)
            - structure_tags: list (e.g., ['BOS', 'OB_retest'])
            - extra: dict (additional metadata)
    
    Returns:
        Tuple of (ai_score, breakdown_dict)
    """
    try:
        from bot.ai_score import predict_score
        
        # The predict_score function already handles Signal objects
        # and automatically applies cognition + prop mode adjustments
        ai_score, breakdown = predict_score(
            signal_obj,
            apply_cognition=True,
            apply_prop_mode=True
        )
        
        # Add engine-specific metadata to breakdown
        breakdown['engine_metadata'] = {
            'strategy': strategy_metadata.get('strategy', 'Unknown'),
            'confidence': strategy_metadata.get('confidence', 50),
            'regime': strategy_metadata.get('regime', 'Unknown'),
            'entry_reason': strategy_metadata.get('entry_reason', ''),
            'structure_tags': strategy_metadata.get('structure_tags', []),
        }
        
        logger.info(f"Scored signal {signal_obj.id}: {ai_score}/100 "
                   f"(strategy: {strategy_metadata.get('strategy')})")
        
        return ai_score, breakdown
        
    except ImportError as e:
        logger.error(f"Could not import bot.ai_score: {e}")
        # Fallback to engine-only scoring
        return fallback_engine_score(strategy_metadata)
    except Exception as e:
        logger.error(f"Error scoring signal {signal_obj.id}: {e}", exc_info=True)
        # Return conservative fallback
        return fallback_engine_score(strategy_metadata)


def fallback_engine_score(metadata: Dict) -> Tuple[int, Dict]:
    """
    Fallback scoring when ZenBot is unavailable.
    Uses only engine strategy metadata.
    
    Args:
        metadata: Strategy metadata dict
        
    Returns:
        Tuple of (score, breakdown)
    """
    score = 50  # Start neutral
    breakdown = {'model_type': 'engine_fallback'}
    
    # Confidence factor (weight: 40%)
    confidence = float(metadata.get('confidence', 50))
    conf_contribution = (confidence - 50) * 0.8
    score += conf_contribution
    breakdown['confidence_contribution'] = round(conf_contribution, 1)
    
    # Regime factor (weight: 20%)
    regime = metadata.get('regime', 'Unknown')
    regime_scores = {
        'Trending': 15,
        'Ranging': 5,
        'Volatile': -5,
        'Bullish': 10,
        'Bearish': 10,
        'Choppy': -10,
    }
    regime_contribution = regime_scores.get(regime, 0)
    score += regime_contribution
    breakdown['regime_contribution'] = regime_contribution
    
    # Structure tags (weight: 20%)
    structure_tags = metadata.get('structure_tags', [])
    high_value_tags = ['BOS', 'CHoCH', 'OB_retest', 'FVG_fill', 'liquidity_sweep']
    structure_bonus = sum(5 for tag in structure_tags if tag in high_value_tags)
    structure_bonus = min(structure_bonus, 20)  # Cap at 20
    score += structure_bonus
    breakdown['structure_bonus'] = structure_bonus
    breakdown['structure_tags'] = structure_tags
    
    # Strategy type adjustment (weight: 10%)
    strategy = metadata.get('strategy', '')
    high_reliability_strategies = ['SMC', 'MultiTimeframe', 'SupplyDemand']
    if strategy in high_reliability_strategies:
        score += 10
        breakdown['strategy_bonus'] = 10
    else:
        breakdown['strategy_bonus'] = 0
    
    # Risk/Reward check (weight: 10%)
    extra = metadata.get('extra', {})
    rr_ratio = extra.get('risk_reward_ratio', 1.5)
    if rr_ratio >= 2.5:
        rr_bonus = 10
    elif rr_ratio >= 2.0:
        rr_bonus = 7
    elif rr_ratio >= 1.5:
        rr_bonus = 3
    else:
        rr_bonus = -5
    score += rr_bonus
    breakdown['risk_reward_bonus'] = rr_bonus
    breakdown['risk_reward_ratio'] = rr_ratio
    
    # Clamp to 0-100
    final_score = max(0, min(100, int(score)))
    
    breakdown['final_score'] = final_score
    breakdown['strategy'] = strategy
    breakdown['regime'] = regime
    
    logger.warning(f"Using fallback scoring: {final_score}/100 for {strategy}")
    
    return final_score, breakdown


def create_trade_score_entry(signal_obj, ai_score: int, breakdown: Dict) -> Optional[object]:
    """
    Create a TradeScore entry in the database.
    
    Args:
        signal_obj: Signal instance
        ai_score: AI score (0-100)
        breakdown: Scoring breakdown dict
        
    Returns:
        TradeScore instance or None if creation failed
    """
    try:
        from bot.models import TradeScore
        
        # Extract key metrics from breakdown
        confidence = breakdown.get('confidence', 50)
        if isinstance(confidence, str):
            # Handle string format like "+20 (base: 75%)"
            try:
                confidence = float(confidence.split('base:')[1].split('%')[0].strip())
            except:
                confidence = 50
        
        rr_ratio = breakdown.get('risk_reward_ratio', 1.5)
        if not isinstance(rr_ratio, (int, float)):
            rr_ratio = 1.5
        
        # Create TradeScore entry
        trade_score = TradeScore.objects.create(
            signal=signal_obj,
            ai_score=ai_score,
            confidence_score=round(confidence, 2),
            risk_reward_ratio=round(rr_ratio, 2),
            strategy_win_rate=round(breakdown.get('strategy_win_rate', 50), 2),
            user_win_rate=round(breakdown.get('user_win_rate', 50), 2),
            is_major_pair=breakdown.get('is_major_pair', False),
            in_peak_hours=breakdown.get('in_peak_hours', False),
            model_version=breakdown.get('version', 'v1.0'),
            raw_features=breakdown
        )
        
        logger.info(f"Created TradeScore entry for signal {signal_obj.id}: {ai_score}/100")
        
        return trade_score
        
    except ImportError as e:
        logger.error(f"Could not import TradeScore model: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create TradeScore entry: {e}", exc_info=True)
        return None


def score_and_save(signal_obj, strategy_metadata: Dict) -> Tuple[int, Optional[object]]:
    """
    Score a signal and save the TradeScore entry (convenience function).
    
    Args:
        signal_obj: Signal instance
        strategy_metadata: Dict from strategy detector
        
    Returns:
        Tuple of (ai_score, trade_score_obj)
    """
    # Get score
    ai_score, breakdown = score_engine_signal(signal_obj, strategy_metadata)
    
    # Save to database
    trade_score = create_trade_score_entry(signal_obj, ai_score, breakdown)
    
    return ai_score, trade_score


def score_backtest_signal(
    symbol: str,
    side: str,
    price: float,
    sl: float,
    tp: float,
    strategy_metadata: Dict,
    historical_data: Dict = None
) -> Tuple[int, Dict]:
    """
    Score a signal during backtesting (no database access).
    
    This is a stateless version that doesn't require Signal objects.
    Used for fast backtesting without creating database entries.
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        side: 'BUY' or 'SELL'
        price: Entry price
        sl: Stop loss price
        tp: Take profit price
        strategy_metadata: Dict from strategy detector
        historical_data: Optional dict with user/strategy historical performance
        
    Returns:
        Tuple of (ai_score, breakdown)
    """
    # Build synthetic features dict
    features = {}
    
    # 1. Strategy confidence
    features['confidence'] = float(strategy_metadata.get('confidence', 50))
    
    # 2. Stop loss distance
    sl_distance = abs(price - sl)
    features['sl_distance_pct'] = (sl_distance / price) * 100
    
    # 3. Take profit distance
    tp_distance = abs(tp - price)
    features['tp_distance_pct'] = (tp_distance / price) * 100
    
    # 4. Risk/Reward ratio
    if sl_distance > 0:
        features['risk_reward_ratio'] = tp_distance / sl_distance
    else:
        features['risk_reward_ratio'] = 2.0
    
    # 5. Strategy encoding
    strategy_map = {
        'SMC': 10,
        'ICT': 9,
        'MultiTimeframe': 8,
        'SupplyDemand': 7,
        'Trend': 6,
        'Breakout': 5,
        'VWAP': 4,
        'MeanReversion': 3,
        'Squeeze': 2,
        'Scalping': 1,
    }
    strategy_name = strategy_metadata.get('strategy', 'Unknown')
    features['strategy_encoded'] = strategy_map.get(strategy_name, 0)
    
    # 6. Regime encoding
    regime_map = {
        'Bullish': 3,
        'Trending': 3,
        'Ranging': 2,
        'Bearish': 1,
        'Volatile': 1,
        'Choppy': 0,
    }
    features['regime_encoded'] = regime_map.get(
        strategy_metadata.get('regime', 'Unknown'), 2
    )
    
    # 7. Side encoding
    features['is_buy'] = 1 if side == 'BUY' else 0
    
    # 8. Major pair check
    major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
    features['is_major_pair'] = 1 if symbol in major_pairs else 0
    
    # 9-10. Historical performance (use provided or defaults)
    if historical_data:
        features['strategy_win_rate'] = historical_data.get('strategy_win_rate', 50.0)
        features['user_win_rate'] = historical_data.get('user_win_rate', 50.0)
    else:
        # Use baseline from strategy metadata or neutral
        features['strategy_win_rate'] = 50.0
        features['user_win_rate'] = 50.0
    
    # 11. Peak hours (assume yes for backtesting)
    features['in_peak_hours'] = 1
    
    # 12. Recent activity (assume active for backtesting)
    features['recent_activity'] = 75.0
    
    # Calculate score using rule-based method (fast for backtesting)
    score = 50  # Start neutral
    breakdown = {'model_type': 'backtest_rules'}
    
    # Confidence (20%)
    conf_contrib = (features['confidence'] - 50) * 0.4
    score += conf_contrib
    breakdown['confidence'] = features['confidence']
    
    # Risk/Reward (15%)
    rr = features['risk_reward_ratio']
    if rr >= 2.5:
        rr_contrib = 15
    elif rr >= 2.0:
        rr_contrib = 10
    elif rr >= 1.5:
        rr_contrib = 5
    else:
        rr_contrib = -5
    score += rr_contrib
    breakdown['risk_reward_ratio'] = round(rr, 2)
    breakdown['rr_contribution'] = rr_contrib
    
    # Strategy win rate (25%)
    wr_contrib = (features['strategy_win_rate'] - 50) * 0.5
    score += wr_contrib
    breakdown['strategy_win_rate'] = features['strategy_win_rate']
    
    # Structure tags bonus (15%)
    structure_tags = strategy_metadata.get('structure_tags', [])
    high_value_tags = ['BOS', 'CHoCH', 'OB_retest', 'FVG_fill']
    structure_bonus = sum(5 for tag in structure_tags if tag in high_value_tags)
    structure_bonus = min(structure_bonus, 15)
    score += structure_bonus
    breakdown['structure_bonus'] = structure_bonus
    
    # Major pair bonus (10%)
    if features['is_major_pair']:
        score += 10
        breakdown['major_pair_bonus'] = 10
    else:
        breakdown['major_pair_bonus'] = 0
    
    # Peak hours bonus (5%)
    if features['in_peak_hours']:
        score += 5
        breakdown['peak_hours_bonus'] = 5
    else:
        breakdown['peak_hours_bonus'] = 0
    
    # Strategy reliability (10%)
    if strategy_name in ['SMC', 'MultiTimeframe', 'SupplyDemand']:
        score += 10
        breakdown['strategy_reliability_bonus'] = 10
    elif strategy_name in ['Trend', 'Breakout', 'ICT']:
        score += 5
        breakdown['strategy_reliability_bonus'] = 5
    else:
        breakdown['strategy_reliability_bonus'] = 0
    
    # Clamp to 0-100
    final_score = max(0, min(100, int(score)))
    
    breakdown['final_score'] = final_score
    breakdown['strategy'] = strategy_name
    breakdown['regime'] = strategy_metadata.get('regime', 'Unknown')
    breakdown['entry_reason'] = strategy_metadata.get('entry_reason', '')
    breakdown['structure_tags'] = structure_tags
    
    return final_score, breakdown


def bulk_score_signals(signals_with_metadata: list) -> list:
    """
    Score multiple signals in batch (for efficiency).
    
    Args:
        signals_with_metadata: List of tuples (signal_obj, strategy_metadata)
        
    Returns:
        List of tuples (signal_obj, ai_score, breakdown, trade_score_obj)
    """
    results = []
    
    for signal_obj, metadata in signals_with_metadata:
        try:
            ai_score, breakdown = score_engine_signal(signal_obj, metadata)
            trade_score = create_trade_score_entry(signal_obj, ai_score, breakdown)
            results.append((signal_obj, ai_score, breakdown, trade_score))
            
        except Exception as e:
            logger.error(f"Failed to score signal {signal_obj.id}: {e}")
            # Add failure entry
            results.append((signal_obj, 0, {'error': str(e)}, None))
    
    logger.info(f"Bulk scored {len(results)} signals")
    
    return results


def explain_score(ai_score: int, breakdown: Dict) -> str:
    """
    Generate human-readable explanation of score.
    
    This is a wrapper around bot.ai_score.explain_score with engine enhancements.
    
    Args:
        ai_score: AI score (0-100)
        breakdown: Scoring breakdown dict
        
    Returns:
        Formatted explanation string
    """
    try:
        from bot.ai_score import explain_score as bot_explain_score
        
        # Use ZenBot's explanation function
        explanation = bot_explain_score(ai_score, breakdown)
        
        # Add engine-specific details if present
        engine_metadata = breakdown.get('engine_metadata', {})
        if engine_metadata:
            explanation += "\n\n**Engine Detection:**\n"
            explanation += f"• Strategy: {engine_metadata.get('strategy', 'Unknown')}\n"
            explanation += f"• Regime: {engine_metadata.get('regime', 'Unknown')}\n"
            
            entry_reason = engine_metadata.get('entry_reason', '')
            if entry_reason:
                explanation += f"• Entry: {entry_reason}\n"
            
            structure_tags = engine_metadata.get('structure_tags', [])
            if structure_tags:
                explanation += f"• Structure: {', '.join(structure_tags)}\n"
        
        return explanation
        
    except ImportError:
        # Fallback if bot.ai_score not available
        explanation = f"**Score: {ai_score}/100**\n\n"
        
        if ai_score >= 80:
            explanation += "✅ High Confidence Signal\n"
        elif ai_score >= 60:
            explanation += "🟡 Moderate Confidence\n"
        else:
            explanation += "⚠️ Low Confidence - Caution\n"
        
        explanation += f"\n**Strategy:** {breakdown.get('strategy', 'Unknown')}\n"
        explanation += f"**Regime:** {breakdown.get('regime', 'Unknown')}\n"
        explanation += f"**Confidence:** {breakdown.get('confidence', 50):.0f}%\n"
        explanation += f"**Risk:Reward:** {breakdown.get('risk_reward_ratio', 1.5):.2f}:1\n"
        
        structure_tags = breakdown.get('structure_tags', [])
        if structure_tags:
            explanation += f"**Structure:** {', '.join(structure_tags)}\n"
        
        return explanation


# Convenience function for quick testing
def test_scoring():
    """Test the scoring module with synthetic data."""
    print("🧪 Testing Engine Scoring Module\n")
    
    # Test backtest scoring (no database)
    print("1. Backtest Scoring (stateless):")
    score, breakdown = score_backtest_signal(
        symbol='EURUSD',
        side='BUY',
        price=1.1000,
        sl=1.0950,
        tp=1.1100,
        strategy_metadata={
            'confidence': 78,
            'strategy': 'SMC',
            'regime': 'Trending',
            'entry_reason': 'BOS + OB retest in discount',
            'structure_tags': ['BOS', 'OB_retest', 'discount_zone'],
            'extra': {'risk_reward_ratio': 2.0}
        }
    )
    print(f"   Score: {score}/100")
    print(f"   Breakdown: {breakdown}\n")
    
    # Test explanation
    print("2. Score Explanation:")
    explanation = explain_score(score, breakdown)
    print(f"   {explanation}\n")
    
    print("✅ Scoring module test complete!")


if __name__ == '__main__':
    test_scoring()
