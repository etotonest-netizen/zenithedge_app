"""
Zenith Market Analyst - Insight Scoring System

Calculates Insight Index (0-100) based on:
- Structure clarity
- Regime stability
- Volume quality
- Momentum alignment
- Session validity
- Risk level

NO external APIs - pure mathematical scoring
"""
from typing import Dict, Any, Tuple
from datetime import datetime, time


class InsightScorer:
    """
    Calculate comprehensive insight quality scores
    """
    
    def __init__(self):
        # Scoring weights (total = 100)
        self.weights = {
            'structure_clarity': 25,
            'regime_stability': 20,
            'volume_quality': 15,
            'momentum_alignment': 15,
            'session_validity': 15,
            'risk_level': 10,  # Inverted - lower risk = higher score
        }
    
    def calculate_insight_index(self, metadata: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
        """
        Calculate overall Insight Index (0-100) and component scores
        
        Returns:
            (total_score, breakdown_dict)
        """
        # Calculate individual components
        structure_clarity = self._score_structure_clarity(metadata)
        regime_stability = self._score_regime_stability(metadata)
        volume_quality = self._score_volume_quality(metadata)
        momentum_alignment = self._score_momentum_alignment(metadata)
        session_validity = self._score_session_validity(metadata)
        risk_level = self._score_risk_level(metadata)
        
        # Weighted sum
        total = (
            structure_clarity * self.weights['structure_clarity'] +
            regime_stability * self.weights['regime_stability'] +
            volume_quality * self.weights['volume_quality'] +
            momentum_alignment * self.weights['momentum_alignment'] +
            session_validity * self.weights['session_validity'] +
            risk_level * self.weights['risk_level']
        ) / 100
        
        breakdown = {
            'structure_clarity': structure_clarity,
            'regime_stability': regime_stability,
            'volume_quality': volume_quality,
            'momentum_alignment': momentum_alignment,
            'session_validity': session_validity,
            'risk_level': risk_level,
        }
        
        return int(total), breakdown
    
    def _score_structure_clarity(self, metadata: Dict[str, Any]) -> int:
        """
        Score structural clarity (0-100)
        
        Higher score = clearer, more actionable structure
        """
        structure = metadata.get('structure', 'none')
        strength = metadata.get('strength', 0)
        
        # Base score by structure type
        structure_scores = {
            'bos': 95,           # Very clear directional signal
            'choch': 85,         # Strong reversal indication
            'order_block': 80,   # Clear institutional zone
            'liquidity_sweep': 75,  # Engineered move identified
            'fvg': 70,           # Imbalance zone
            'pullback': 65,      # Retracement phase
            'eqh': 60,           # Equal highs/lows
            'eql': 60,
            'compression': 50,   # Pre-breakout state
            'none': 20,          # No clear structure
        }
        
        base_score = structure_scores.get(structure, 20)
        
        # Adjust by strength
        strength_adjustment = (strength - 50) * 0.3  # -15 to +15
        
        final_score = base_score + strength_adjustment
        
        return max(0, min(100, int(final_score)))
    
    def _score_regime_stability(self, metadata: Dict[str, Any]) -> int:
        """
        Score regime clarity and stability (0-100)
        
        Higher score = more predictable, stable regime
        """
        regime = metadata.get('regime', 'unknown')
        expected_behavior = metadata.get('expected_behavior', '').lower()
        
        # Base regime scores
        regime_scores = {
            'trending': 90,      # Most predictable
            'consolidation': 70, # Accumulation/distribution
            'ranging': 60,       # Defined boundaries
            'volatile': 30,      # Unstable
            'unknown': 10,       # No regime identified
        }
        
        base_score = regime_scores.get(regime, 10)
        
        # Boost if expected behavior aligns with regime
        alignment_boost = 0
        if regime == 'trending' and 'expansion' in expected_behavior:
            alignment_boost = 10
        elif regime == 'ranging' and 'reversion' in expected_behavior:
            alignment_boost = 10
        elif regime == 'consolidation' and 'breakout' in expected_behavior:
            alignment_boost = 15
        
        final_score = base_score + alignment_boost
        
        return max(0, min(100, int(final_score)))
    
    def _score_volume_quality(self, metadata: Dict[str, Any]) -> int:
        """
        Score volume conditions (0-100)
        
        Higher score = volume supports current price action
        """
        volume_state = metadata.get('volume_state', 'normal')
        structure = metadata.get('structure', 'none')
        momentum = metadata.get('momentum', 'neutral')
        
        # Base volume scores
        volume_scores = {
            'spike': 80,   # High participation
            'normal': 60,  # Average conditions
            'drop': 30,    # Thin liquidity
        }
        
        base_score = volume_scores.get(volume_state, 60)
        
        # Context adjustments
        adjustment = 0
        
        # Volume spike during breakout = excellent
        if volume_state == 'spike' and structure in ['bos', 'choch']:
            adjustment += 15
        
        # Volume spike with strong momentum = good
        elif volume_state == 'spike' and momentum in ['increasing', 'decreasing']:
            adjustment += 10
        
        # Low volume during pullback = acceptable
        elif volume_state == 'drop' and structure == 'pullback':
            adjustment += 15
        
        # Low volume during breakout = warning
        elif volume_state == 'drop' and structure in ['bos', 'choch']:
            adjustment -= 20
        
        final_score = base_score + adjustment
        
        return max(0, min(100, int(final_score)))
    
    def _score_momentum_alignment(self, metadata: Dict[str, Any]) -> int:
        """
        Score momentum clarity and alignment (0-100)
        
        Higher score = momentum supports structure and regime
        """
        momentum = metadata.get('momentum', 'neutral')
        structure = metadata.get('structure', 'none')
        regime = metadata.get('regime', 'unknown')
        
        # Base momentum scores
        momentum_scores = {
            'increasing': 75,  # Clear directional momentum
            'decreasing': 75,  # Clear directional momentum
            'diverging': 85,   # High-value signal
            'neutral': 40,     # No clear momentum
        }
        
        base_score = momentum_scores.get(momentum, 40)
        
        # Alignment bonuses
        alignment = 0
        
        # Divergence is always valuable
        if momentum == 'diverging':
            alignment += 10
        
        # Momentum aligns with trending regime
        elif regime == 'trending' and momentum in ['increasing', 'decreasing']:
            alignment += 15
        
        # Neutral momentum in ranging regime is acceptable
        elif regime == 'ranging' and momentum == 'neutral':
            alignment += 10
        
        # Momentum supports structure break
        elif structure == 'bos' and momentum in ['increasing', 'decreasing']:
            alignment += 10
        
        final_score = base_score + alignment
        
        return max(0, min(100, int(final_score)))
    
    def _score_session_validity(self, metadata: Dict[str, Any]) -> int:
        """
        Score session quality (0-100)
        
        Higher score = better liquidity and participation
        """
        session = metadata.get('session', 'off')
        timestamp = metadata.get('timestamp')
        
        # Base session scores
        session_scores = {
            'london': 90,    # High liquidity
            'newyork': 95,   # Highest liquidity
            'asia': 70,      # Moderate liquidity
            'off': 30,       # Low liquidity
        }
        
        base_score = session_scores.get(session, 30)
        
        # Time-based adjustments
        if timestamp:
            hour = timestamp.hour if isinstance(timestamp, datetime) else None
            
            if hour is not None:
                # Peak hours boost
                if session == 'london' and 8 <= hour < 12:  # London morning
                    base_score += 5
                elif session == 'newyork' and 13 <= hour < 16:  # NY afternoon
                    base_score += 5
                
                # Overlap boost (London-NY overlap is 12:00-16:00 UTC)
                if 12 <= hour < 16:
                    base_score += 10
        
        return max(0, min(100, int(base_score)))
    
    def _score_risk_level(self, metadata: Dict[str, Any]) -> int:
        """
        Score risk level (0-100)
        
        INVERTED: Higher score = lower risk
        Lower score = higher risk
        """
        risk_notes = metadata.get('risk_notes', [])
        regime = metadata.get('regime', 'unknown')
        volume_state = metadata.get('volume_state', 'normal')
        
        # Start at 100 (no risk)
        score = 100
        
        # Deduct for each risk factor
        risk_penalties = {
            'high volatility': 20,
            'news risk': 25,
            'no clean structure': 15,
            'spread risk': 10,
            'liquidity risk': 15,
            'whipsaw risk': 20,
        }
        
        for note in risk_notes:
            note_lower = note.lower()
            for risk_key, penalty in risk_penalties.items():
                if risk_key in note_lower:
                    score -= penalty
                    break
        
        # Additional contextual risks
        if regime == 'volatile':
            score -= 15
        
        if volume_state == 'drop':
            score -= 10
        
        return max(0, min(100, score))
    
    def get_quality_label(self, insight_index: int) -> str:
        """
        Convert numerical score to quality label
        """
        if insight_index >= 80:
            return "Exceptional"
        elif insight_index >= 65:
            return "High Quality"
        elif insight_index >= 50:
            return "Moderate"
        elif insight_index >= 35:
            return "Low Quality"
        else:
            return "Poor"
    
    def get_color_code(self, insight_index: int) -> str:
        """
        Get color code for UI display based on score
        """
        if insight_index >= 80:
            return "#10b981"  # Green
        elif insight_index >= 65:
            return "#3b82f6"  # Blue
        elif insight_index >= 50:
            return "#f59e0b"  # Amber
        elif insight_index >= 35:
            return "#ef4444"  # Red
        else:
            return "#6b7280"  # Gray
    
    def generate_score_explanation(self, breakdown: Dict[str, int]) -> str:
        """
        Generate human-readable explanation of score components
        """
        components = []
        
        for component, score in breakdown.items():
            label = component.replace('_', ' ').title()
            
            if score >= 80:
                quality = "excellent"
            elif score >= 60:
                quality = "good"
            elif score >= 40:
                quality = "moderate"
            else:
                quality = "weak"
            
            components.append(f"{label}: {quality} ({score}/100)")
        
        return " • ".join(components)
