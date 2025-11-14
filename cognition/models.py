"""
Cognition Module Models
Tracks trader psychology, market regimes, signal clusters, and prop-firm predictions
"""
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TraderPsychology(models.Model):
    """
    Tracks trader emotional state, confidence, and psychological patterns
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psychology_entries')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Source text
    text_content = models.TextField(help_text="Journal entry, chat message, or feedback")
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('journal', 'Trade Journal'),
            ('chat', 'Chat Message'),
            ('feedback', 'Feedback Form'),
            ('note', 'Personal Note'),
        ],
        default='journal'
    )
    
    # Sentiment analysis
    sentiment_score = models.FloatField(
        help_text="Overall sentiment: -1 (very negative) to +1 (very positive)"
    )
    confidence_level = models.FloatField(
        help_text="Trader confidence: 0 (uncertain) to 1 (highly confident)"
    )
    emotional_tone = models.CharField(
        max_length=20,
        choices=[
            ('fearful', 'Fearful'),
            ('anxious', 'Anxious'),
            ('neutral', 'Neutral'),
            ('confident', 'Confident'),
            ('overconfident', 'Overconfident'),
            ('greedy', 'Greedy'),
            ('disciplined', 'Disciplined'),
        ]
    )
    
    # Extracted entities and keywords
    key_phrases = models.JSONField(default=list, help_text="Important phrases extracted")
    entities = models.JSONField(default=dict, help_text="Named entities found (symbols, strategies)")
    
    # Psychological metrics
    risk_tolerance = models.FloatField(
        default=0.5,
        help_text="Implied risk tolerance: 0 (risk-averse) to 1 (risk-seeking)"
    )
    patience_score = models.FloatField(
        default=0.5,
        help_text="Patience level: 0 (impulsive) to 1 (patient)"
    )
    discipline_score = models.FloatField(
        default=0.5,
        help_text="Discipline level: 0 (undisciplined) to 1 (highly disciplined)"
    )
    
    # Bias detection
    detected_biases = models.JSONField(
        default=list,
        help_text="List of cognitive biases detected (e.g., 'overconfidence', 'revenge_trading')"
    )
    bias_severity = models.FloatField(
        default=0.0,
        help_text="Overall bias severity: 0 (minimal) to 1 (severe)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['emotional_tone']),
        ]
        verbose_name_plural = 'Trader Psychology Entries'
    
    def __str__(self):
        return f"{self.user.username} - {self.emotional_tone} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_psychological_bias_score(self):
        """
        Calculate overall psychological bias for AI scoring
        Returns: -1 (negative bias) to +1 (positive bias)
        """
        # Combine sentiment, confidence, and bias severity
        confidence_penalty = 0
        if self.emotional_tone == 'overconfident':
            confidence_penalty = -0.3
        elif self.emotional_tone == 'fearful':
            confidence_penalty = -0.2
        
        bias_penalty = -self.bias_severity * 0.5
        
        return max(-1, min(1, self.sentiment_score + confidence_penalty + bias_penalty))


class MarketRegime(models.Model):
    """
    Classifies current market state for adaptive strategy selection
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(
        max_length=10,
        choices=[
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('4h', '4 Hours'),
            ('1d', '1 Day'),
        ],
        default='15m'
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Regime classification
    regime_type = models.CharField(
        max_length=20,
        choices=[
            ('strong_trend', 'Strong Trend'),
            ('weak_trend', 'Weak Trend'),
            ('choppy', 'Choppy/Range-bound'),
            ('squeeze', 'Squeeze/Consolidation'),
            ('volatile', 'High Volatility'),
            ('quiet', 'Low Volatility'),
        ],
        db_index=True
    )
    regime_confidence = models.FloatField(
        help_text="Confidence in regime classification: 0 to 1"
    )
    
    # Market characteristics
    trend_strength = models.FloatField(
        help_text="ADX-based trend strength: 0 (no trend) to 1 (strong trend)"
    )
    volatility_percentile = models.FloatField(
        help_text="Current volatility vs 30-day range: 0 (low) to 1 (high)"
    )
    volume_profile = models.FloatField(
        help_text="Volume relative to average: 0 (low) to 2+ (high)"
    )
    
    # Detected patterns
    detected_patterns = models.JSONField(
        default=list,
        help_text="Technical patterns detected (e.g., 'higher_highs', 'range_bound')"
    )
    
    # Statistical features (for ML)
    feature_vector = models.JSONField(
        default=dict,
        help_text="Numerical features used for classification"
    )
    
    # Recommended bias
    regime_bias = models.FloatField(
        default=0.0,
        help_text="Trading bias: -1 (avoid), 0 (neutral), +1 (favorable)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'timestamp']),
            models.Index(fields=['regime_type']),
        ]
        unique_together = [['symbol', 'timeframe', 'timestamp']]
    
    def __str__(self):
        return f"{self.symbol} {self.timeframe} - {self.regime_type} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_regime_bias_score(self):
        """
        Calculate regime appropriateness for trading
        """
        if self.regime_type in ['strong_trend', 'weak_trend']:
            return self.trend_strength * self.regime_confidence
        elif self.regime_type in ['choppy', 'squeeze']:
            return -0.5 * self.regime_confidence  # Penalize choppy markets
        elif self.regime_type == 'volatile':
            return -0.3 if self.volatility_percentile > 0.8 else 0.2
        return 0.0


class SignalCluster(models.Model):
    """
    Groups similar trading signals and tracks their performance
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cluster_id = models.IntegerField(db_index=True, help_text="ML-assigned cluster ID")
    cluster_name = models.CharField(
        max_length=50,
        help_text="Human-readable cluster name (e.g., 'Morning Breakouts')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Cluster characteristics
    strategy_pattern = models.CharField(
        max_length=100,
        help_text="Dominant strategy pattern in this cluster"
    )
    typical_timeframe = models.CharField(max_length=10)
    typical_symbols = models.JSONField(default=list, help_text="Common symbols in cluster")
    
    # Performance metrics
    signal_count = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.5)
    avg_profit_factor = models.FloatField(default=1.0)
    avg_risk_reward = models.FloatField(default=1.5)
    sharpe_ratio = models.FloatField(default=0.0)
    
    # Cluster features (centroid)
    feature_centroid = models.JSONField(
        default=dict,
        help_text="Average feature vector for this cluster"
    )
    
    # Reliability scoring
    reliability_score = models.FloatField(
        default=0.5,
        help_text="Overall cluster reliability: 0 (unreliable) to 1 (highly reliable)"
    )
    confidence_interval = models.FloatField(
        default=0.95,
        help_text="Statistical confidence in performance metrics"
    )
    
    # Market condition preferences
    preferred_regimes = models.JSONField(
        default=list,
        help_text="Regimes where this cluster performs best"
    )
    
    class Meta:
        ordering = ['-reliability_score']
        indexes = [
            models.Index(fields=['cluster_id']),
            models.Index(fields=['reliability_score']),
        ]
    
    def __str__(self):
        return f"Cluster {self.cluster_id}: {self.cluster_name} (Reliability: {self.reliability_score:.2f})"
    
    def get_cluster_reliability_score(self):
        """
        Calculate reliability for AI scoring adjustment
        """
        # Weight multiple factors
        performance_score = (
            self.win_rate * 0.4 +
            min(self.avg_profit_factor / 2, 1.0) * 0.3 +
            min(self.sharpe_ratio / 2, 1.0) * 0.3
        )
        
        # Confidence penalty for small sample sizes
        sample_penalty = min(self.signal_count / 100, 1.0)
        
        return performance_score * sample_penalty * self.confidence_interval


class PropFirmPrediction(models.Model):
    """
    Predicts likelihood of passing prop firm challenge based on trading metrics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prop_predictions')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Challenge parameters
    challenge_type = models.CharField(
        max_length=20,
        choices=[
            ('phase1', 'Phase 1 Challenge'),
            ('phase2', 'Phase 2 Challenge'),
            ('funded', 'Funded Account'),
        ],
        default='phase1'
    )
    account_size = models.DecimalField(max_digits=12, decimal_places=2)
    profit_target = models.DecimalField(max_digits=12, decimal_places=2)
    max_drawdown = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Current metrics
    current_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    days_remaining = models.IntegerField(default=30)
    trades_taken = models.IntegerField(default=0)
    
    # Performance indicators
    current_win_rate = models.FloatField(default=0.5)
    current_profit_factor = models.FloatField(default=1.0)
    current_sharpe = models.FloatField(default=0.0)
    avg_trade_duration = models.FloatField(default=0.0, help_text="Hours")
    
    # Psychological indicators
    avg_confidence_score = models.FloatField(default=0.5)
    avg_discipline_score = models.FloatField(default=0.5)
    recent_bias_severity = models.FloatField(default=0.0)
    
    # Prediction outputs
    pass_probability = models.FloatField(
        help_text="Predicted probability of passing challenge: 0 to 1"
    )
    estimated_completion_days = models.IntegerField(
        help_text="Estimated days to hit profit target"
    )
    risk_of_failure = models.FloatField(
        help_text="Probability of hitting max drawdown: 0 to 1"
    )
    
    # Recommendations
    recommended_adjustments = models.JSONField(
        default=list,
        help_text="Suggested changes to improve pass probability"
    )
    confidence_level = models.FloatField(
        default=0.7,
        help_text="Confidence in prediction: 0 to 1"
    )
    
    # Feature vector for ML
    feature_vector = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['pass_probability']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge_type}: {self.pass_probability:.1%} pass rate"
    
    def get_status_badge(self):
        """Return color-coded status"""
        if self.pass_probability >= 0.7:
            return 'success', 'High Confidence'
        elif self.pass_probability >= 0.4:
            return 'warning', 'Moderate Risk'
        else:
            return 'danger', 'High Risk'


class CognitionInsight(models.Model):
    """
    Stores generated insights and summaries from cognition analysis
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    insight_type = models.CharField(
        max_length=30,
        choices=[
            ('daily_summary', 'Daily Summary'),
            ('psychology_alert', 'Psychology Alert'),
            ('regime_change', 'Regime Change'),
            ('cluster_insight', 'Cluster Insight'),
            ('prop_warning', 'Prop Firm Warning'),
        ],
        db_index=True
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Information'),
            ('success', 'Success'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ],
        default='info'
    )
    
    # Related data
    related_data = models.JSONField(default=dict)
    
    # Action tracking
    is_read = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['insight_type']),
        ]
    
    def __str__(self):
        return f"{self.insight_type}: {self.title}"
