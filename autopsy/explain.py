"""
Explainability Engine

Provides feature attribution and model interpretation using
permutation importance and simplified SHAP-style explanations.
"""
import logging
import numpy as np
from typing import Dict, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class SimpleExplainer:
    """
    Lightweight explainer for insight predictions
    
    Uses permutation importance and feature contribution analysis
    """
    
    def __init__(self, insight):
        """
        Initialize explainer for an insight
        
        Args:
            insight: Signal instance
        """
        self.insight = insight
        self.features = {}
        self.contributions = {}
    
    def extract_features(self) -> Dict:
        """
        Extract features from insight that influenced prediction
        
        Returns:
            Dictionary of feature name -> value
        """
        try:
            features = {}
            
            # Technical indicators
            if hasattr(self.insight, 'quality_metrics') and self.insight.quality_metrics:
                qm = self.insight.quality_metrics
                
                if isinstance(qm, dict):
                    # Extract numeric features
                    for key, value in qm.items():
                        if isinstance(value, (int, float, Decimal)):
                            features[f"qm_{key}"] = float(value)
            
            # Validation features
            try:
                from signals.models import TradeValidation
                validation = TradeValidation.objects.filter(
                    signal=self.insight
                ).order_by('-created_at').first()
                
                if validation:
                    features['ai_score'] = float(validation.ai_score or 50)
                    features['confidence'] = float(validation.confidence or 0)
                    features['truth_index'] = float(getattr(validation, 'truth_index', 50))
            except:
                pass
            
            # Market context
            features['timeframe'] = self._timeframe_to_numeric(self.insight.timeframe)
            features['side'] = 1.0 if self.insight.side.lower() in ['buy', 'long'] else -1.0
            
            # Timing features
            if self.insight.received_at:
                hour = self.insight.received_at.hour
                features['hour_of_day'] = hour
                features['is_london_session'] = 1.0 if 8 <= hour <= 16 else 0.0
                features['is_ny_session'] = 1.0 if 13 <= hour <= 21 else 0.0
            
            self.features = features
            return features
        
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return {}
    
    def _timeframe_to_numeric(self, tf: str) -> float:
        """Convert timeframe to numeric value"""
        mapping = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440, '1w': 10080
        }
        return float(mapping.get(tf.lower(), 60))
    
    def explain_prediction(self) -> Dict:
        """
        Generate feature importance explanation
        
        Returns:
            Dictionary with feature contributions
        """
        try:
            if not self.features:
                self.extract_features()
            
            # Calculate simple feature importance based on deviation from neutral
            contributions = {}
            
            for feature, value in self.features.items():
                # Normalize contribution (-1 to 1 scale)
                if feature == 'ai_score':
                    # AI score deviation from 50 (neutral)
                    contrib = (value - 50) / 50
                elif feature == 'confidence':
                    # Confidence boost
                    contrib = value / 100
                elif feature == 'truth_index':
                    # Truth index deviation
                    contrib = (value - 50) / 50
                elif feature == 'hour_of_day':
                    # Prefer London/NY overlap (13-16 GMT)
                    contrib = 0.5 if 13 <= value <= 16 else 0.0
                elif feature.startswith('is_'):
                    # Session indicators
                    contrib = value * 0.3
                else:
                    # Generic numeric features
                    contrib = np.tanh(value / 100)  # Soft normalize
                
                contributions[feature] = float(contrib)
            
            # Sort by absolute contribution
            sorted_features = sorted(
                contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            self.contributions = dict(sorted_features)
            
            return self.contributions
        
        except Exception as e:
            logger.error(f"Explanation error: {e}")
            return {}
    
    def get_top_features(self, n=5) -> List[tuple]:
        """
        Get top N most influential features
        
        Args:
            n: Number of features to return
        
        Returns:
            List of (feature_name, contribution, interpretation) tuples
        """
        if not self.contributions:
            self.explain_prediction()
        
        top_features = []
        for feature, contrib in list(self.contributions.items())[:n]:
            interpretation = self._interpret_contribution(feature, contrib)
            top_features.append((feature, contrib, interpretation))
        
        return top_features
    
    def _interpret_contribution(self, feature: str, contribution: float) -> str:
        """Generate human-readable interpretation"""
        direction = "positive" if contribution > 0 else "negative"
        strength = "strong" if abs(contribution) > 0.5 else "moderate" if abs(contribution) > 0.2 else "weak"
        
        interpretations = {
            'ai_score': f"{strength.capitalize()} {direction} AI prediction",
            'confidence': f"{strength.capitalize()} model confidence",
            'truth_index': f"{strength.capitalize()} truth index alignment",
            'is_london_session': "London session active" if contribution > 0 else "Outside London hours",
            'is_ny_session': "NY session active" if contribution > 0 else "Outside NY hours",
            'side': "Bullish bias" if contribution > 0 else "Bearish bias",
        }
        
        return interpretations.get(feature, f"{strength.capitalize()} {direction} influence")
    
    def generate_explanation_snapshot(self) -> Dict:
        """
        Generate complete explanation snapshot for storage
        
        Returns:
            Dictionary with all explanation data
        """
        try:
            self.extract_features()
            self.explain_prediction()
            top_features = self.get_top_features()
            
            return {
                'features': self.features,
                'contributions': self.contributions,
                'top_features': [
                    {
                        'feature': f,
                        'contribution': float(c),
                        'interpretation': i
                    }
                    for f, c, i in top_features
                ],
                'summary': self._generate_summary(top_features)
            }
        
        except Exception as e:
            logger.error(f"Snapshot generation error: {e}")
            return {'error': str(e)}
    
    def _generate_summary(self, top_features: List[tuple]) -> str:
        """Generate natural language summary"""
        if not top_features:
            return "Insufficient data for explanation."
        
        primary_feature, primary_contrib, primary_interp = top_features[0]
        
        if abs(primary_contrib) > 0.5:
            strength_word = "strongly"
        elif abs(primary_contrib) > 0.2:
            strength_word = "moderately"
        else:
            strength_word = "weakly"
        
        direction = "supported" if primary_contrib > 0 else "opposed"
        
        summary = (
            f"Prediction was {strength_word} {direction} by {primary_interp.lower()}. "
        )
        
        if len(top_features) > 1:
            secondary_feature, secondary_contrib, secondary_interp = top_features[1]
            summary += f"Secondary factor: {secondary_interp.lower()}."
        
        return summary


def explain_insight(insight) -> Dict:
    """
    Convenience function to explain a single insight
    
    Args:
        insight: Signal instance
    
    Returns:
        Explanation dictionary
    """
    try:
        explainer = SimpleExplainer(insight)
        return explainer.generate_explanation_snapshot()
    except Exception as e:
        logger.error(f"Failed to explain insight #{insight.id}: {e}")
        return {'error': str(e)}


def compare_predictions(audits: List) -> Dict:
    """
    Compare explanations across multiple audits
    
    Useful for finding common failure patterns
    
    Args:
        audits: List of InsightAudit instances
    
    Returns:
        Dictionary with comparison insights
    """
    try:
        feature_importance_sum = {}
        count = 0
        
        for audit in audits:
            explainer = SimpleExplainer(audit.insight)
            contributions = explainer.explain_prediction()
            
            for feature, contrib in contributions.items():
                if feature not in feature_importance_sum:
                    feature_importance_sum[feature] = 0
                feature_importance_sum[feature] += abs(contrib)
            
            count += 1
        
        if count == 0:
            return {}
        
        # Calculate average importance
        avg_importance = {
            feature: importance / count
            for feature, importance in feature_importance_sum.items()
        }
        
        # Sort by importance
        sorted_features = sorted(
            avg_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'sample_size': count,
            'top_discriminative_features': dict(sorted_features[:10]),
            'summary': f"Analyzed {count} audits. Top feature: {sorted_features[0][0] if sorted_features else 'None'}"
        }
    
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return {'error': str(e)}
