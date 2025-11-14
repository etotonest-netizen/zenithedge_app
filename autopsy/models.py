"""
AutopsyLoop Database Models

Automated retrospective auditing system that evaluates insight outcomes,
performs root-cause analysis, and feeds learnings back into the platform.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

User = get_user_model()


class OutcomeChoices(models.TextChoices):
    """Outcome labels for insights after real-world evaluation"""
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    NEUTRAL = 'neutral', 'Neutral'
    FILTERED_OUT = 'filtered_out', 'Filtered Out'
    PENDING = 'pending', 'Pending Evaluation'
    NEEDS_REVIEW = 'needs_review', 'Needs Manual Review'


class RCACauseChoices(models.TextChoices):
    """Root cause categories for insight failures"""
    MODEL_ERROR = 'model_error', 'Model Error'
    REGIME_DRIFT = 'regime_drift', 'Regime Drift'
    NEWS_SHOCK = 'news_shock', 'News Shock'
    LIQUIDITY_EVENT = 'liquidity_event', 'Liquidity Event'
    DETECTOR_MISIDENTIFICATION = 'detector_misid', 'Detector Mis-identification'
    USER_PSYCHOLOGY = 'user_psychology', 'User Psychology Effect'
    VOLATILITY_SPIKE = 'volatility_spike', 'Volatility Spike'
    SPREAD_SLIPPAGE = 'spread_slippage', 'Spread/Slippage'
    FALSE_POSITIVE = 'false_positive', 'False Positive Pattern'
    EXTERNAL_SHOCK = 'external_shock', 'External Market Shock'
    UNKNOWN = 'unknown', 'Unknown'


class JobStatusChoices(models.TextChoices):
    """Status for autopsy jobs"""
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class RetrainStatusChoices(models.TextChoices):
    """Status for retrain requests"""
    REQUESTED = 'requested', 'Requested'
    SIMULATING = 'simulating', 'Simulating Uplift'
    PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    TRAINING = 'training', 'Training'
    COMPLETED = 'completed', 'Completed'
    REJECTED = 'rejected', 'Rejected'
    ROLLED_BACK = 'rolled_back', 'Rolled Back'


class InsightAudit(models.Model):
    """
    Complete audit record for an insight with outcome evaluation
    
    Stores real-world results, performance metrics, and evaluation metadata
    """
    # Core relationships
    insight = models.ForeignKey('signals.Signal', on_delete=models.CASCADE, related_name='audits')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Evaluation metadata
    evaluated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    horizon = models.CharField(max_length=10, help_text="Evaluation timeframe (1H, 4H, 24H, 7D)")
    outcome = models.CharField(max_length=20, choices=OutcomeChoices.choices, default=OutcomeChoices.PENDING, db_index=True)
    
    # Performance metrics
    pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, 
                                    help_text="Realized P&L percentage")
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True,
                                        help_text="Maximum adverse move during evaluation")
    duration_minutes = models.IntegerField(null=True, blank=True, help_text="Time to outcome")
    
    # Price action details
    entry_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    high_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    low_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    
    # Risk metrics
    risk_reward_actual = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    slippage_pips = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Flags
    user_acted = models.BooleanField(default=False, help_text="User actually took this trade")
    replay_verified = models.BooleanField(default=False, help_text="Pattern re-detected in replay")
    needs_manual_review = models.BooleanField(default=False, db_index=True)
    
    # Human review
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='audits_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)
    
    # Raw data snapshot (for reproducibility)
    replay_snapshot = models.JSONField(default=dict, help_text="OHLCV data at evaluation time")
    config_snapshot = models.JSONField(default=dict, help_text="Labeling rules used")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'autopsy_insightaudit'
        ordering = ['-evaluated_at']
        indexes = [
            models.Index(fields=['insight', 'horizon']),
            models.Index(fields=['outcome', '-evaluated_at']),
            models.Index(fields=['user', '-evaluated_at']),
            models.Index(fields=['needs_manual_review', '-evaluated_at']),
        ]
        verbose_name = 'Insight Audit'
        verbose_name_plural = 'Insight Audits'
    
    def __str__(self):
        return f"Audit #{self.id} - {self.insight.symbol} {self.outcome} ({self.horizon})"
    
    def get_success_rate_context(self):
        """Get success rate for similar insights"""
        similar = InsightAudit.objects.filter(
            insight__symbol=self.insight.symbol,
            insight__timeframe=self.insight.timeframe,
            horizon=self.horizon
        ).exclude(outcome=OutcomeChoices.PENDING)
        
        total = similar.count()
        if total == 0:
            return None
        
        succeeded = similar.filter(outcome=OutcomeChoices.SUCCEEDED).count()
        return {
            'success_rate': round((succeeded / total) * 100, 1),
            'sample_size': total
        }


class AuditRCA(models.Model):
    """
    Root Cause Analysis for an audit
    
    Each audit can have multiple ranked causes with confidence scores
    """
    audit = models.ForeignKey(InsightAudit, on_delete=models.CASCADE, related_name='root_causes')
    cause = models.CharField(max_length=30, choices=RCACauseChoices.choices, db_index=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, help_text="0-100 confidence score")
    rank = models.IntegerField(help_text="Ranking among all causes (1=primary)")
    
    # Evidence supporting this cause
    evidence = models.JSONField(default=dict, help_text="Structured evidence data")
    summary = models.TextField(help_text="Human-readable summary of why this cause applies")
    
    # Attribution details
    explain_shap = models.JSONField(default=dict, blank=True, help_text="SHAP values if model-related")
    news_references = models.JSONField(default=list, blank=True, help_text="Related NewsEvent IDs")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'autopsy_auditrca'
        ordering = ['audit', 'rank']
        indexes = [
            models.Index(fields=['audit', 'rank']),
            models.Index(fields=['cause', '-confidence']),
        ]
        verbose_name = 'Audit Root Cause'
        verbose_name_plural = 'Audit Root Causes'
    
    def __str__(self):
        return f"RCA: {self.get_cause_display()} ({self.confidence}%) - Audit #{self.audit_id}"


class AutopsyJob(models.Model):
    """
    Batch job for running audits on multiple insights
    """
    job_id = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Scope
    insight_ids = models.JSONField(default=list, help_text="List of Signal IDs to audit")
    from_date = models.DateTimeField(null=True, blank=True)
    to_date = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    horizons = models.JSONField(default=list, help_text="e.g., ['1H', '4H', '24H']")
    params = models.JSONField(default=dict, help_text="Labeling rules and thresholds")
    
    # Execution
    status = models.CharField(max_length=20, choices=JobStatusChoices.choices, 
                             default=JobStatusChoices.PENDING, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_insights = models.IntegerField(default=0)
    completed_audits = models.IntegerField(default=0)
    failed_audits = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Metadata
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'autopsy_autopsyjob'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['job_id']),
        ]
        verbose_name = 'Autopsy Job'
        verbose_name_plural = 'Autopsy Jobs'
    
    def __str__(self):
        return f"Job {self.job_id} - {self.status} ({self.completed_audits}/{self.total_insights})"
    
    def get_duration(self):
        """Calculate job duration"""
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            return delta.total_seconds()
        return None


class RetrainRequest(models.Model):
    """
    Request to retrain a model based on audit findings
    """
    # Identification
    request_id = models.CharField(max_length=100, unique=True, db_index=True)
    strategy = models.CharField(max_length=100, help_text="Strategy or model to retrain")
    
    # Dataset
    dataset_path = models.CharField(max_length=500, help_text="Path to training dataset")
    audit_count = models.IntegerField(default=0, help_text="Number of audits in dataset")
    
    # Justification
    reason = models.TextField(help_text="Why retraining is needed")
    suggested_changes = models.JSONField(default=list, help_text="Specific suggestions")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=RetrainStatusChoices.choices,
                             default=RetrainStatusChoices.REQUESTED, db_index=True)
    
    # Metrics
    metrics_before = models.JSONField(default=dict, help_text="Current model performance")
    metrics_after_simulation = models.JSONField(default=dict, blank=True, 
                                                help_text="Simulated performance after retrain")
    metrics_after_production = models.JSONField(default=dict, blank=True,
                                                help_text="Actual performance in production")
    
    # Approval workflow
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                     related_name='retrain_requests')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='retrain_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)
    
    # Model version linkage
    old_model_version = models.ForeignKey('ModelVersion', on_delete=models.SET_NULL, null=True,
                                          blank=True, related_name='retrain_from')
    new_model_version = models.ForeignKey('ModelVersion', on_delete=models.SET_NULL, null=True,
                                          blank=True, related_name='retrain_to')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'autopsy_retrainrequest'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['strategy', '-created_at']),
        ]
        verbose_name = 'Retrain Request'
        verbose_name_plural = 'Retrain Requests'
    
    def __str__(self):
        return f"Retrain {self.strategy} - {self.status}"


class ModelVersion(models.Model):
    """
    Track model versions with metrics and dataset snapshots
    
    Enables rollback and A/B testing
    """
    # Identification
    version_id = models.CharField(max_length=100, unique=True, db_index=True)
    strategy = models.CharField(max_length=100, db_index=True)
    model_type = models.CharField(max_length=50, help_text="e.g., RandomForest, XGBoost")
    
    # Artifacts
    model_path = models.CharField(max_length=500, help_text="Path to serialized model")
    config = models.JSONField(default=dict, help_text="Hyperparameters and configuration")
    
    # Training details
    dataset_path = models.CharField(max_length=500)
    dataset_size = models.IntegerField(help_text="Number of training samples")
    train_date_from = models.DateTimeField(null=True, blank=True)
    train_date_to = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    metrics = models.JSONField(default=dict, help_text="Accuracy, precision, recall, F1, etc.")
    validation_metrics = models.JSONField(default=dict, blank=True)
    feature_importance = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=False, db_index=True)
    is_production = models.BooleanField(default=False, db_index=True)
    
    # Metadata
    trained_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'autopsy_modelversion'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['strategy', '-created_at']),
            models.Index(fields=['is_production', 'strategy']),
        ]
        verbose_name = 'Model Version'
        verbose_name_plural = 'Model Versions'
    
    def __str__(self):
        prod_flag = " [PROD]" if self.is_production else ""
        return f"{self.strategy} v{self.version_id}{prod_flag}"
    
    def activate(self):
        """Set this version as active, deactivating others"""
        ModelVersion.objects.filter(strategy=self.strategy, is_active=True).update(is_active=False)
        self.is_active = True
        self.save()


class LabelingRule(models.Model):
    """
    Configurable rules for outcome labeling
    
    Allows dynamic adjustment of success/failure criteria per strategy/symbol
    """
    # Scope
    strategy = models.CharField(max_length=100, blank=True, help_text="Apply to specific strategy (blank = all)")
    symbol = models.CharField(max_length=20, blank=True, help_text="Apply to specific symbol (blank = all)")
    timeframe = models.CharField(max_length=10, blank=True)
    
    # Rule configuration
    horizon = models.CharField(max_length=10, help_text="e.g., 1H, 4H, 24H")
    
    # Success criteria
    success_tp_pips = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                          help_text="Price must move this many pips in favor")
    success_rr_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                           help_text="Risk:Reward ratio (e.g., 2.0 = 1:2)")
    
    # Failure criteria
    fail_sl_pips = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                       help_text="Stop loss threshold")
    fail_adverse_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                           help_text="Max adverse move percentage")
    
    # Neutral zone
    neutral_band_pips = models.DecimalField(max_digits=8, decimal_places=2, default=10,
                                            help_text="Price movement within this = neutral")
    
    # Flags
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=100, help_text="Higher = applied first")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'autopsy_labelingrule'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', '-priority']),
            models.Index(fields=['strategy', 'symbol', 'timeframe']),
        ]
        verbose_name = 'Labeling Rule'
        verbose_name_plural = 'Labeling Rules'
    
    def __str__(self):
        scope = f"{self.strategy or 'All'} / {self.symbol or 'All'}"
        return f"Rule: {scope} ({self.horizon})"
    
    def matches(self, insight):
        """Check if this rule applies to an insight"""
        if self.strategy and insight.strategy != self.strategy:
            return False
        if self.symbol and insight.symbol != self.symbol:
            return False
        if self.timeframe and insight.timeframe != self.timeframe:
            return False
        return True


# ============================================================================
# VISUAL INSIGHTS MODE (ZENITH MARKET ANALYST)
# ============================================================================

class RegimeChoices(models.TextChoices):
    """Market regime classifications"""
    TRENDING = 'trending', 'Trending'
    RANGING = 'ranging', 'Ranging'
    VOLATILE = 'volatile', 'Volatile'
    CONSOLIDATION = 'consolidation', 'Consolidation'
    UNKNOWN = 'unknown', 'Unknown'


class StructureChoices(models.TextChoices):
    """Market structure patterns"""
    BOS = 'bos', 'Break of Structure'
    CHOCH = 'choch', 'Change of Character'
    PULLBACK = 'pullback', 'Pullback'
    LIQUIDITY_SWEEP = 'liquidity_sweep', 'Liquidity Sweep'
    FVG = 'fvg', 'Fair Value Gap'
    ORDER_BLOCK = 'order_block', 'Order Block'
    EQH = 'eqh', 'Equal Highs'
    EQL = 'eql', 'Equal Lows'
    COMPRESSION = 'compression', 'Compression'
    NONE = 'none', 'No Clear Structure'


class MomentumChoices(models.TextChoices):
    """Momentum states"""
    INCREASING = 'increasing', 'Increasing'
    DECREASING = 'decreasing', 'Decreasing'
    DIVERGING = 'diverging', 'Diverging'
    NEUTRAL = 'neutral', 'Neutral'


class VolumeStateChoices(models.TextChoices):
    """Volume conditions"""
    SPIKE = 'spike', 'Volume Spike'
    DROP = 'drop', 'Volume Drop'
    NORMAL = 'normal', 'Normal Volume'


class SessionChoices(models.TextChoices):
    """Trading sessions"""
    LONDON = 'london', 'London'
    NEW_YORK = 'newyork', 'New York'
    ASIA = 'asia', 'Asia'
    OFF_SESSION = 'off', 'Off-Session'


class MarketInsight(models.Model):
    """
    Visual Insights Mode - Continuous market intelligence without signals
    
    Generated every bar to provide real-time market analysis and context
    """
    # Core identification
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10, db_index=True)
    timestamp = models.DateTimeField(db_index=True, help_text="Bar timestamp")
    
    # Market metadata (from Pine Script)
    regime = models.CharField(max_length=20, choices=RegimeChoices.choices, default=RegimeChoices.UNKNOWN)
    structure = models.CharField(max_length=30, choices=StructureChoices.choices, default=StructureChoices.NONE)
    momentum = models.CharField(max_length=20, choices=MomentumChoices.choices, default=MomentumChoices.NEUTRAL)
    volume_state = models.CharField(max_length=20, choices=VolumeStateChoices.choices, default=VolumeStateChoices.NORMAL)
    session = models.CharField(max_length=20, choices=SessionChoices.choices, default=SessionChoices.OFF_SESSION)
    
    # Contextual data
    expected_behavior = models.CharField(max_length=100, blank=True, 
                                         help_text="Expansion | Retracement | Reversal | Liquidity grab")
    strength = models.IntegerField(default=0, help_text="0-100 strength score")
    risk_notes = models.JSONField(default=list, help_text="Array of risk warnings")
    
    # AI-generated insight
    insight_text = models.TextField(help_text="Natural language market analysis")
    suggestion = models.TextField(blank=True, help_text="Actionable guidance (not buy/sell)")
    insight_index = models.IntegerField(default=0, help_text="0-100 insight quality score")
    
    # Scoring breakdown
    structure_clarity = models.IntegerField(default=0, help_text="0-100")
    regime_stability = models.IntegerField(default=0, help_text="0-100")
    volume_quality = models.IntegerField(default=0, help_text="0-100")
    momentum_alignment = models.IntegerField(default=0, help_text="0-100")
    session_validity = models.IntegerField(default=0, help_text="0-100")
    risk_level = models.IntegerField(default=0, help_text="0-100, higher = more risk")
    
    # News integration
    news_impact = models.CharField(max_length=20, blank=True, 
                                   help_text="high | medium | low | none")
    news_context = models.TextField(blank=True, 
                                    help_text="High-impact USD news in 27 minutes")
    
    # Chart labels (for TradingView display)
    chart_labels = models.JSONField(default=dict, 
                                    help_text="{'structure': 'BOS', 'regime': 'Trending', ...}")
    
    # Variation tracking
    vocabulary_hash = models.CharField(max_length=64, blank=True, db_index=True,
                                       help_text="Hash of word choices to ensure uniqueness")
    sentence_structure_id = models.CharField(max_length=50, blank=True,
                                            help_text="Template ID used for variation")
    
    # Raw metadata
    raw_metadata = models.JSONField(default=dict, help_text="Complete Pine Script output")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'autopsy_marketinsight'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timeframe', '-timestamp']),
            models.Index(fields=['regime', '-timestamp']),
            models.Index(fields=['session', '-timestamp']),
            models.Index(fields=['-insight_index']),
            models.Index(fields=['vocabulary_hash']),
        ]
        verbose_name = 'Market Insight'
        verbose_name_plural = 'Market Insights'
        unique_together = [['symbol', 'timeframe', 'timestamp']]
    
    def __str__(self):
        return f"{self.symbol} {self.timeframe} - {self.regime} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    def get_context_summary(self):
        """One-line context for display"""
        return f"{self.symbol} • {self.get_regime_display()} • {self.get_session_display()} • {self.timestamp.strftime('%H:%M')}"


class VariationVocabulary(models.Model):
    """
    Dynamic vocabulary for insight variation engine
    
    Stores synonym groups, sentence templates, and phrase alternatives
    """
    # Category
    category = models.CharField(max_length=50, db_index=True,
                                help_text="liquidity | momentum | structure | regime | session | volume")
    subcategory = models.CharField(max_length=50, blank=True,
                                   help_text="building | forming | sweeping | etc.")
    
    # Variations
    base_phrase = models.CharField(max_length=200, help_text="Original/canonical phrase")
    variations = models.JSONField(default=list, 
                                  help_text="Array of alternative phrasings")
    
    # Usage tracking
    usage_count = models.IntegerField(default=0, help_text="How many times used")
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Context rules
    appropriate_for = models.JSONField(default=dict,
                                       help_text="{'regime': ['trending'], 'session': ['london'], ...}")
    avoid_with = models.JSONField(default=list,
                                  help_text="Don't use with these other phrases")
    
    # Flags
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=100, help_text="Higher = preferred")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'autopsy_variationvocabulary'
        ordering = ['category', '-priority']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-usage_count']),
        ]
        verbose_name = 'Variation Vocabulary'
        verbose_name_plural = 'Variation Vocabularies'
    
    def __str__(self):
        return f"{self.category}: {self.base_phrase}"
    
    def get_next_variation(self):
        """Return least-recently used variation"""
        if not self.variations:
            return self.base_phrase
        # Rotate through variations
        idx = self.usage_count % len(self.variations)
        return self.variations[idx]


class InsightTemplate(models.Model):
    """
    Sentence structure templates for generating varied insights
    """
    # Template
    template_id = models.CharField(max_length=50, unique=True, db_index=True)
    structure = models.TextField(help_text="e.g., 'Price is {action} as {condition}.'")
    
    # Slots
    slots = models.JSONField(default=list, 
                            help_text="['action', 'condition'] - vocabulary categories")
    
    # Context
    regime_filter = models.JSONField(default=list, blank=True,
                                     help_text="Only use for these regimes")
    structure_filter = models.JSONField(default=list, blank=True,
                                       help_text="Only use for these structures")
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Flags
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=100)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'autopsy_insighttemplate'
        ordering = ['-priority', 'usage_count']
        indexes = [
            models.Index(fields=['is_active', '-priority']),
        ]
        verbose_name = 'Insight Template'
        verbose_name_plural = 'Insight Templates'
    
    def __str__(self):
        return f"Template: {self.template_id}"
