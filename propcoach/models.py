"""
PropCoach Models
Database models for prop firm challenge simulation and training
"""
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import json

User = get_user_model()


class FirmTemplate(models.Model):
    """
    Predefined or custom prop firm challenge templates
    """
    FIRM_CHOICES = [
        ('ftmo', 'FTMO'),
        ('funding_pips', 'Funding Pips'),
        ('mff', 'MyForexFunds'),
        ('tft', 'The Funded Trader'),
        ('ftc', 'FundedNext'),
        ('e8', 'E8 Funding'),
        ('custom', 'Custom Template'),
    ]
    
    PHASE_CHOICES = [
        ('phase1', 'Phase 1 (Evaluation)'),
        ('phase2', 'Phase 2 (Verification)'),
        ('funded', 'Funded Account'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm_name = models.CharField(max_length=50, choices=FIRM_CHOICES, default='custom')
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='phase1')
    template_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Account parameters
    account_size = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=100000,
        help_text="Starting account balance"
    )
    
    # Profit requirements
    profit_target_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Required profit % to pass"
    )
    
    # Drawdown limits
    max_daily_drawdown_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Max daily loss %"
    )
    
    max_total_drawdown_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Max total loss %"
    )
    
    # Time requirements
    challenge_duration_days = models.IntegerField(
        default=30,
        help_text="Total days to complete challenge"
    )
    
    min_trading_days = models.IntegerField(
        default=5,
        help_text="Minimum days with trades required"
    )
    
    # Trading rules
    min_trade_duration_minutes = models.IntegerField(
        default=5,
        help_text="Minimum holding time per trade (0 = no limit)"
    )
    
    max_leverage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100.0,
        help_text="Maximum leverage allowed"
    )
    
    allow_weekend_holding = models.BooleanField(
        default=False,
        help_text="Allow holding positions over weekend"
    )
    
    allow_news_trading = models.BooleanField(
        default=True,
        help_text="Allow trading during high-impact news"
    )
    
    max_position_size_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.0,
        help_text="Max position size as % of account"
    )
    
    # Additional rules (JSON)
    custom_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional firm-specific rules"
    )
    
    # Profit split (for funded accounts)
    profit_split_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=80.0,
        help_text="Trader's profit share %"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['firm_name', 'phase']
        verbose_name = 'Firm Template'
        verbose_name_plural = 'Firm Templates'
    
    def __str__(self):
        return f"{self.get_firm_name_display()} - {self.template_name}"
    
    def get_profit_target_amount(self):
        """Calculate profit target in currency"""
        return self.account_size * (self.profit_target_percent / 100)
    
    def get_max_daily_loss(self):
        """Calculate max daily loss in currency"""
        return self.account_size * (self.max_daily_drawdown_percent / 100)
    
    def get_max_total_loss(self):
        """Calculate max total loss in currency"""
        return self.account_size * (self.max_total_drawdown_percent / 100)


