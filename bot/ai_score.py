"""
AI Trade Score Predictor
Powered by XGBoost machine learning model.

This module provides functions to:
1. Extract features from trading signals
2. Train a predictive model from historical data
3. Score new signals based on learned patterns
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import RandomForestClassifier
    XGBOOST_AVAILABLE = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Model storage path
MODEL_DIR = Path(__file__).parent / 'models'
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / 'trade_score_model.pkl'
SCALER_PATH = MODEL_DIR / 'trade_score_scaler.pkl'
VERSION = 'v1.0'


def extract_features(signal_object) -> Dict[str, float]:
    """
    Extract numerical features from a signal object.
    
    Returns a dictionary of features used for scoring.
    """
    from signals.models import Signal, TradeJournalEntry
    from django.db.models import Count, Avg
    from django.utils import timezone
    
    features = {}
    
    # 1. Signal confidence (from TradingView Pine)
    features['confidence'] = float(signal_object.confidence or 50)
    
    # 2. Stop loss distance as percentage
    if signal_object.price and signal_object.sl:
        sl_distance = abs(signal_object.price - signal_object.sl)
        features['sl_distance_pct'] = (sl_distance / signal_object.price) * 100
    else:
        features['sl_distance_pct'] = 2.0  # Default
    
    # 3. Take profit distance as percentage
    if signal_object.price and signal_object.tp:
        tp_distance = abs(signal_object.tp - signal_object.price)
        features['tp_distance_pct'] = (tp_distance / signal_object.price) * 100
    else:
        features['tp_distance_pct'] = 4.0  # Default
    
    # 4. Risk/Reward ratio
    if features['sl_distance_pct'] > 0:
        features['risk_reward_ratio'] = features['tp_distance_pct'] / features['sl_distance_pct']
    else:
        features['risk_reward_ratio'] = 2.0
    
    # 5. Strategy encoding (one-hot)
    strategy_map = {
        'Trend Following': 1,
        'Range Trading': 2,
        'Breakout': 3,
        'Mean Reversion': 4,
        'Momentum': 5
    }
    features['strategy_encoded'] = strategy_map.get(signal_object.strategy, 0)
    
    # 6. Regime encoding
    regime_map = {
        'Bullish': 3,
        'Ranging': 2,
        'Bearish': 1,
        'Volatile': 2
    }
    features['regime_encoded'] = regime_map.get(signal_object.regime, 2)
    
    # 7. Side encoding
    features['is_buy'] = 1 if signal_object.side == 'BUY' else 0
    
    # 8. Symbol volatility indicator (major pairs = lower risk)
    major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
    features['is_major_pair'] = 1 if signal_object.symbol in major_pairs else 0
    
    # 9. Historical strategy success rate (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    past_signals = Signal.objects.filter(
        user=signal_object.user,
        strategy=signal_object.strategy,
        received_at__gte=thirty_days_ago
    )
    
    total_past = past_signals.count()
    if total_past > 0:
        winning_past = past_signals.filter(outcome='green').count()
        features['strategy_win_rate'] = (winning_past / total_past) * 100
    else:
        features['strategy_win_rate'] = 50.0  # Neutral
    
    # 10. User's overall win rate (last 30 days)
    user_signals = Signal.objects.filter(
        user=signal_object.user,
        received_at__gte=thirty_days_ago
    )
    
    total_user = user_signals.count()
    if total_user > 0:
        winning_user = user_signals.filter(outcome='green').count()
        features['user_win_rate'] = (winning_user / total_user) * 100
    else:
        features['user_win_rate'] = 50.0
    
    # 11. Time of day factor (session awareness)
    signal_hour = signal_object.timestamp.hour if signal_object.timestamp else 12
    # Peak trading hours: London (8-12 UTC) and NY (13-17 UTC)
    if 8 <= signal_hour <= 17:
        features['in_peak_hours'] = 1
    else:
        features['in_peak_hours'] = 0
    
    # 12. Consistency score (how many trades in last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_count = Signal.objects.filter(
        user=signal_object.user,
        received_at__gte=seven_days_ago
    ).count()
    features['recent_activity'] = min(recent_count / 10.0, 1.0) * 100  # Normalize to 0-100
    
    return features


def train_model(dataframe: pd.DataFrame, target_col: str = 'outcome') -> Tuple[object, object]:
    """
    Train a machine learning model to predict signal success.
    
    Args:
        dataframe: DataFrame with features and outcomes
        target_col: Column name for the target variable
        
    Returns:
        Tuple of (trained_model, scaler)
    """
    # Prepare features
    feature_cols = [col for col in dataframe.columns if col not in [target_col, 'signal_id']]
    X = dataframe[feature_cols]
    
    # Prepare target (1 for green/winning, 0 for red/losing)
    y = (dataframe[target_col] == 'green').astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    if XGBOOST_AVAILABLE:
        model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        print("📊 Training XGBoost model...")
    else:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        print("📊 Training RandomForest model...")
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"✅ Model trained successfully!")
    print(f"   Train accuracy: {train_score:.2%}")
    print(f"   Test accuracy: {test_score:.2%}")
    
    # Save model and scaler
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"💾 Model saved to {MODEL_PATH}")
    
    return model, scaler


def load_model() -> Tuple[Optional[object], Optional[object]]:
    """Load trained model and scaler from disk."""
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        
        return model, scaler
    except FileNotFoundError:
        return None, None


def predict_score(signal_object, apply_cognition: bool = True, apply_prop_mode: bool = True) -> Tuple[int, Dict]:
    """
    Predict AI score for a signal.
    
    Args:
        signal_object: Signal model instance
        apply_cognition: Whether to apply cognition intelligence adjustments (default: True)
        apply_prop_mode: Whether to apply prop firm challenge mode adjustments (default: True)
        
    Returns:
        Tuple of (ai_score, breakdown_dict)
    """
    # Extract features
    features = extract_features(signal_object)
    
    # Try to load trained model
    model, scaler = load_model()
    
    if model is None or scaler is None:
        # Fallback to rule-based scoring if no model exists
        base_score, breakdown = rule_based_score(features)
    else:
        # Prepare feature vector
        feature_vector = np.array([list(features.values())])
        
        # Scale features
        feature_vector_scaled = scaler.transform(feature_vector)
        
        # Get prediction probability
        try:
            prob = model.predict_proba(feature_vector_scaled)[0][1]  # Probability of success
            base_score = int(prob * 100)
        except Exception as e:
            print(f"⚠️ Model prediction failed: {e}")
            base_score, breakdown = rule_based_score(features)
            return base_score, breakdown
        
        # Generate breakdown
        breakdown = generate_breakdown(features, base_score)
    
    # Apply Cognition Intelligence (if enabled)
    if apply_cognition:
        try:
            # Prepare signal data for cluster prediction
            signal_data = {
                'timestamp': signal_object.timestamp.isoformat() if signal_object.timestamp else None,
                'strategy': signal_object.strategy,
                'confidence': features.get('confidence', 50),
                'timeframe': getattr(signal_object, 'timeframe', '15m'),
                'symbol': signal_object.symbol,
            }
            
            # Get cognition bias adjustment
            cognition_adjustment, cognition_breakdown = integrate_cognition_bias(
                symbol=signal_object.symbol,
                user=signal_object.user,
                signal_data=signal_data
            )
            
            # Apply adjustment to score
            final_score = max(0, min(100, base_score + cognition_adjustment))
            
            # Add cognition data to breakdown
            breakdown['base_score'] = base_score
            breakdown['cognition_adjustment'] = round(cognition_adjustment, 2)
            breakdown['cognition_data'] = cognition_breakdown
            breakdown['final_score'] = final_score
            
            return int(final_score), breakdown
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Cognition integration failed in predict_score: {e}")
            # Return base score without cognition
            breakdown['cognition_error'] = str(e)
            # Continue to prop mode even if cognition fails
            final_score = base_score
    else:
        final_score = base_score
    
    # Apply PropCoach Mode (if enabled and user has active challenge)
    if apply_prop_mode:
        try:
            from propcoach.prop_mode import apply_prop_mode
            
            # Apply prop mode adjustments
            prop_score, prop_breakdown = apply_prop_mode(signal_object, final_score, breakdown)
            
            # Add prop data to breakdown
            if prop_breakdown.get('prop_mode_enabled'):
                breakdown['prop_mode'] = prop_breakdown
                breakdown['score_before_prop'] = final_score
                breakdown['score_after_prop'] = prop_score
                final_score = prop_score
            else:
                breakdown['prop_mode'] = {'enabled': False, 'message': prop_breakdown.get('message', 'No active challenge')}
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"PropCoach mode integration failed in predict_score: {e}")
            breakdown['prop_mode_error'] = str(e)
    
    return final_score, breakdown


def rule_based_score(features: Dict[str, float]) -> Tuple[int, Dict]:
    """
    Fallback rule-based scoring when ML model is not available.
    """
    score = 50  # Start at neutral
    breakdown = {}
    
    # Confidence factor (weight: 20%)
    confidence_contribution = (features['confidence'] - 50) * 0.4
    score += confidence_contribution
    breakdown['confidence'] = f"+{confidence_contribution:.1f} (base: {features['confidence']:.0f}%)"
    
    # Risk/Reward ratio (weight: 15%)
    rr_ratio = features['risk_reward_ratio']
    if rr_ratio >= 2.0:
        rr_contribution = 15
    elif rr_ratio >= 1.5:
        rr_contribution = 10
    else:
        rr_contribution = -5
    score += rr_contribution
    breakdown['risk_reward'] = f"{'+' if rr_contribution >= 0 else ''}{rr_contribution} (R:R = {rr_ratio:.2f})"
    
    # Strategy win rate (weight: 25%)
    win_rate_contribution = (features['strategy_win_rate'] - 50) * 0.5
    score += win_rate_contribution
    breakdown['strategy_performance'] = f"{'+' if win_rate_contribution >= 0 else ''}{win_rate_contribution:.1f} (win rate: {features['strategy_win_rate']:.0f}%)"
    
    # User win rate (weight: 20%)
    user_contribution = (features['user_win_rate'] - 50) * 0.4
    score += user_contribution
    breakdown['user_performance'] = f"{'+' if user_contribution >= 0 else ''}{user_contribution:.1f} (user WR: {features['user_win_rate']:.0f}%)"
    
    # Major pair bonus (weight: 10%)
    if features['is_major_pair']:
        score += 10
        breakdown['asset_type'] = "+10 (major pair)"
    else:
        breakdown['asset_type'] = "0 (exotic pair)"
    
    # Peak hours bonus (weight: 5%)
    if features['in_peak_hours']:
        score += 5
        breakdown['timing'] = "+5 (peak trading hours)"
    else:
        breakdown['timing'] = "0 (off-peak)"
    
    # Recent activity factor (weight: 5%)
    activity_contribution = features['recent_activity'] * 0.05
    score += activity_contribution
    breakdown['consistency'] = f"+{activity_contribution:.1f} (active trader)"
    
    # Clamp score to 0-100
    ai_score = max(0, min(100, int(score)))
    
    breakdown['model_type'] = 'rule-based (no ML model trained yet)'
    breakdown['version'] = VERSION
    
    return ai_score, breakdown


def generate_breakdown(features: Dict[str, float], ai_score: int) -> Dict:
    """Generate human-readable breakdown of scoring factors."""
    breakdown = {
        'confidence': features['confidence'],
        'risk_reward_ratio': round(features['risk_reward_ratio'], 2),
        'strategy_win_rate': round(features['strategy_win_rate'], 1),
        'user_win_rate': round(features['user_win_rate'], 1),
        'is_major_pair': bool(features['is_major_pair']),
        'in_peak_hours': bool(features['in_peak_hours']),
        'strategy': features['strategy_encoded'],
        'regime': features['regime_encoded'],
        'model_type': 'xgboost' if XGBOOST_AVAILABLE else 'random_forest',
        'version': VERSION,
        'total_score': ai_score
    }
    
    return breakdown


def explain_score(ai_score: int, breakdown: Dict) -> str:
    """
    Generate natural language explanation of the AI score.
    """
    # Check if cognition was applied
    cognition_data = breakdown.get('cognition_data', {})
    has_cognition = cognition_data.get('cognition_enabled', False)
    base_score = breakdown.get('base_score', ai_score)
    
    explanation = f"This trade scored **{ai_score}/100** "
    
    if ai_score >= 80:
        explanation += "✅ (High Confidence)\n\n"
    elif ai_score >= 50:
        explanation += "🟡 (Medium)\n\n"
    else:
        explanation += "🚫 (Risky)\n\n"
    
    # Show cognition verdict if available
    if has_cognition:
        verdict = cognition_data.get('cognition_verdict', '')
        if verdict:
            explanation += f"**{verdict}**\n\n"
    
    explanation += "**Scoring Factors:**\n"
    
    # Confidence (handle both numeric and string formats)
    conf = breakdown.get('confidence', 50)
    if isinstance(conf, str):
        # Extract number from string like "+20 (base: 75%)"
        try:
            conf = float(conf.split('base:')[1].split('%')[0].strip()) if 'base:' in conf else 50
        except:
            conf = 50
    
    if conf >= 80:
        explanation += f"• Strong signal confidence ({conf:.0f}%) 💪\n"
    elif conf >= 60:
        explanation += f"• Moderate signal confidence ({conf:.0f}%) 👍\n"
    else:
        explanation += f"• Low signal confidence ({conf:.0f}%) ⚠️\n"
    
    # Risk/Reward
    rr = breakdown.get('risk_reward_ratio', 1.0)
    if not isinstance(rr, (int, float)):
        rr = 1.0
    if rr >= 2.0:
        explanation += f"• Excellent risk/reward ratio ({rr:.2f}:1) 🎯\n"
    elif rr >= 1.5:
        explanation += f"• Good risk/reward ratio ({rr:.2f}:1) ✓\n"
    else:
        explanation += f"• Poor risk/reward ratio ({rr:.2f}:1) ⚠️\n"
    
    # Strategy performance
    strat_wr = breakdown.get('strategy_win_rate', 50)
    if not isinstance(strat_wr, (int, float)):
        strat_wr = 50
    if strat_wr >= 60:
        explanation += f"• Strategy has strong track record ({strat_wr:.0f}% win rate) 📈\n"
    elif strat_wr >= 50:
        explanation += f"• Strategy has neutral track record ({strat_wr:.0f}% win rate)\n"
    else:
        explanation += f"• Strategy has poor track record ({strat_wr:.0f}% win rate) 📉\n"
    
    # User performance
    user_wr = breakdown.get('user_win_rate', 50)
    if not isinstance(user_wr, (int, float)):
        user_wr = 50
    if user_wr >= 60:
        explanation += f"• Your recent performance is strong ({user_wr:.0f}% win rate) 🔥\n"
    elif user_wr >= 50:
        explanation += f"• Your recent performance is average ({user_wr:.0f}% win rate)\n"
    else:
        explanation += f"• Your recent performance needs improvement ({user_wr:.0f}% win rate) 💡\n"
    
    # Asset type
    if breakdown.get('is_major_pair'):
        explanation += "• Trading major currency pair (lower risk) ✅\n"
    else:
        explanation += "• Trading exotic pair (higher risk) ⚠️\n"
    
    # Timing
    if breakdown.get('in_peak_hours'):
        explanation += "• Signal during peak market hours (better liquidity) ⏰\n"
    
    # Add cognition intelligence section
    if has_cognition:
        explanation += "\n**🧠 Cognition Intelligence:**\n"
        
        # Psychology
        psych_status = cognition_data.get('psychology_status', 'Unknown')
        psych_bias = cognition_data.get('psychological_bias', 0)
        if psych_bias != 0:
            explanation += f"• Mental State: {psych_status} ({psych_bias:+.2f})\n"
            
            emotional_tone = cognition_data.get('emotional_tone')
            if emotional_tone:
                explanation += f"  Emotional Tone: {emotional_tone.title()}\n"
            
            biases = cognition_data.get('detected_biases', [])
            if biases:
                explanation += f"  ⚠️ Biases: {', '.join(biases)}\n"
        
        # Market Regime
        regime_status = cognition_data.get('regime_status', 'Unknown')
        regime_bias = cognition_data.get('regime_bias', 0)
        if regime_bias != 0:
            explanation += f"• Market Regime: {regime_status} ({regime_bias:+.2f})\n"
            
            regime_type = cognition_data.get('regime_type')
            if regime_type:
                explanation += f"  Type: {regime_type.replace('_', ' ').title()}\n"
        
        # Signal Cluster
        cluster_status = cognition_data.get('cluster_status', 'Unknown')
        cluster_rel = cognition_data.get('cluster_reliability', 0)
        if cluster_rel != 0:
            explanation += f"• Signal Pattern: {cluster_status} (reliability: {cluster_rel:.2f})\n"
            
            cluster_wr = cognition_data.get('cluster_win_rate')
            if cluster_wr:
                explanation += f"  Historical Win Rate: {cluster_wr:.0%}\n"
        
        # Show adjustment
        adjustment = breakdown.get('cognition_adjustment', 0)
        if adjustment != 0:
            explanation += f"\n*Cognition Adjustment: {adjustment:+.1f} points (Base: {base_score} → Final: {ai_score})*\n"
    
    explanation += f"\n*Model: {breakdown.get('model_type', 'rule-based')} {breakdown.get('version', VERSION)}*"
    
    return explanation


def integrate_news_bias(symbol: str, base_score: float) -> Tuple[float, float, Dict]:
    """
    Integrate news sentiment bias into trade score
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        base_score: Base AI score before news adjustment
        
    Returns:
        Tuple of (adjusted_score, bias_adjustment, news_data)
    """
    try:
        from zennews.models import NewsEvent
        from django.utils import timezone
        import numpy as np
        
        # Get recent news for this symbol (last 3 hours)
        recent_news = NewsEvent.objects.filter(
            symbol=symbol,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=3)
        ).order_by('-timestamp')
        
        if not recent_news.exists():
            return base_score, 0.0, {'news_count': 0, 'message': 'No recent news'}
        
        # Calculate news bias
        sentiments = [news.sentiment for news in recent_news]
        avg_sentiment = float(np.mean(sentiments))
        
        # Weight by impact level
        impact_weights = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.5
        }
        
        weighted_impacts = []
        for news in recent_news:
            weight = impact_weights.get(news.impact_level, 1.0)
            weighted_impacts.append(weight)
        
        avg_impact_weight = float(np.mean(weighted_impacts)) if weighted_impacts else 1.0
        
        # Calculate bias adjustment (-10 to +10)
        # Formula: sentiment (-1 to 1) * impact_weight (0.5 to 1.5) * 5 (scaling factor)
        bias_adjustment = avg_sentiment * avg_impact_weight * 5.0
        
        # Apply adjustment to base score
        adjusted_score = max(0.0, min(100.0, base_score + bias_adjustment))
        
        # Prepare news data for logging
        news_data = {
            'news_count': recent_news.count(),
            'avg_sentiment': round(avg_sentiment, 3),
            'avg_impact_weight': round(avg_impact_weight, 2),
            'bias_adjustment': round(bias_adjustment, 2),
            'top_headlines': [
                {
                    'headline': news.headline[:100],
                    'sentiment': round(news.sentiment, 2),
                    'impact': news.impact_level,
                }
                for news in recent_news[:3]
            ]
        }
        
        return adjusted_score, bias_adjustment, news_data
        
    except Exception as e:
        # If zennews not available or any error, return original score
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"News bias integration failed: {str(e)}")
        return base_score, 0.0, {'error': str(e)}


def get_news_sentiment_summary(symbol: str, hours: int = 24) -> Dict:
    """
    Get a summary of news sentiment for a symbol
    
    Args:
        symbol: Trading symbol
        hours: Hours to look back
        
    Returns:
        Dict with sentiment summary
    """
    try:
        from zennews.models import NewsEvent
        from django.utils import timezone
        from django.db.models import Avg, Count
        import numpy as np
        
        news_query = NewsEvent.objects.filter(
            symbol=symbol,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=hours)
        )
        
        if not news_query.exists():
            return {
                'status': 'no_data',
                'news_count': 0,
                'message': f'No news found for {symbol} in last {hours} hours'
            }
        
        # Aggregate statistics
        stats = news_query.aggregate(
            avg_sentiment=Avg('sentiment'),
            total_count=Count('id')
        )
        
        # Impact breakdown
        impact_counts = {
            'high': news_query.filter(impact_level='high').count(),
            'medium': news_query.filter(impact_level='medium').count(),
            'low': news_query.filter(impact_level='low').count(),
        }
        
        # Sentiment label
        avg_sent = stats['avg_sentiment'] or 0
        if avg_sent > 0.3:
            sentiment_label = 'Bullish'
        elif avg_sent < -0.3:
            sentiment_label = 'Bearish'
        else:
            sentiment_label = 'Neutral'
        
        return {
            'status': 'success',
            'symbol': symbol,
            'news_count': stats['total_count'],
            'avg_sentiment': round(avg_sent, 3),
            'sentiment_label': sentiment_label,
            'impact_breakdown': impact_counts,
            'high_impact_count': impact_counts['high'],
            'period_hours': hours,
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def integrate_cognition_bias(symbol: str, user, signal_data: Dict) -> Tuple[float, Dict]:
    """
    Integrate cognition intelligence to adjust trade score.
    
    This function combines:
    1. Psychological bias from trader's recent journal entries and emotional state
    2. Market regime suitability for the current symbol and conditions
    3. Signal cluster reliability based on similar historical patterns
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        user: User object
        signal_data: Dict containing signal features for cluster prediction
        
    Returns:
        Tuple of (bias_adjustment, breakdown_data)
        - bias_adjustment: Score delta (-10 to +10 points)
        - breakdown_data: Dict with detailed cognition metrics
    """
    try:
        from cognition.models import TraderPsychology, MarketRegime, SignalCluster
        from cognition.utils import SignalClusterer
        from django.utils import timezone
        from datetime import timedelta
        import logging
        
        logger = logging.getLogger(__name__)
        breakdown = {}
        
        # 1. PSYCHOLOGICAL BIAS (Weight: 30%)
        # Get recent psychology entries (last 24 hours)
        try:
            recent_psych = TraderPsychology.objects.filter(
                user=user,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-timestamp').first()
            
            if recent_psych:
                psych_bias = recent_psych.get_psychological_bias_score()
                breakdown['psychological_bias'] = round(psych_bias, 3)
                breakdown['emotional_tone'] = recent_psych.emotional_tone
                breakdown['detected_biases'] = recent_psych.detected_biases
                breakdown['discipline_score'] = round(recent_psych.discipline_score, 2)
                
                # Interpret psychology state
                if psych_bias > 0.5:
                    breakdown['psychology_status'] = 'Excellent mental state'
                elif psych_bias > 0:
                    breakdown['psychology_status'] = 'Good mental state'
                elif psych_bias > -0.3:
                    breakdown['psychology_status'] = 'Neutral state, watch emotions'
                else:
                    breakdown['psychology_status'] = 'Poor mental state - caution advised'
            else:
                psych_bias = 0.0
                breakdown['psychological_bias'] = 0.0
                breakdown['psychology_status'] = 'No recent psychology data'
        except Exception as e:
            logger.warning(f"Psychology bias calculation failed: {e}")
            psych_bias = 0.0
            breakdown['psychological_bias'] = 0.0
            breakdown['psychology_status'] = f'Error: {str(e)[:50]}'
        
        # 2. MARKET REGIME BIAS (Weight: 40%)
        # Get recent regime for this symbol (last 1 hour)
        try:
            recent_regime = MarketRegime.objects.filter(
                symbol=symbol,
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).order_by('-timestamp').first()
            
            if recent_regime:
                regime_bias = recent_regime.get_regime_bias_score()
                breakdown['regime_bias'] = round(regime_bias, 3)
                breakdown['regime_type'] = recent_regime.regime_type
                breakdown['regime_confidence'] = round(recent_regime.regime_confidence, 2)
                breakdown['trend_strength'] = round(recent_regime.trend_strength, 2)
                
                # Interpret regime
                if regime_bias > 0.5:
                    breakdown['regime_status'] = f'Excellent {recent_regime.regime_type} conditions'
                elif regime_bias > 0:
                    breakdown['regime_status'] = f'Good {recent_regime.regime_type} conditions'
                elif regime_bias > -0.3:
                    breakdown['regime_status'] = f'Neutral {recent_regime.regime_type} conditions'
                else:
                    breakdown['regime_status'] = f'Poor {recent_regime.regime_type} - avoid trading'
            else:
                regime_bias = 0.0
                breakdown['regime_bias'] = 0.0
                breakdown['regime_status'] = f'No recent regime data for {symbol}'
        except Exception as e:
            logger.warning(f"Regime bias calculation failed: {e}")
            regime_bias = 0.0
            breakdown['regime_bias'] = 0.0
            breakdown['regime_status'] = f'Error: {str(e)[:50]}'
        
        # 3. SIGNAL CLUSTER RELIABILITY (Weight: 30%)
        # Predict which cluster this signal belongs to and get reliability
        try:
            if signal_data:
                clusterer = SignalClusterer()
                
                # Check if we have trained clusters
                cluster_count = SignalCluster.objects.count()
                if cluster_count > 0:
                    # Predict cluster for this signal
                    cluster_id, cluster_confidence = clusterer.predict_cluster(signal_data)
                    
                    # Get cluster from database
                    cluster = SignalCluster.objects.filter(cluster_id=cluster_id).first()
                    
                    if cluster:
                        cluster_reliability = cluster.get_cluster_reliability_score()
                        breakdown['cluster_reliability'] = round(cluster_reliability, 3)
                        breakdown['cluster_id'] = cluster_id
                        breakdown['cluster_name'] = cluster.cluster_name
                        breakdown['cluster_win_rate'] = round(cluster.win_rate, 2)
                        breakdown['cluster_confidence'] = round(cluster_confidence, 2)
                        
                        # Interpret cluster
                        if cluster_reliability > 0.7:
                            breakdown['cluster_status'] = f'Excellent pattern (⭐⭐⭐)'
                        elif cluster_reliability > 0.5:
                            breakdown['cluster_status'] = f'Good pattern (⭐⭐)'
                        elif cluster_reliability > 0.3:
                            breakdown['cluster_status'] = f'Average pattern (⭐)'
                        else:
                            breakdown['cluster_status'] = f'Poor pattern - be cautious'
                    else:
                        cluster_reliability = 0.5  # Neutral
                        breakdown['cluster_reliability'] = 0.5
                        breakdown['cluster_status'] = 'Cluster not found in database'
                else:
                    cluster_reliability = 0.5  # Neutral
                    breakdown['cluster_reliability'] = 0.5
                    breakdown['cluster_status'] = 'No signal clusters available yet'
            else:
                cluster_reliability = 0.5  # Neutral
                breakdown['cluster_reliability'] = 0.5
                breakdown['cluster_status'] = 'No signal data provided for clustering'
        except Exception as e:
            logger.warning(f"Cluster reliability calculation failed: {e}")
            cluster_reliability = 0.5
            breakdown['cluster_reliability'] = 0.5
            breakdown['cluster_status'] = f'Error: {str(e)[:50]}'
        
        # 4. COMBINE ALL BIASES WITH WEIGHTS
        # Formula: (psych * 0.3) + (regime * 0.4) + (cluster * 0.3)
        # Each component ranges from -1 to +1, result is -1 to +1
        combined_bias = (
            psych_bias * 0.3 +       # 30% weight to psychology
            regime_bias * 0.4 +       # 40% weight to market regime
            (cluster_reliability - 0.5) * 2 * 0.3  # 30% weight to cluster (convert 0-1 to -1 to +1)
        )
        
        # Scale to score adjustment (-10 to +10 points)
        bias_adjustment = combined_bias * 10.0
        
        # Add summary to breakdown
        breakdown['combined_bias'] = round(combined_bias, 3)
        breakdown['bias_adjustment'] = round(bias_adjustment, 2)
        breakdown['cognition_weights'] = {
            'psychology': '30%',
            'regime': '40%',
            'cluster': '30%'
        }
        
        # Overall assessment
        if bias_adjustment > 5:
            breakdown['cognition_verdict'] = '🟢 STRONG BUY - All systems favorable'
        elif bias_adjustment > 2:
            breakdown['cognition_verdict'] = '🟢 BUY - Conditions are good'
        elif bias_adjustment > -2:
            breakdown['cognition_verdict'] = '🟡 NEUTRAL - Mixed signals'
        elif bias_adjustment > -5:
            breakdown['cognition_verdict'] = '🔴 CAUTION - Conditions not ideal'
        else:
            breakdown['cognition_verdict'] = '🔴 AVOID - Multiple risk factors present'
        
        breakdown['cognition_enabled'] = True
        
        return bias_adjustment, breakdown
        
    except Exception as e:
        # If cognition module not available or any error, return neutral
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Cognition bias integration failed: {str(e)}")
        
        return 0.0, {
            'cognition_enabled': False,
            'error': str(e),
            'bias_adjustment': 0.0,
            'cognition_verdict': 'Cognition module unavailable'
        }


def get_cognition_summary(user) -> Dict:
    """
    Get a comprehensive summary of cognition intelligence for a user.
    
    Args:
        user: User object
        
    Returns:
        Dict with cognition summary including psychology, active regimes, and clusters
    """
    try:
        from cognition.models import (
            TraderPsychology, MarketRegime, SignalCluster, 
            PropFirmPrediction, CognitionInsight
        )
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg
        
        summary = {}
        
        # Psychology Summary (last 7 days)
        psych_entries = TraderPsychology.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=7)
        )
        
        if psych_entries.exists():
            avg_sentiment = psych_entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg']
            avg_discipline = psych_entries.aggregate(Avg('discipline_score'))['discipline_score__avg']
            
            # Count biases
            all_biases = []
            for entry in psych_entries:
                all_biases.extend(entry.detected_biases)
            
            from collections import Counter
            bias_counts = Counter(all_biases)
            
            summary['psychology'] = {
                'entry_count': psych_entries.count(),
                'avg_sentiment': round(avg_sentiment or 0, 3),
                'avg_discipline': round(avg_discipline or 0, 2),
                'most_common_biases': dict(bias_counts.most_common(3)),
                'latest_emotional_tone': psych_entries.order_by('-timestamp').first().emotional_tone
            }
        else:
            summary['psychology'] = {'status': 'No psychology data available'}
        
        # Active Market Regimes (last 1 hour, all symbols)
        active_regimes = MarketRegime.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).order_by('-timestamp')
        
        summary['regimes'] = [
            {
                'symbol': regime.symbol,
                'regime_type': regime.regime_type,
                'regime_bias': round(regime.regime_bias, 2),
                'confidence': round(regime.regime_confidence, 2),
                'trend_strength': round(regime.trend_strength, 2),
            }
            for regime in active_regimes[:10]  # Top 10 most recent
        ]
        
        # Top Signal Clusters
        top_clusters = SignalCluster.objects.order_by('-reliability_score')[:5]
        
        summary['top_clusters'] = [
            {
                'cluster_name': cluster.cluster_name,
                'strategy': cluster.strategy_pattern,
                'win_rate': round(cluster.win_rate, 2),
                'reliability': round(cluster.reliability_score, 2),
                'signal_count': cluster.signal_count,
            }
            for cluster in top_clusters
        ]
        
        # Prop Firm Prediction (latest)
        latest_prediction = PropFirmPrediction.objects.filter(
            user=user
        ).order_by('-timestamp').first()
        
        if latest_prediction:
            summary['prop_prediction'] = {
                'challenge_type': latest_prediction.challenge_type,
                'pass_probability': round(latest_prediction.pass_probability, 2),
                'risk_of_failure': round(latest_prediction.risk_of_failure, 2),
                'estimated_days': latest_prediction.estimated_completion_days,
                'status': latest_prediction.get_status_badge()[1],
            }
        else:
            summary['prop_prediction'] = {'status': 'No predictions available'}
        
        # Recent Insights (unread)
        unread_insights = CognitionInsight.objects.filter(
            user=user,
            is_read=False
        ).order_by('-timestamp')[:5]
        
        summary['insights'] = [
            {
                'type': insight.insight_type,
                'title': insight.title,
                'severity': insight.severity,
                'is_actionable': insight.is_actionable,
            }
            for insight in unread_insights
        ]
        
        summary['status'] = 'success'
        summary['generated_at'] = timezone.now().isoformat()
        
        return summary
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
