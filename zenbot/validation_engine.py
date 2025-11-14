"""
ZenithEdge AI Validation Engine (Truth Filter)
Evaluates signal quality before publication using multi-dimensional scoring.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, Tuple

import pandas as pd
from django.db.models import Avg, Count, Q
from django.utils import timezone

logger = logging.getLogger('zenbot')


class SignalValidator:
    """
    AI-powered validation layer that evaluates signals across multiple dimensions:
    - Technical integrity
    - Volatility conditions
    - Market regime alignment
    - News sentiment coherence
    - Historical strategy performance
    - Psychological risk factors
    """
    
    # Thresholds
    TRUTH_INDEX_REJECT = 60  # Below this = discard
    TRUTH_INDEX_CONDITIONAL = 80  # 60-80 = needs review
    TRUTH_INDEX_APPROVED = 80  # 80+ = auto-approve
    
    def __init__(self):
        self.validation_cache = {}
    
    def validate_signal(self, signal_data: dict) -> Dict:
        """
        Main validation entry point.
        
        Args:
            signal_data: Raw signal dict from TradingView
            
        Returns:
            {
                'truth_index': float (0-100),
                'status': 'approved' | 'conditional' | 'rejected',
                'breakdown': dict of sub-scores,
                'validation_notes': list of reasons,
                'recommendation': str
            }
        """
        logger.info(f"Validating signal: {signal_data.get('symbol')} {signal_data.get('side')}")
        
        # Initialize result
        result = {
            'truth_index': 0.0,
            'status': 'rejected',
            'breakdown': {},
            'validation_notes': [],
            'recommendation': ''
        }
        
        # Calculate sub-scores (0-1 scale)
        scores = {
            'technical_integrity': self._check_technical_integrity(signal_data),
            'volatility_filter': self._check_volatility(signal_data),
            'regime_alignment': self._check_regime_match(signal_data),
            'sentiment_coherence': self._check_sentiment(signal_data),
            'historical_reliability': self._check_historical_performance(signal_data),
            'psychological_safety': self._check_psychological_factors(signal_data)
        }
        
        # Calculate weighted truth index (0-100)
        weights = {
            'technical_integrity': 0.25,
            'volatility_filter': 0.15,
            'regime_alignment': 0.20,
            'sentiment_coherence': 0.15,
            'historical_reliability': 0.15,
            'psychological_safety': 0.10
        }
        
        truth_index = sum(scores[k] * weights[k] * 100 for k in scores.keys())
        result['truth_index'] = round(truth_index, 1)
        result['breakdown'] = {k: round(v * 100, 1) for k, v in scores.items()}
        
        # Determine status
        if truth_index >= self.TRUTH_INDEX_APPROVED:
            result['status'] = 'approved'
            result['validation_notes'].append('✅ Signal passed all validation checks')
        elif truth_index >= self.TRUTH_INDEX_REJECT:
            result['status'] = 'conditional'
            result['validation_notes'].append('⚠️ Signal requires manual review')
        else:
            result['status'] = 'rejected'
            result['validation_notes'].append('❌ Signal rejected - quality threshold not met')
        
        # Add detailed notes
        result['validation_notes'].extend(self._generate_validation_notes(scores, signal_data))
        
        # Generate recommendation
        result['recommendation'] = self._generate_recommendation(result, signal_data)
        
        logger.info(f"Validation complete: Truth Index {truth_index:.1f} - Status: {result['status']}")
        
        return result
    
    def _check_technical_integrity(self, signal_data: dict) -> float:
        """
        Verify signal technical logic is sound.
        Checks: price levels, SL/TP ratios, strategy consistency.
        """
        score = 1.0
        reasons = []
        
        try:
            # Check if required fields present
            required = ['symbol', 'side', 'strategy', 'price']
            if not all(field in signal_data for field in required):
                score -= 0.3
                reasons.append("Missing required fields")
            
            # Validate risk-reward ratio
            if 'sl' in signal_data and 'tp' in signal_data and 'price' in signal_data:
                price = float(signal_data['price'])
                sl = float(signal_data['sl'])
                tp = float(signal_data['tp'])
                
                risk = abs(price - sl)
                reward = abs(tp - price)
                
                if risk > 0:
                    rr_ratio = reward / risk
                    if rr_ratio < 1.0:
                        score -= 0.2
                        reasons.append(f"Poor R:R ratio: {rr_ratio:.2f}")
                    elif rr_ratio < 1.5:
                        score -= 0.1
                        reasons.append(f"Suboptimal R:R: {rr_ratio:.2f}")
                else:
                    score -= 0.4
                    reasons.append("Invalid stop loss")
            
            # Check confidence score if present
            if 'confidence' in signal_data:
                confidence = float(signal_data['confidence'])
                if confidence < 50:
                    score -= 0.2
                    reasons.append(f"Low confidence: {confidence}%")
                elif confidence < 70:
                    score -= 0.1
            
            # Strategy validation (check if known strategy)
            strategy = signal_data.get('strategy', '').lower()
            known_strategies = ['smc', 'ict', 'wyckoff', 'vsa', 'elliot', 'harmonic']
            if strategy and not any(s in strategy for s in known_strategies):
                score -= 0.1
                reasons.append("Unknown strategy type")
        
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Technical integrity check error: {e}")
            score -= 0.3
            reasons.append("Data validation error")
        
        return max(0.0, min(1.0, score))
    
    def _check_volatility(self, signal_data: dict) -> float:
        """
        Check if market volatility is acceptable for trading.
        High volatility = higher risk, lower score.
        """
        score = 0.85  # Default good score
        
        try:
            from signals.models import Signal
            
            symbol = signal_data.get('symbol')
            if not symbol:
                return 0.7
            
            # Get recent price movements
            recent_signals = Signal.objects.filter(
                symbol=symbol,
                received_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-received_at')[:20]
            
            if recent_signals.count() > 5:
                prices = [float(s.price) for s in recent_signals if s.price]
                if prices:
                    df = pd.Series(prices)
                    volatility = df.std() / df.mean() if df.mean() > 0 else 0
                    
                    # Score based on volatility
                    if volatility > 0.05:  # 5% volatility
                        score = 0.5
                    elif volatility > 0.03:  # 3% volatility
                        score = 0.7
                    elif volatility > 0.02:  # 2% volatility
                        score = 0.85
                    else:
                        score = 0.95
        
        except Exception as e:
            logger.warning(f"Volatility check error: {e}")
            score = 0.7
        
        return score
    
    def _check_regime_match(self, signal_data: dict) -> float:
        """
        Verify signal aligns with current market regime.
        """
        score = 0.8  # Default neutral
        
        try:
            regime = signal_data.get('regime', '').lower()
            side = signal_data.get('side', '').lower()
            
            # Regime alignment logic
            if regime == 'trending':
                score = 0.9  # Trending is good for directional trades
            elif regime == 'ranging':
                # Range trading needs different approach
                if 'breakout' in signal_data.get('strategy', '').lower():
                    score = 0.6  # Breakout in range = lower confidence
                else:
                    score = 0.85
            elif regime == 'volatile':
                score = 0.6  # High risk in volatile markets
            elif regime == 'consolidation':
                score = 0.75
        
        except Exception as e:
            logger.warning(f"Regime check error: {e}")
        
        return score
    
    def _check_sentiment(self, signal_data: dict) -> float:
        """
        Check if news sentiment aligns with signal direction.
        """
        score = 0.75  # Neutral if no sentiment data
        
        try:
            from zennews.models import NewsEvent
            
            symbol = signal_data.get('symbol')
            side = signal_data.get('side', '').lower()
            
            if not symbol:
                return score
            
            # Get recent news for this symbol
            recent_news = NewsEvent.objects.filter(
                symbol=symbol,
                timestamp__gte=timezone.now() - timedelta(hours=12)
            ).order_by('-timestamp')[:5]
            
            if recent_news.exists():
                avg_sentiment = recent_news.aggregate(Avg('sentiment'))['sentiment__avg'] or 0
                
                # Check alignment
                if side == 'buy' and avg_sentiment > 0.3:
                    score = 0.95  # Bullish news + buy signal = good
                elif side == 'sell' and avg_sentiment < -0.3:
                    score = 0.95  # Bearish news + sell signal = good
                elif side == 'buy' and avg_sentiment < -0.3:
                    score = 0.4  # Bullish signal against bearish news = risky
                elif side == 'sell' and avg_sentiment > 0.3:
                    score = 0.4  # Bearish signal against bullish news = risky
                else:
                    score = 0.75  # Neutral sentiment
        
        except Exception as e:
            logger.warning(f"Sentiment check error: {e}")
        
        return score
    
    def _check_historical_performance(self, signal_data: dict) -> float:
        """
        Check historical win rate for this strategy-symbol combination.
        """
        score = 0.7  # Neutral default
        
        try:
            from signals.models import StrategyPerformance
            
            strategy = signal_data.get('strategy')
            symbol = signal_data.get('symbol')
            
            if not strategy or not symbol:
                return score
            
            # Get strategy performance
            perf = StrategyPerformance.objects.filter(
                strategy_name=strategy,
                symbol=symbol
            ).first()
            
            if perf and perf.total_trades >= 10:  # Need at least 10 trades
                win_rate = perf.win_rate
                
                if win_rate >= 65:
                    score = 0.95
                elif win_rate >= 55:
                    score = 0.85
                elif win_rate >= 50:
                    score = 0.75
                elif win_rate >= 45:
                    score = 0.65
                else:
                    score = 0.4  # Poor historical performance
        
        except Exception as e:
            logger.warning(f"Historical performance check error: {e}")
        
        return score
    
    def _check_psychological_factors(self, signal_data: dict) -> float:
        """
        Check for psychological risk factors (drawdown, overtrading, etc).
        """
        score = 0.9  # Default good
        
        try:
            from signals.models import Signal, RiskControl
            
            # Check recent signal frequency (avoid overtrading)
            recent_count = Signal.objects.filter(
                received_at__gte=timezone.now() - timedelta(hours=4)
            ).count()
            
            if recent_count > 10:
                score = 0.5  # Too many signals = possible overtrading
            elif recent_count > 5:
                score = 0.7
            
            # Check if risk controls are triggered
            risk_controls = RiskControl.objects.filter(is_halted=True)
            if risk_controls.exists():
                score *= 0.5  # Reduce score if risk controls active
        
        except Exception as e:
            logger.warning(f"Psychological check error: {e}")
        
        return score
    
    def _generate_validation_notes(self, scores: dict, signal_data: dict) -> list:
        """Generate human-readable validation notes."""
        notes = []
        
        for key, score in scores.items():
            label = key.replace('_', ' ').title()
            if score >= 0.9:
                notes.append(f"✅ {label}: Excellent ({score*100:.0f}%)")
            elif score >= 0.7:
                notes.append(f"✓ {label}: Good ({score*100:.0f}%)")
            elif score >= 0.5:
                notes.append(f"⚠️ {label}: Acceptable ({score*100:.0f}%)")
            else:
                notes.append(f"❌ {label}: Weak ({score*100:.0f}%)")
        
        return notes
    
    def _generate_recommendation(self, result: dict, signal_data: dict) -> str:
        """Generate action recommendation based on validation."""
        truth_index = result['truth_index']
        status = result['status']
        
        if status == 'approved':
            return f"✅ High-confidence signal ({truth_index:.0f}/100). Proceed with standard risk management."
        elif status == 'conditional':
            return f"⚠️ Moderate-confidence signal ({truth_index:.0f}/100). Review carefully before execution."
        else:
            return f"❌ Low-confidence signal ({truth_index:.0f}/100). Avoid or wait for confirmation."


# Global validator instance
validator = SignalValidator()


def validate_signal(signal_data: dict) -> Dict:
    """
    Convenience function to validate a signal.
    
    Args:
        signal_data: Raw signal dictionary
        
    Returns:
        Validation result dictionary
    """
    return validator.validate_signal(signal_data)