class PropChallenge(models.Model):
    """
    User's active or completed prop challenge
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('paused', 'Paused'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='propcoach_challenges')
    template = models.ForeignKey(FirmTemplate, on_delete=models.PROTECT, related_name='challenges')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Balance tracking
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2)
    peak_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Performance metrics
    total_profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    
    # Drawdown tracking
    current_daily_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_daily_drawdown_reached = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_total_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_total_drawdown_reached = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Time tracking
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trading_days_count = models.IntegerField(default=0)
    last_trade_date = models.DateField(null=True, blank=True)
    
    # Rule violations
    violation_count = models.IntegerField(default=0)
    
    # Completion
    completion_date = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    # Readiness score (AI-calculated)
    funding_readiness_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=50.0,
        help_text="AI-calculated readiness (0-100)"
    )
    
    pass_probability = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=50.0,
        help_text="ML-predicted pass probability"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Prop Challenge'
        verbose_name_plural = 'Prop Challenges'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.template.template_name} ({self.status})"
    
    @property
    def days_elapsed(self):
        """Calculate days since start"""
        delta = timezone.now() - self.start_date
        return delta.days
    
    @property
    def days_remaining(self):
        """Calculate days remaining"""
        return max(0, self.template.challenge_duration_days - self.days_elapsed)
    
    @property
    def profit_target(self):
        """Get profit target amount"""
        return self.template.get_profit_target_amount()
    
    @property
    def profit_progress_percent(self):
        """Calculate % of profit target reached"""
        if self.profit_target == 0:
            return 0
        return float((self.total_profit_loss / self.profit_target) * 100)
    
    @property
    def win_rate(self):
        """Calculate win rate %"""
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def is_passing(self):
        """Check if currently meeting pass criteria"""
        if self.status != 'active':
            return self.status == 'passed'
        
        # Check profit target
        profit_met = self.total_profit_loss >= self.profit_target
        
        # Check trading days
        days_met = self.trading_days_count >= self.template.min_trading_days
        
        # Check no violations
        no_violations = self.violation_count == 0
        
        return profit_met and days_met and no_violations
    
    def update_balance(self, trade_pnl: Decimal):
        """Update balance after trade"""
        self.current_balance += trade_pnl
        self.total_profit_loss += trade_pnl
        
        # Update peak
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        # Update drawdown
        drawdown_from_peak = self.peak_balance - self.current_balance
        self.current_total_drawdown = drawdown_from_peak
        
        if drawdown_from_peak > self.max_total_drawdown_reached:
            self.max_total_drawdown_reached = drawdown_from_peak
        
        self.save()
    
    def reset_daily_drawdown(self):
        """Reset daily drawdown (call at start of new trading day)"""
        self.current_daily_drawdown = Decimal('0.00')
        self.save()
    
    def check_violations(self):
        """Check if any rules are violated"""
        violations = []
        
        # Check daily drawdown
        max_daily_loss = self.template.get_max_daily_loss()
        if self.current_daily_drawdown > max_daily_loss:
            violations.append({
                'type': 'daily_drawdown',
                'message': f'Daily drawdown {self.current_daily_drawdown} exceeds limit {max_daily_loss}',
                'severity': 'critical'
            })
        
        # Check total drawdown
        max_total_loss = self.template.get_max_total_loss()
        if self.current_total_drawdown > max_total_loss:
            violations.append({
                'type': 'total_drawdown',
                'message': f'Total drawdown {self.current_total_drawdown} exceeds limit {max_total_loss}',
                'severity': 'critical'
            })
        
        # Check time limit
        if self.days_remaining <= 0 and not self.is_passing:
            violations.append({
                'type': 'time_expired',
                'message': 'Challenge time expired without meeting profit target',
                'severity': 'critical'
            })
        
        return violations
    
    def calculate_readiness_score(self):
        """Calculate funding readiness score (0-100)"""
        score = 50.0  # Base score
        
        # Profit progress (30%)
        if self.profit_target > 0:
            profit_factor = min(1.0, float(self.total_profit_loss / self.profit_target))
            score += profit_factor * 30
        
        # Risk management (30%)
        max_total_loss = self.template.get_max_total_loss()
        if max_total_loss > 0:
            drawdown_factor = 1 - float(self.current_total_drawdown / max_total_loss)
            score += max(0, drawdown_factor) * 30
        
        # Consistency (20%)
        if self.total_trades > 0:
            consistency = min(1.0, self.win_rate / 60.0)  # Target 60% WR
            score += consistency * 20
        
        # Rule adherence (20%)
        violation_penalty = min(20, self.violation_count * 5)
        score -= violation_penalty
        
        self.funding_readiness_score = max(0, min(100, score))
        self.save()
        
        return self.funding_readiness_score


class TradeRecord(models.Model):
    """
    Individual trade within a prop challenge
    """
    TRADE_STATUS = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(PropChallenge, on_delete=models.CASCADE, related_name='trades')
    
    # Trade details
    symbol = models.CharField(max_length=20)
    side = models.CharField(max_length=10, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    entry_price = models.DecimalField(max_digits=20, decimal_places=5)
    exit_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    
    # Position sizing
    lot_size = models.DecimalField(max_digits=10, decimal_places=2)
    position_size_percent = models.DecimalField(max_digits=5, decimal_places=2)
    leverage_used = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    # Risk management
    stop_loss = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    risk_reward_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Results
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_loss_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Timing
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    hold_duration_minutes = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=TRADE_STATUS, default='open')
    
    # Trading context
    strategy_used = models.CharField(max_length=100, blank=True)
    confidence_score = models.IntegerField(default=50)
    trader_sentiment = models.CharField(max_length=50, blank=True)
    
    # Violations flagged
    has_violations = models.BooleanField(default=False)
    violation_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-entry_time']
        verbose_name = 'Trade Record'
        verbose_name_plural = 'Trade Records'
        indexes = [
            models.Index(fields=['challenge', 'status']),
            models.Index(fields=['entry_time']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.side} - {self.profit_loss} ({self.status})"
    
    def close_trade(self, exit_price: Decimal, exit_time=None):
        """Close the trade and calculate P/L"""
        self.exit_price = exit_price
        self.exit_time = exit_time or timezone.now()
        self.status = 'closed'
        
        # Calculate hold duration
        duration = self.exit_time - self.entry_time
        self.hold_duration_minutes = int(duration.total_seconds() / 60)
        
        # Calculate P/L (simplified - should use proper forex calculation)
        if self.side == 'buy':
            pnl = (self.exit_price - self.entry_price) * self.lot_size * 100000  # Simplified
        else:
            pnl = (self.entry_price - self.exit_price) * self.lot_size * 100000
        
        self.profit_loss = pnl
        self.profit_loss_percent = (pnl / self.challenge.initial_balance) * 100
        
        self.save()
        
        # Update challenge
        self.challenge.update_balance(pnl)
        self.challenge.total_trades += 1
        if pnl > 0:
            self.challenge.winning_trades += 1
        else:
            self.challenge.losing_trades += 1
        self.challenge.save()
        
        return pnl


class PropRuleViolation(models.Model):
    """
    Log of rule violations during challenges
    """
    VIOLATION_TYPES = [
        ('daily_drawdown', 'Daily Drawdown Exceeded'),
        ('total_drawdown', 'Total Drawdown Exceeded'),
        ('min_trade_time', 'Minimum Trade Duration Violated'),
        ('weekend_hold', 'Weekend Holding Violation'),
        ('news_trading', 'News Trading Violation'),
        ('max_leverage', 'Maximum Leverage Exceeded'),
        ('max_position_size', 'Position Size Too Large'),
        ('consistency', 'Inconsistent Position Sizing'),
        ('time_expired', 'Challenge Time Expired'),
        ('other', 'Other Violation'),
    ]
    
    SEVERITY_CHOICES = [
        ('warning', 'Warning'),
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical - Challenge Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(PropChallenge, on_delete=models.CASCADE, related_name='violations')
    trade = models.ForeignKey(TradeRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='violations')
    
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='minor')
    
    description = models.TextField()
    value_breached = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    limit_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    auto_detected = models.BooleanField(default=True)
    challenge_failed = models.BooleanField(default=False)
    
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Rule Violation'
        verbose_name_plural = 'Rule Violations'
        indexes = [
            models.Index(fields=['challenge', 'severity']),
            models.Index(fields=['violation_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_violation_type_display()} - {self.severity} ({self.timestamp.strftime('%Y-%m-%d')})"


class CoachingFeedback(models.Model):
    """
    AI-generated coaching feedback for traders
    """
    FEEDBACK_TYPES = [
        ('daily_summary', 'Daily Summary'),
        ('performance_alert', 'Performance Alert'),
        ('behavioral_insight', 'Behavioral Insight'),
        ('risk_warning', 'Risk Warning'),
        ('achievement', 'Achievement Unlocked'),
        ('strategy_suggestion', 'Strategy Suggestion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(PropChallenge, on_delete=models.CASCADE, related_name='coaching_feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_feedback')
    
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Metrics referenced
    metrics_data = models.JSONField(default=dict, blank=True)
    
    # Psychology correlation (from cognition module)
    emotional_tone = models.CharField(max_length=50, blank=True)
    detected_biases = models.JSONField(default=list, blank=True)
    discipline_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Actionable recommendations
    recommendations = models.JSONField(default=list, blank=True)
    priority = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Status
    is_read = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=True)
    action_taken = models.BooleanField(default=False)
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Coaching Feedback'
        verbose_name_plural = 'Coaching Feedback'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['challenge', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email} ({self.timestamp.strftime('%Y-%m-%d')})"


class PropTrainingSession(models.Model):
    """
    Track training sessions and learning progress
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_sessions')
    
    session_date = models.DateField(default=timezone.now)
    challenges_attempted = models.IntegerField(default=0)
    challenges_passed = models.IntegerField(default=0)
    challenges_failed = models.IntegerField(default=0)
    
    # Performance metrics
    avg_win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_profit_factor = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    avg_max_drawdown = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Learning indicators
    rule_violations_count = models.IntegerField(default=0)
    discipline_improvement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    readiness_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    
    # AI insights
    learning_insights = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-session_date']
        verbose_name = 'Training Session'
        verbose_name_plural = 'Training Sessions'
    
    def __str__(self):
        return f"{self.user.email} - {self.session_date}"
