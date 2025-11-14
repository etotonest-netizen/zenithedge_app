"""
ZenBot In-House AI Trade Score Engine
No external ML dependencies - pure logic-based scoring with explainability.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
import random
import logging

logger = logging.getLogger('zenbot')


# =============================================================================
# Lookup Tables for Strategy & Regime Fit
# =============================================================================

# Strategy-specific weight adjustments (multipliers for base weights)
STRATEGY_WEIGHT_ADJUSTMENTS = {
    'Trend': {
        'signal_confidence': 1.1,  # Trend strategies trust high confidence more
        'regime_fit': 1.3,  # Regime alignment is critical
        'rolling_win_rate': 1.0,
        'atr_safety': 0.9,
        'strategy_bias': 1.0,
    },
    'Breakout': {
        'signal_confidence': 1.2,  # Breakouts need strong signals
        'regime_fit': 1.1,
        'rolling_win_rate': 0.9,
        'atr_safety': 1.1,  # Volatility is friend of breakouts
        'strategy_bias': 1.0,
    },
    'MeanReversion': {
        'signal_confidence': 0.9,  # Mean reversion can work with lower confidence
        'regime_fit': 1.2,  # Must be in ranging regime
        'rolling_win_rate': 1.1,  # Historical performance matters more
        'atr_safety': 1.0,
        'strategy_bias': 1.0,
    },
    'Squeeze': {
        'signal_confidence': 1.0,
        'regime_fit': 1.2,
        'rolling_win_rate': 1.0,
        'atr_safety': 1.1,
        'strategy_bias': 1.0,
    },
}

STRATEGY_BIAS = {
    'Trend': 0.70,
    'Trend Following': 0.70,
    'Breakout': 0.65,
    'MeanReversion': 0.55,
    'Mean Reversion': 0.55,
    'Range Trading': 0.55,
    'Squeeze': 0.50,
    'Default': 0.50
}

# Matrix: REGIME_FIT[strategy][regime] -> 0..1 score
REGIME_FIT = {
    'Trend': {
        'Trend': 0.95,
        'Trending': 0.95,
        'Bullish': 0.90,
        'Bearish': 0.90,
        'Breakout': 0.70,
        'MeanReversion': 0.30,
        'Ranging': 0.30,
        'Squeeze': 0.40,
        'Neutral': 0.50
    },
    'Trend Following': {
        'Trend': 0.95,
        'Trending': 0.95,
        'Bullish': 0.90,
        'Bearish': 0.90,
        'Breakout': 0.70,
        'MeanReversion': 0.30,
        'Ranging': 0.30,
        'Squeeze': 0.40,
        'Neutral': 0.50
    },
    'Breakout': {
        'Breakout': 0.95,
        'Trend': 0.75,
        'Trending': 0.75,
        'Bullish': 0.70,
        'Bearish': 0.70,
        'Squeeze': 0.80,
        'Ranging': 0.40,
        'MeanReversion': 0.35,
        'Neutral': 0.50
    },
    'MeanReversion': {
        'MeanReversion': 0.90,
        'Ranging': 0.90,
        'Neutral': 0.75,
        'Squeeze': 0.60,
        'Trend': 0.25,
        'Trending': 0.25,
        'Bullish': 0.30,
        'Bearish': 0.30,
        'Breakout': 0.35
    },
    'Mean Reversion': {
        'MeanReversion': 0.90,
        'Ranging': 0.90,
        'Neutral': 0.75,
        'Squeeze': 0.60,
        'Trend': 0.25,
        'Trending': 0.25,
        'Bullish': 0.30,
        'Bearish': 0.30,
        'Breakout': 0.35
    },
    'Range Trading': {
        'Ranging': 0.90,
        'MeanReversion': 0.85,
        'Neutral': 0.70,
        'Squeeze': 0.55,
        'Trend': 0.30,
        'Trending': 0.30,
        'Bullish': 0.35,
        'Bearish': 0.35,
        'Breakout': 0.40
    },
    'Squeeze': {
        'Squeeze': 0.95,
        'Ranging': 0.70,
        'Breakout': 0.75,
        'Neutral': 0.65,
        'MeanReversion': 0.50,
        'Trend': 0.45,
        'Trending': 0.45,
        'Bullish': 0.40,
        'Bearish': 0.40
    }
}

# Session preferences (some strategies work better in certain sessions)
SESSION_PREFERENCE = {
    'Trend': {'Asia': 0.5, 'London': 0.85, 'New York': 0.90},
    'Trend Following': {'Asia': 0.5, 'London': 0.85, 'New York': 0.90},
    'Breakout': {'Asia': 0.4, 'London': 0.95, 'New York': 0.95},
    'MeanReversion': {'Asia': 0.75, 'London': 0.65, 'New York': 0.60},
    'Mean Reversion': {'Asia': 0.75, 'London': 0.65, 'New York': 0.60},
    'Range Trading': {'Asia': 0.80, 'London': 0.60, 'New York': 0.55},
    'Squeeze': {'Asia': 0.60, 'London': 0.70, 'New York': 0.70}
}


# =============================================================================
# TradeScorer Class
# =============================================================================

class TradeScorer:
    """
    In-house AI scoring engine for trading signals.
    Uses weighted factors with explainable logic - no black box ML.
    """
    
    def __init__(self, weights=None, strategy=None):
        """
        Initialize scorer with weight configuration.
        
        Args:
            weights: dict with keys: signal_confidence, atr_safety, strategy_bias,
                     regime_fit, rolling_win_rate (values should sum to ~1.0)
            strategy: Strategy name for strategy-specific weight adjustments
        """
        if weights is None:
            # Default weights (balanced)
            self.weights = {
                'signal_confidence': 0.32,
                'atr_safety': 0.18,
                'strategy_bias': 0.16,
                'regime_fit': 0.18,
                'rolling_win_rate': 0.16
            }
        else:
            self.weights = weights.copy()
        
        # Apply strategy-specific adjustments if provided
        self.strategy = strategy
        if strategy and strategy in STRATEGY_WEIGHT_ADJUSTMENTS:
            adjustments = STRATEGY_WEIGHT_ADJUSTMENTS[strategy]
            for key in self.weights:
                if key in adjustments:
                    self.weights[key] *= adjustments[key]
            
            # Re-normalize to sum to 1.0
            total = sum(self.weights.values())
            if total > 0:
                self.weights = {k: v/total for k, v in self.weights.items()}
            
            logger.info(f"Applied {strategy} weight adjustments")
    
    def extract_features(self, signal):
        """
        Extract raw features from signal object.
        
        Returns:
            dict with feature values ready for factorization
        """
        features = {}
        
        # 1. Signal confidence (from Pine script, 0-100)
        features['signal_confidence'] = float(signal.confidence or 0)
        
        # 2. ATR safety (computed from SL distance vs price)
        sl_distance = abs(float(signal.price or 0) - float(signal.sl or 0))
        price = float(signal.price or 1)  # avoid division by zero
        sl_pct = (sl_distance / price) * 100 if price > 0 else 0
        
        # Lower SL % = tighter stop = higher risk but also higher precision
        # We consider 0.5-1.5% as "safe", <0.3% as "too tight", >3% as "too wide"
        features['sl_pct'] = sl_pct
        
        # Compute ATR percentile (mock calculation - in production, use real ATR)
        # For now, use SL distance as proxy
        if sl_pct < 0.3:
            features['atr_percentile'] = 0.9  # Too tight
        elif sl_pct < 0.8:
            features['atr_percentile'] = 0.3  # Good tight stop
        elif sl_pct < 2.0:
            features['atr_percentile'] = 0.5  # Moderate
        else:
            features['atr_percentile'] = 0.8  # Wide stop
        
        # 3. Strategy type
        features['strategy_type'] = signal.strategy or 'Default'
        
        # 4. Regime type
        features['regime_type'] = signal.regime or 'Neutral'
        
        # 5. Session type
        features['session_type'] = signal.session or 'London'  # Default to London
        
        # 6. Symbol (for rolling win rate lookup)
        features['symbol'] = signal.symbol
        
        # 7. Timeframe
        features['timeframe'] = signal.timeframe
        
        return features
    
    def factorize(self, features, signal=None):
        """
        Transform raw features into normalized factors (0..1).
        
        Returns:
            dict with normalized factor scores
        """
        factors = {}
        
        # 1. Confidence factor (normalize 0-100 to 0-1)
        conf_raw = features.get('signal_confidence', 50)
        factors['conf_norm'] = min(max(conf_raw / 100.0, 0), 1)
        
        # 2. ATR safety factor (inverse of ATR percentile)
        atr_pct = features.get('atr_percentile', 0.5)
        factors['atr_safety'] = 1.0 - atr_pct
        
        # 3. Strategy bias (from lookup table)
        strategy = features.get('strategy_type', 'Default')
        factors['strategy_bias'] = STRATEGY_BIAS.get(strategy, STRATEGY_BIAS['Default'])
        
        # 4. Regime fit (from matrix)
        regime = features.get('regime_type', 'Neutral')
        strategy_matrix = REGIME_FIT.get(strategy, REGIME_FIT.get('Default', {}))
        if isinstance(strategy_matrix, dict):
            factors['regime_fit'] = strategy_matrix.get(regime, 0.5)
        else:
            factors['regime_fit'] = 0.5
        
        # 5. Session fit (optional bonus/penalty)
        session = features.get('session_type', 'London')
        session_matrix = SESSION_PREFERENCE.get(strategy, {})
        factors['session_fit'] = session_matrix.get(session, 0.7)
        
        # 6. Rolling win rate (from recent history)
        if signal:
            factors['rolling_win_rate'] = self._compute_rolling_win_rate(
                signal=signal,
                strategy=strategy,
                symbol=features.get('symbol'),
                timeframe=features.get('timeframe')
            )
        else:
            factors['rolling_win_rate'] = 0.5  # Neutral default
        
        return factors
    
    def _compute_rolling_win_rate(self, signal, strategy, symbol, timeframe, window_days=30):
        """
        Compute rolling win rate for similar signals from journal/backtest data.
        
        Returns:
            float 0..1 representing win rate
        """
        try:
            from signals.models import Signal
            from django.db.models import Q
            
            # Look back N days
            cutoff = timezone.now() - timedelta(days=window_days)
            
            # Find similar signals (same user, strategy, symbol, timeframe)
            similar = Signal.objects.filter(
                user=signal.user,
                strategy=strategy,
                symbol=symbol,
                received_at__gte=cutoff
            ).exclude(outcome='pending')
            
            total_count = similar.count()
            if total_count == 0:
                # No history - return neutral
                return 0.5
            
            green_count = similar.filter(outcome='green').count()
            win_rate = green_count / total_count
            
            return win_rate
            
        except Exception as e:
            # Fallback to neutral if error
            return 0.5
    
    def score_signal(self, signal):
        """
        Compute final AI score (0-100) and detailed breakdown.
        
        Args:
            signal: Signal model instance
        
        Returns:
            tuple: (int_score, breakdown_list)
                int_score: 0-100 integer score
                breakdown_list: list of dicts with factor details
        """
        # Extract features
        features = self.extract_features(signal)
        
        # Factorize to normalized scores
        factors = self.factorize(features, signal=signal)
        
        # Compute weighted sum
        breakdown = []
        total_score = 0.0
        
        # Factor 1: Signal Confidence
        conf_weight = self.weights.get('signal_confidence', 0.32)
        conf_contribution = factors['conf_norm'] * conf_weight
        total_score += conf_contribution
        breakdown.append({
            'factor': 'Signal Confidence',
            'raw_value': f"{features['signal_confidence']:.0f}/100",
            'normalized': factors['conf_norm'],
            'weight': conf_weight,
            'contribution': conf_contribution,
            'explanation': f"Pine script confidence level"
        })
        
        # Factor 2: ATR Safety
        atr_weight = self.weights.get('atr_safety', 0.18)
        atr_contribution = factors['atr_safety'] * atr_weight
        total_score += atr_contribution
        breakdown.append({
            'factor': 'ATR Safety',
            'raw_value': f"{features['sl_pct']:.2f}% SL distance",
            'normalized': factors['atr_safety'],
            'weight': atr_weight,
            'contribution': atr_contribution,
            'explanation': f"Stop loss positioning vs volatility"
        })
        
        # Factor 3: Strategy Bias
        strat_weight = self.weights.get('strategy_bias', 0.16)
        strat_contribution = factors['strategy_bias'] * strat_weight
        total_score += strat_contribution
        breakdown.append({
            'factor': 'Strategy Bias',
            'raw_value': features['strategy_type'],
            'normalized': factors['strategy_bias'],
            'weight': strat_weight,
            'contribution': strat_contribution,
            'explanation': f"Historical {features['strategy_type']} performance"
        })
        
        # Factor 4: Regime Fit
        regime_weight = self.weights.get('regime_fit', 0.18)
        regime_contribution = factors['regime_fit'] * regime_weight
        total_score += regime_contribution
        breakdown.append({
            'factor': 'Regime Fit',
            'raw_value': f"{features['strategy_type']} × {features['regime_type']}",
            'normalized': factors['regime_fit'],
            'weight': regime_weight,
            'contribution': regime_contribution,
            'explanation': f"Strategy alignment with market regime"
        })
        
        # Factor 5: Rolling Win Rate
        wr_weight = self.weights.get('rolling_win_rate', 0.16)
        wr_contribution = factors['rolling_win_rate'] * wr_weight
        total_score += wr_contribution
        breakdown.append({
            'factor': 'Rolling Win Rate',
            'raw_value': f"{factors['rolling_win_rate']*100:.0f}%",
            'normalized': factors['rolling_win_rate'],
            'weight': wr_weight,
            'contribution': wr_contribution,
            'explanation': f"Recent {features['strategy_type']} success on {features['symbol']}"
        })
        
        # Convert to 0-100 scale and clamp
        final_score = int(min(max(total_score * 100, 0), 100))
        
        return final_score, breakdown, factors


# =============================================================================
# Weight Optimization (Self-Learning)
# =============================================================================

def update_weights_from_journal(window_days=30, learning_rate=0.1):
    """
    Analyze recent journal/backtest outcomes and nudge weights to favor
    successful factor combinations.
    
    This is a simple gradient-free optimization based on correlation analysis.
    
    Args:
        window_days: lookback period for analysis
        learning_rate: how much to adjust weights (0-1, typically 0.05-0.2)
    
    Returns:
        dict: new_weights, performance_metrics
    """
    try:
        from signals.models import Signal, TradeScore, ScoringWeights
        from django.db.models import Avg, Count, Q
        
        # Get active weights
        current_weights_obj = ScoringWeights.get_active_weights()
        current_weights = current_weights_obj.weights.copy()
        
        # Analyze recent signals with scores
        cutoff = timezone.now() - timedelta(days=window_days)
        scored_signals = Signal.objects.filter(
            received_at__gte=cutoff,
            ai_score__isnull=False
        ).exclude(outcome='pending')
        
        if scored_signals.count() < 10:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least 10 completed signals, found {scored_signals.count()}'
            }
        
        # Compute correlation between factors and outcomes
        factor_correlations = {}
        
        for factor_name in ['confidence_factor', 'atr_safety_factor', 'strategy_bias_factor', 
                            'regime_fit_factor', 'rolling_win_rate']:
            # Get signals grouped by outcome
            green_signals = scored_signals.filter(outcome='green')
            red_signals = scored_signals.filter(outcome='red')
            
            if green_signals.exists() and red_signals.exists():
                # Average factor value for winning vs losing trades
                avg_green = green_signals.aggregate(avg=Avg(f'ai_score__{factor_name}'))['avg'] or 0
                avg_red = red_signals.aggregate(avg=Avg(f'ai_score__{factor_name}'))['avg'] or 0
                
                # Positive correlation = factor is predictive of success
                correlation = avg_green - avg_red
                factor_correlations[factor_name] = correlation
        
        # Adjust weights based on correlations
        weight_map = {
            'confidence_factor': 'signal_confidence',
            'atr_safety_factor': 'atr_safety',
            'strategy_bias_factor': 'strategy_bias',
            'regime_fit_factor': 'regime_fit',
            'rolling_win_rate': 'rolling_win_rate'
        }
        
        new_weights = current_weights.copy()
        for db_field, weight_key in weight_map.items():
            if db_field in factor_correlations:
                corr = factor_correlations[db_field]
                # Nudge weight up if positive correlation, down if negative
                adjustment = corr * learning_rate
                new_weights[weight_key] = max(0.05, min(0.50, 
                    new_weights.get(weight_key, 0.2) + adjustment
                ))
        
        # Normalize weights to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: v/total for k, v in new_weights.items()}
        
        return {
            'status': 'success',
            'old_weights': current_weights,
            'new_weights': new_weights,
            'correlations': factor_correlations,
            'analyzed_signals': scored_signals.count(),
            'win_rate': green_signals.count() / scored_signals.count() if scored_signals.count() > 0 else 0
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def score_signal(signal):
    """
    Main entry point to score a signal.
    
    Args:
        signal: Signal model instance
    
    Returns:
        TradeScore instance (saved to DB)
    """
    from signals.models import TradeScore, ScoringWeights
    
    # Get active weights
    weights_obj = ScoringWeights.get_active_weights()
    weights = weights_obj.weights
    
    # Create scorer with strategy-specific adjustments
    scorer = TradeScorer(weights=weights, strategy=signal.strategy)
    
    # Compute score
    final_score, breakdown, factors = scorer.score_signal(signal)
    
    # Generate human-readable explanation
    explanation = generate_score_explanation(signal, final_score, breakdown, factors)
    
    # Log the score
    logger.info(
        f"Signal #{signal.id} scored {final_score}/100 | "
        f"{signal.symbol} {signal.side.upper()} | "
        f"Strategy: {signal.strategy} | "
        f"Regime: {signal.regime}"
    )
    
    # Save or update TradeScore
    trade_score, created = TradeScore.objects.update_or_create(
        signal=signal,
        defaults={
            'ai_score': final_score,
            'score_breakdown': breakdown,
            'version': weights_obj.version,
            'confidence_factor': factors.get('conf_norm', 0),
            'atr_safety_factor': factors.get('atr_safety', 0),
            'strategy_bias_factor': factors.get('strategy_bias', 0),
            'regime_fit_factor': factors.get('regime_fit', 0),
            'rolling_win_rate': factors.get('rolling_win_rate', 0)
        }
    )
    
    # Log detailed explanation for high/low scores
    if final_score >= 80 or final_score <= 40:
        logger.info(f"Score explanation for #{signal.id}:\n{explanation}")
    
    return trade_score


def generate_score_explanation(signal, final_score, breakdown, factors):
    """
    Generate a human-readable explanation of the AI score.
    
    Example output:
    "Trade scored 82 — trend confidence high, ATR stable, London session bias, 
    strategy win rate 68%."
    
    Args:
        signal: Signal instance
        final_score: Final score (0-100)
        breakdown: List of factor breakdowns
        factors: Dict of normalized factors
    
    Returns:
        str: Human-readable explanation
    """
    explanations = []
    
    # Overall assessment
    if final_score >= 80:
        assessment = "Excellent setup"
    elif final_score >= 65:
        assessment = "Good setup"
    elif final_score >= 50:
        assessment = "Moderate setup"
    else:
        assessment = "Weak setup"
    
    # Confidence analysis
    conf = factors.get('conf_norm', 0) * 100
    if conf >= 80:
        explanations.append("high signal confidence")
    elif conf >= 60:
        explanations.append("moderate confidence")
    else:
        explanations.append("low confidence")
    
    # ATR safety
    atr = factors.get('atr_safety', 0)
    if atr >= 0.7:
        explanations.append("tight stop placement")
    elif atr >= 0.4:
        explanations.append("moderate stop distance")
    else:
        explanations.append("wide stop placement")
    
    # Regime fit
    regime_fit = factors.get('regime_fit', 0)
    if regime_fit >= 0.8:
        explanations.append(f"excellent {signal.regime} alignment")
    elif regime_fit >= 0.6:
        explanations.append(f"good {signal.regime} fit")
    else:
        explanations.append(f"weak {signal.regime} alignment")
    
    # Session preference
    session_fit = factors.get('session_fit', 0)
    if session_fit >= 0.8:
        explanations.append(f"{signal.session} session optimal")
    elif session_fit >= 0.6:
        explanations.append(f"{signal.session} session suitable")
    
    # Historical performance
    rolling_wr = factors.get('rolling_win_rate', 0) * 100
    if rolling_wr >= 60:
        explanations.append(f"strong historical performance ({rolling_wr:.0f}% WR)")
    elif rolling_wr >= 50:
        explanations.append(f"balanced historical data ({rolling_wr:.0f}% WR)")
    elif rolling_wr > 0:
        explanations.append(f"challenging recent performance ({rolling_wr:.0f}% WR)")
    else:
        explanations.append("no historical data")
    
    # Strategy-specific notes
    if signal.strategy in STRATEGY_WEIGHT_ADJUSTMENTS:
        explanations.append(f"strategy-tuned weights applied")
    
    # Combine into readable sentence
    explanation = f"{assessment}: {', '.join(explanations)}."
    
    # Add score at the beginning
    full_explanation = f"Trade scored {final_score}/100 — {explanation}"
    
    return full_explanation


def bulk_rescore_signals(signal_queryset):
    """
    Rescore multiple signals efficiently.
    
    Args:
        signal_queryset: QuerySet of Signal objects
    
    Returns:
        dict with stats
    """
    from signals.models import ScoringWeights
    
    weights_obj = ScoringWeights.get_active_weights()
    scorer = TradeScorer(weights=weights_obj.weights)
    
    scored_count = 0
    for signal in signal_queryset:
        try:
            score_signal(signal)
            scored_count += 1
        except Exception as e:
            print(f"Error scoring signal {signal.id}: {e}")
    
    return {
        'total': signal_queryset.count(),
        'scored': scored_count,
        'version': weights_obj.version
    }
