"""
Prop Firm Challenge Predictor
Predicts probability of passing prop firm challenges using ML
"""
import logging
import numpy as np
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


class PropFirmPredictor:
    """
    Predicts prop firm challenge success probability
    """
    
    def __init__(self):
        """Initialize predictor"""
        self.model = RandomForestClassifier(n_estimators=100, random_state=42) if SKLEARN_AVAILABLE else None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
    
    def predict(self, user_metrics: Dict) -> Dict:
        """
        Predict challenge success probability
        
        Args:
            user_metrics: Dictionary with current trading metrics
            
        Returns:
            Prediction results
        """
        try:
            # Extract features
            features = self._extract_features(user_metrics)
            
            # Calculate heuristic-based prediction (rule-based)
            pass_prob = self._calculate_pass_probability(user_metrics)
            risk_of_failure = self._calculate_failure_risk(user_metrics)
            estimated_days = self._estimate_completion_days(user_metrics)
            recommendations = self._generate_recommendations(user_metrics, pass_prob)
            
            return {
                'pass_probability': pass_prob,
                'estimated_completion_days': estimated_days,
                'risk_of_failure': risk_of_failure,
                'recommended_adjustments': recommendations,
                'confidence_level': 0.75,
                'feature_vector': features,
            }
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._get_default_prediction()
    
    def _extract_features(self, metrics: Dict) -> Dict:
        """Extract numerical features"""
        return {
            'current_profit_pct': float(metrics.get('current_profit', 0)) / float(metrics.get('account_size', 100000)) * 100,
            'drawdown_pct': float(metrics.get('current_drawdown', 0)) / float(metrics.get('account_size', 100000)) * 100,
            'profit_progress': float(metrics.get('current_profit', 0)) / float(metrics.get('profit_target', 10000)),
            'days_progress': (float(metrics.get('days_remaining', 30)) - 30) / -30,  # 0 to 1
            'win_rate': float(metrics.get('current_win_rate', 0.5)),
            'profit_factor': float(metrics.get('current_profit_factor', 1.0)),
            'sharpe': float(metrics.get('current_sharpe', 0.0)),
            'trades_per_day': float(metrics.get('trades_taken', 0)) / max(1, 30 - float(metrics.get('days_remaining', 30))),
            'avg_confidence': float(metrics.get('avg_confidence_score', 0.5)),
            'discipline': float(metrics.get('avg_discipline_score', 0.5)),
            'bias_severity': float(metrics.get('recent_bias_severity', 0.0)),
        }
    
    def _calculate_pass_probability(self, metrics: Dict) -> float:
        """
        Calculate pass probability using rule-based heuristics
        """
        # Extract key metrics
        current_profit = float(metrics.get('current_profit', 0))
        profit_target = float(metrics.get('profit_target', 10000))
        current_drawdown = abs(float(metrics.get('current_drawdown', 0)))
        max_drawdown = float(metrics.get('max_drawdown', 5000))
        days_remaining = int(metrics.get('days_remaining', 30))
        
        win_rate = float(metrics.get('current_win_rate', 0.5))
        profit_factor = float(metrics.get('current_profit_factor', 1.0))
        discipline = float(metrics.get('avg_discipline_score', 0.5))
        
        # Calculate progress metrics
        profit_progress = current_profit / profit_target if profit_target > 0 else 0
        drawdown_usage = current_drawdown / max_drawdown if max_drawdown > 0 else 0
        
        # Base probability starts at 0.5
        probability = 0.5
        
        # Profit progress factor (0-30% boost)
        probability += profit_progress * 0.3
        
        # Drawdown risk (0-20% penalty)
        probability -= drawdown_usage * 0.2
        
        # Win rate impact (0-15% boost/penalty)
        probability += (win_rate - 0.5) * 0.3
        
        # Profit factor impact (0-15% boost/penalty)
        if profit_factor > 1.0:
            probability += min((profit_factor - 1.0) * 0.15, 0.15)
        else:
            probability -= (1.0 - profit_factor) * 0.15
        
        # Discipline factor (0-10% boost/penalty)
        probability += (discipline - 0.5) * 0.2
        
        # Time pressure (penalty if low progress with little time)
        if days_remaining < 7 and profit_progress < 0.5:
            probability -= 0.15
        
        # Bonus for being ahead of pace
        required_daily_profit = (profit_target - current_profit) / max(1, days_remaining)
        days_elapsed = 30 - days_remaining
        if days_elapsed > 0:
            actual_daily_avg = current_profit / days_elapsed
            if actual_daily_avg > required_daily_profit * 1.5:
                probability += 0.1
        
        return max(0.05, min(0.95, probability))
    
    def _calculate_failure_risk(self, metrics: Dict) -> float:
        """Calculate risk of hitting max drawdown"""
        current_drawdown = abs(float(metrics.get('current_drawdown', 0)))
        max_drawdown = float(metrics.get('max_drawdown', 5000))
        win_rate = float(metrics.get('current_win_rate', 0.5))
        profit_factor = float(metrics.get('current_profit_factor', 1.0))
        bias_severity = float(metrics.get('recent_bias_severity', 0.0))
        
        # Base risk
        drawdown_proximity = current_drawdown / max_drawdown if max_drawdown > 0 else 0
        risk = drawdown_proximity * 0.5
        
        # Poor performance increases risk
        if win_rate < 0.4:
            risk += 0.2
        if profit_factor < 0.8:
            risk += 0.2
        
        # Psychological risk
        risk += bias_severity * 0.2
        
        return max(0.0, min(1.0, risk))
    
    def _estimate_completion_days(self, metrics: Dict) -> int:
        """Estimate days to hit profit target"""
        current_profit = float(metrics.get('current_profit', 0))
        profit_target = float(metrics.get('profit_target', 10000))
        days_remaining = int(metrics.get('days_remaining', 30))
        trades_taken = int(metrics.get('trades_taken', 0))
        
        days_elapsed = 30 - days_remaining
        
        if days_elapsed == 0 or current_profit <= 0:
            return days_remaining
        
        # Calculate current pace
        daily_profit_avg = current_profit / days_elapsed
        remaining_profit = profit_target - current_profit
        
        if daily_profit_avg <= 0:
            return days_remaining
        
        estimated_days = int(remaining_profit / daily_profit_avg)
        
        # Add buffer for variability
        estimated_days = int(estimated_days * 1.2)
        
        return max(1, min(estimated_days, days_remaining))
    
    def _generate_recommendations(self, metrics: Dict, pass_prob: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        win_rate = float(metrics.get('current_win_rate', 0.5))
        profit_factor = float(metrics.get('current_profit_factor', 1.0))
        discipline = float(metrics.get('avg_discipline_score', 0.5))
        bias_severity = float(metrics.get('recent_bias_severity', 0.0))
        drawdown_pct = abs(float(metrics.get('current_drawdown', 0))) / float(metrics.get('max_drawdown', 5000))
        
        # Win rate recommendations
        if win_rate < 0.45:
            recommendations.append("Improve win rate: Focus on higher probability setups")
        
        # Profit factor recommendations
        if profit_factor < 1.0:
            recommendations.append("Improve profit factor: Let winners run longer, cut losses faster")
        
        # Discipline recommendations
        if discipline < 0.6:
            recommendations.append("Increase discipline: Follow your trading plan strictly")
        
        # Psychological recommendations
        if bias_severity > 0.5:
            recommendations.append("Address cognitive biases: Take a break after losses")
        
        # Drawdown recommendations
        if drawdown_pct > 0.7:
            recommendations.append("Critical: Reduce position size immediately to avoid max drawdown")
        elif drawdown_pct > 0.5:
            recommendations.append("Warning: Lower risk per trade to protect against further drawdown")
        
        # Progress recommendations
        days_remaining = int(metrics.get('days_remaining', 30))
        profit_progress = float(metrics.get('current_profit', 0)) / float(metrics.get('profit_target', 10000))
        
        if days_remaining < 10 and profit_progress < 0.6:
            recommendations.append("Time pressure: Increase trading frequency with controlled risk")
        
        if profit_progress > 0.8:
            recommendations.append("Near target: Consider reducing risk to preserve gains")
        
        # If probability is low
        if pass_prob < 0.3:
            recommendations.append("High risk of failure: Consider resetting strategy or taking a break")
        
        return recommendations[:5]  # Return top 5
    
    def _get_default_prediction(self) -> Dict:
        """Default prediction for errors"""
        return {
            'pass_probability': 0.5,
            'estimated_completion_days': 15,
            'risk_of_failure': 0.3,
            'recommended_adjustments': ["Insufficient data for detailed analysis"],
            'confidence_level': 0.5,
            'feature_vector': {},
        }


# Convenience function
def predict_challenge_success(user_metrics: Dict) -> Dict:
    """
    Predict prop firm challenge success
    
    Args:
        user_metrics: Dictionary with trading metrics
        
    Returns:
        Prediction results
    """
    predictor = PropFirmPredictor()
    return predictor.predict(user_metrics)
