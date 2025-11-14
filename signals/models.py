from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


class PropRules(models.Model):
    """
    Model to store proprietary trading rules and risk management parameters
    """
    name = models.CharField(max_length=100, unique=True, help_text="Rule set name (e.g., 'FTMO', 'MyFundedFX')")
    
    # Daily loss limits
    max_daily_loss_pct = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=5.0,
        help_text="Maximum daily loss as percentage of account balance"
    )
    max_daily_loss_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum daily loss in absolute currency amount (optional)"
    )
    
    # Trade limits
    max_trades_per_day = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=10,
        help_text="Maximum number of trades allowed per day"
    )
    max_open_positions = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=3,
        help_text="Maximum number of simultaneously open positions"
    )
    
    # Time restrictions
    blackout_minutes = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=5,
        help_text="Minutes to wait between trades on the same symbol"
    )
    trading_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Start of allowed trading hours (UTC)"
    )
    trading_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="End of allowed trading hours (UTC)"
    )
    
    # Position sizing
    max_position_size_pct = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=2.0,
        help_text="Maximum position size as percentage of account"
    )
    max_risk_per_trade_pct = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=1.0,
        help_text="Maximum risk per trade as percentage of account"
    )
    
    # Symbol restrictions
    allowed_symbols = models.TextField(
        blank=True,
        help_text="Comma-separated list of allowed symbols (leave empty for all)"
    )
    blacklisted_symbols = models.TextField(
        blank=True,
        help_text="Comma-separated list of blacklisted symbols"
    )
    
    # Confidence threshold
    min_confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=60.0,
        help_text="Minimum confidence score required to take a trade"
    )
    
    # Weekend trading
    allow_weekend_trading = models.BooleanField(
        default=False,
        help_text="Allow trading on weekends"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rule set is currently active"
    )
    
    # Metadata
    account_balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('10000.00'),
        help_text="Current account balance for percentage calculations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Prop Trading Rule'
        verbose_name_plural = 'Prop Trading Rules'
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class SessionRule(models.Model):
    """
    Model to store per-session trading rules (weight, blocking)
    Allows users to customize behavior by FX trading session
    """
    SESSION_CHOICES = [
        ('Asia', 'Asia Session'),
        ('London', 'London Session'),
        ('New York', 'New York Session'),
    ]
    
    # Session identification
    session = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES,
        db_index=True,
        help_text="FX trading session"
    )
    
    # User ownership
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='session_rules',
        help_text="User who owns this session rule"
    )
    
    # Session weight (for ranking/prioritization)
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Weight multiplier for signals in this session (0.0-10.0, default 1.0)"
    )
    
    # Session blocking
    is_blocked = models.BooleanField(
        default=False,
        help_text="If true, signals during this session are auto-blocked"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this session rule"
    )
    
    class Meta:
        verbose_name = 'Session Rule'
        verbose_name_plural = 'Session Rules'
        ordering = ['user', 'session']
        unique_together = [['user', 'session']]
    
    def __str__(self):
        status = "BLOCKED" if self.is_blocked else f"Weight: {self.weight}"
        return f"{self.user.email} - {self.session} ({status})"


class RiskControl(models.Model):
    """
    Model to store risk control settings to protect against loss spirals
    Automatically disables trading when risk thresholds are exceeded
    """
    # User ownership
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='risk_controls',
        help_text="User who owns this risk control setting"
    )
    
    # Risk thresholds
    max_consecutive_losers = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Maximum consecutive losing trades before auto-halt (1-20)"
    )
    
    max_daily_trades = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum total trades allowed per day (1-100)"
    )
    
    max_red_signals_per_day = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Maximum rejected/blocked signals per day before halting (1-50)"
    )
    
    # Control settings
    is_active = models.BooleanField(
        default=True,
        help_text="Whether risk controls are currently active"
    )
    
    halt_until_reset = models.BooleanField(
        default=True,
        help_text="If true, halt trading until manual reset. If false, reset at midnight UTC."
    )
    
    # Tracking
    is_halted = models.BooleanField(
        default=False,
        help_text="Whether trading is currently halted due to risk violation"
    )
    
    halt_reason = models.TextField(
        blank=True,
        help_text="Reason for current halt (if any)"
    )
    
    halt_triggered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the halt was triggered"
    )
    
    last_reset_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When risk controls were last reset"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about risk control strategy"
    )
    
    class Meta:
        verbose_name = 'Risk Control'
        verbose_name_plural = 'Risk Controls'
        ordering = ['user', '-is_active']
    
    def __str__(self):
        status = "🚫 HALTED" if self.is_halted else "✅ Active" if self.is_active else "⏸️ Paused"
        return f"{self.user.email} - {status}"
    
    def reset_halt(self):
        """Manually reset the halt status"""
        self.is_halted = False
        self.halt_reason = ""
        self.halt_triggered_at = None
        self.last_reset_at = timezone.now()
        self.save()
    
    def trigger_halt(self, reason):
        """Trigger a trading halt with specified reason"""
        self.is_halted = True
        self.halt_reason = reason
        self.halt_triggered_at = timezone.now()
        self.save()
    
    def should_auto_reset(self):
        """Check if risk controls should auto-reset (new trading day)"""
        if not self.halt_until_reset and self.halt_triggered_at:
            # Check if it's a new day (UTC)
            now = timezone.now()
            halt_date = self.halt_triggered_at.date()
            return now.date() > halt_date
        return False


class StrategyPerformance(models.Model):
    """
    Model to track and analyze strategy performance metrics
    """
    REGIME_CHOICES = [
        ('Trend', 'Trend'),
        ('Breakout', 'Breakout'),
        ('MeanReversion', 'Mean Reversion'),
        ('Squeeze', 'Squeeze'),
    ]
    
    # Strategy identification
    strategy_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the trading strategy (e.g., 'ZenithEdge-Trend')"
    )
    regime = models.CharField(
        max_length=20,
        choices=REGIME_CHOICES,
        null=True,
        blank=True,
        help_text="Specific regime if performance is regime-specific"
    )
    symbol = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text="Specific symbol if performance is symbol-specific"
    )
    timeframe = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Specific timeframe if performance is timeframe-specific"
    )
    
    # Performance metrics
    total_trades = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total number of completed trades"
    )
    winning_trades = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of winning trades"
    )
    losing_trades = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of losing trades"
    )
    
    win_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Win rate as percentage (0-100)"
    )
    
    # Risk-Reward metrics
    avg_rr = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Average risk-reward ratio achieved"
    )
    total_rr = models.FloatField(
        default=0.0,
        help_text="Cumulative R-multiple (total R gained/lost)"
    )
    
    # Drawdown metrics
    max_drawdown = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Maximum drawdown as percentage"
    )
    current_drawdown = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Current drawdown from peak"
    )
    
    # Profitability metrics
    total_pnl = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Total profit/loss in currency"
    )
    avg_win = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Average winning trade amount"
    )
    avg_loss = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Average losing trade amount"
    )
    profit_factor = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Ratio of gross profit to gross loss"
    )
    
    # Confidence metrics
    avg_confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Average confidence score of signals"
    )
    
    # Tracking
    analysis_period_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Start date of analysis period"
    )
    analysis_period_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End date of analysis period"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Last time performance was calculated"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    # User ownership
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='strategy_performances',
        null=True,
        blank=True,
        help_text="User who owns this performance record"
    )
    
    class Meta:
        ordering = ['-win_rate', '-total_trades']
        verbose_name = 'Strategy Performance'
        verbose_name_plural = 'Strategy Performances'
        indexes = [
            models.Index(fields=['strategy_name', '-win_rate']),
            models.Index(fields=['regime', '-total_trades']),
            models.Index(fields=['-last_updated']),
        ]
        unique_together = [
            ['strategy_name', 'regime', 'symbol', 'timeframe', 'user']
        ]
    
    def __str__(self):
        parts = [self.strategy_name]
        if self.regime:
            parts.append(self.regime)
        if self.symbol:
            parts.append(self.symbol)
        if self.timeframe:
            parts.append(self.timeframe)
        return f"{' - '.join(parts)} (WR: {self.win_rate:.1f}%)"
    
    def update_metrics(self):
        """Recalculate all performance metrics"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        else:
            self.win_rate = 0.0
        
        # Calculate profit factor
        gross_profit = abs(float(self.avg_win)) * self.winning_trades if self.winning_trades > 0 else 0
        gross_loss = abs(float(self.avg_loss)) * self.losing_trades if self.losing_trades > 0 else 0
        
        if gross_loss > 0:
            self.profit_factor = gross_profit / gross_loss
        else:
            self.profit_factor = gross_profit if gross_profit > 0 else 0.0
        
        self.save()
    
    @property
    def is_profitable(self):
        """Check if strategy is profitable"""
        return float(self.total_pnl) > 0
    
    @property
    def performance_score(self):
        """Calculate overall performance score (0-100)"""
        # Weighted score: win_rate (40%), avg_rr (30%), profit_factor (30%)
        if self.total_trades == 0:
            return 0.0
        
        wr_score = self.win_rate * 0.4
        rr_score = min(self.avg_rr * 10, 100) * 0.3  # Cap RR contribution at 10:1
        pf_score = min(self.profit_factor * 20, 100) * 0.3  # Cap PF contribution at 5.0
        
        return wr_score + rr_score + pf_score
    
    def get_allowed_symbols_list(self):
        """Return list of allowed symbols"""
        if not self.allowed_symbols:
            return []
        return [s.strip().upper() for s in self.allowed_symbols.split(',') if s.strip()]
    
    def get_blacklisted_symbols_list(self):
        """Return list of blacklisted symbols"""
        if not self.blacklisted_symbols:
            return []
        return [s.strip().upper() for s in self.blacklisted_symbols.split(',') if s.strip()]
    
    def calculate_daily_loss_limit(self):
        """Calculate the daily loss limit in currency amount"""
        pct_limit = float(self.account_balance) * (self.max_daily_loss_pct / 100)
        
        if self.max_daily_loss_amount:
            return min(float(self.max_daily_loss_amount), pct_limit)
        
        return pct_limit


class Signal(models.Model):
    """
    Model to store trading signals received from TradingView webhooks
    """
    SIDE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    REGIME_CHOICES = [
        ('Trend', 'Trend'),
        ('Breakout', 'Breakout'),
        ('MeanReversion', 'Mean Reversion'),
        ('Squeeze', 'Squeeze'),
    ]
    
    SESSION_CHOICES = [
        ('Asia', 'Asia Session'),
        ('London', 'London Session'),
        ('New York', 'New York Session'),
    ]
    
    # Core signal fields
    symbol = models.CharField(max_length=20, db_index=True)
    timeframe = models.CharField(max_length=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    sl = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="Stop Loss")
    tp = models.DecimalField(max_digits=20, decimal_places=8, verbose_name="Take Profit")
    confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    strategy = models.CharField(max_length=50)
    regime = models.CharField(max_length=20, choices=REGIME_CHOICES)
    session = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="FX trading session (auto-detected from timestamp)"
    )
    
    # Additional fields
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    timestamp = models.CharField(max_length=100, null=True, blank=True)
    
    # Auto-generated fields
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User ownership
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='signals',
        null=True,
        blank=True,
        help_text="User who owns this signal"
    )
    
    # Prop rules validation
    is_allowed = models.BooleanField(default=True, help_text="Whether signal passed prop rules validation")
    rejection_reason = models.TextField(blank=True, help_text="Reason for signal rejection")
    prop_rule_checked = models.ForeignKey(
        PropRules,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signals',
        help_text="Prop rule set used for validation"
    )
    
    # Risk control fields
    outcome = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('win', 'Win'),
            ('loss', 'Loss'),
        ],
        default='pending',
        help_text="Trade outcome (pending until manually set or auto-detected)"
    )
    
    is_risk_blocked = models.BooleanField(
        default=False,
        help_text="Whether signal was blocked by risk control rules"
    )
    
    risk_control_checked = models.ForeignKey(
        'RiskControl',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signals',
        help_text="Risk control setting used for validation"
    )
    
    # Chart replay fields
    chart_snapshot = models.ImageField(
        upload_to='chart_snapshots/',
        null=True,
        blank=True,
        help_text="Chart snapshot image for trade replay"
    )
    
    replay_data = models.JSONField(
        null=True,
        blank=True,
        help_text="OHLCV data for replay (JSON format)"
    )
    
    entry_bar_index = models.IntegerField(
        null=True,
        blank=True,
        help_text="Bar index where signal was generated"
    )
    
    exit_bar_index = models.IntegerField(
        null=True,
        blank=True,
        help_text="Bar index where trade was closed (SL/TP hit)"
    )
    
    exit_reason = models.CharField(
        max_length=20,
        choices=[
            ('tp_hit', 'Take Profit Hit'),
            ('sl_hit', 'Stop Loss Hit'),
            ('manual', 'Manual Close'),
            ('active', 'Still Active'),
        ],
        default='active',
        help_text="Reason for trade exit"
    )
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Trading Signal'
        verbose_name_plural = 'Trading Signals'
        indexes = [
            models.Index(fields=['-received_at', 'symbol']),
            models.Index(fields=['strategy', 'regime']),
        ]
    
    def __str__(self):
        user_info = f"[{self.user.email}] " if self.user else ""
        return f"{user_info}{self.symbol} - {self.side.upper()} - {self.regime} ({self.received_at.strftime('%Y-%m-%d %H:%M:%S')})"
    
    @staticmethod
    def detect_session(dt):
        """
        Detect FX trading session from UTC timestamp
        
        Args:
            dt: datetime object (UTC timezone)
        
        Returns:
            str: 'Asia', 'London', or 'New York'
        
        Session times (UTC):
        - Asia: 00:00 - 08:00 UTC (Tokyo market hours)
        - London: 08:00 - 16:00 UTC (London market hours)
        - New York: 16:00 - 24:00 UTC (NY market hours)
        """
        if dt is None:
            dt = timezone.now()
        
        # Ensure timezone aware
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        
        # Convert to UTC
        dt_utc = dt.astimezone(timezone.utc)
        hour = dt_utc.hour
        
        if 0 <= hour < 8:
            return 'Asia'
        elif 8 <= hour < 16:
            return 'London'
        else:  # 16 <= hour < 24
            return 'New York'
    
    def save(self, *args, **kwargs):
        """Override save to auto-detect session"""
        # Auto-detect session if not set
        if not self.session:
            self.session = self.detect_session(self.received_at)
        super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convert signal to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'side': self.side,
            'sl': float(self.sl),
            'tp': float(self.tp),
            'confidence': self.confidence,
            'strategy': self.strategy,
            'regime': self.regime,
            'session': self.session,
            'price': float(self.price) if self.price else None,
            'timestamp': self.timestamp,
            'received_at': self.received_at.isoformat(),
            'is_allowed': self.is_allowed,
            'rejection_reason': self.rejection_reason,
        }


class MarketInsight(models.Model):
    """
    AI Decision Intelligence Console - Market Insight Model
    
    Replaces trading signals with intelligent market interpretation.
    Focus on analysis, context, and narrative rather than trade instructions.
    """
    
    BIAS_CHOICES = [
        ('bearish', 'Bearish'),
        ('neutral', 'Neutral'),
        ('bullish', 'Bullish'),
    ]
    
    MARKET_PHASE_CHOICES = [
        ('accumulation', 'Accumulation'),
        ('expansion', 'Expansion'),
        ('manipulation', 'Manipulation'),
        ('distribution', 'Distribution'),
    ]
    
    REGIME_CHOICES = [
        ('Trend', 'Trend'),
        ('Breakout', 'Breakout'),
        ('MeanReversion', 'Mean Reversion'),
        ('Squeeze', 'Squeeze'),
    ]
    
    SESSION_CHOICES = [
        ('Asia', 'Asia Session'),
        ('London', 'London Session'),
        ('New York', 'New York Session'),
    ]
    
    # Core intelligence fields
    symbol = models.CharField(max_length=20, db_index=True, help_text="Market instrument (e.g., GBPJPY)")
    timeframe = models.CharField(max_length=10, help_text="Analysis timeframe (e.g., 4H, 1H)")
    regime = models.CharField(max_length=20, choices=REGIME_CHOICES, help_text="Market regime classification")
    session = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="FX trading session context"
    )
    
    # AI Intelligence Fields (NEW - Core transformation)
    bias = models.CharField(
        max_length=10,
        choices=BIAS_CHOICES,
        default='neutral',
        help_text="AI-detected market bias (not trade direction)"
    )
    
    narrative = models.TextField(
        help_text="AI-generated market interpretation (2-3 sentences explaining context)"
    )
    
    market_phase = models.CharField(
        max_length=20,
        choices=MARKET_PHASE_CHOICES,
        help_text="Current market phase classification"
    )
    
    insight_index = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="AI reasoning quality score (0-100) - replaces 'AI Score'"
    )
    
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="AI conviction in current regime analysis (not trade confidence)"
    )
    
    follow_up_cue = models.TextField(
        blank=True,
        help_text="Optional suggestion for what to observe (e.g., 'watch for liquidity retest near 185.30')"
    )
    
    # Context fields
    strategy = models.CharField(max_length=50, help_text="Analysis strategy used")
    observation_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Current observation price point"
    )
    
    # Legacy compatibility fields (deprecated but kept for data migration)
    legacy_side = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        help_text="DEPRECATED: Original signal direction (for migration only)"
    )
    legacy_sl = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="DEPRECATED: Stop loss (for migration only)"
    )
    legacy_tp = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="DEPRECATED: Take profit (for migration only)"
    )
    
    # Metadata
    timestamp = models.CharField(max_length=100, null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User ownership
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='market_insights',
        null=True,
        blank=True,
        help_text="User who owns this insight"
    )
    
    # Quality control
    is_high_quality = models.BooleanField(
        default=True,
        help_text="Whether insight passed quality threshold (insight_index >= 70)"
    )
    quality_notes = models.TextField(
        blank=True,
        help_text="Notes about insight quality or data issues"
    )
    
    # Outcome tracking (for model improvement)
    outcome = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('accurate', 'Accurate Analysis'),
            ('inaccurate', 'Inaccurate Analysis'),
        ],
        default='pending',
        help_text="Whether the market analysis proved accurate (for AI improvement)"
    )
    
    # Related signal (for migration period)
    original_signal = models.OneToOneField(
        Signal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insight',
        help_text="Original signal this insight was derived from (migration only)"
    )
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Market Insight'
        verbose_name_plural = 'Market Insights'
        indexes = [
            models.Index(fields=['-received_at', 'symbol']),
            models.Index(fields=['strategy', 'regime']),
            models.Index(fields=['bias', 'market_phase']),
        ]
    
    def __str__(self):
        user_info = f"[{self.user.email}] " if self.user else ""
        return f"{user_info}{self.symbol} - {self.regime} - {self.bias.upper()} ({self.received_at.strftime('%Y-%m-%d %H:%M:%S')})"
    
    @staticmethod
    def detect_session(dt):
        """
        Detect FX trading session from UTC timestamp
        """
        from django.utils import timezone as tz
        
        # If naive datetime, make it aware
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        
        # Convert to UTC
        dt_utc = dt.astimezone(timezone.utc)
        hour = dt_utc.hour
        
        if 0 <= hour < 8:
            return 'Asia'
        elif 8 <= hour < 16:
            return 'London'
        else:
            return 'New York'
    
    def save(self, *args, **kwargs):
        """Override save to auto-detect session and set quality flag"""
        # Auto-detect session if not set
        if not self.session:
            self.session = self.detect_session(self.received_at)
        
        # Auto-set quality flag based on insight_index
        self.is_high_quality = self.insight_index >= 70
        
        super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convert insight to dictionary (NO TRADING LANGUAGE)"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'regime': self.regime,
            'session': self.session,
            'bias': self.bias,
            'narrative': self.narrative,
            'market_phase': self.market_phase,
            'insight_index': self.insight_index,
            'confidence_score': self.confidence_score,
            'follow_up_cue': self.follow_up_cue,
            'strategy': self.strategy,
            'observation_price': float(self.observation_price) if self.observation_price else None,
            'timestamp': self.timestamp,
            'received_at': self.received_at.isoformat(),
            'is_high_quality': self.is_high_quality,
            'quality_notes': self.quality_notes,
        }


def evaluate_risk_controls(user):
    """
    Evaluate if user has exceeded risk control thresholds
    
    Args:
        user: CustomUser instance
    
    Returns:
        dict: {
            'blocked': bool,
            'reason': str,
            'risk_control': RiskControl instance or None
        }
    """
    # Get active risk control for user
    try:
        risk_control = RiskControl.objects.filter(user=user, is_active=True).first()
    except Exception:
        return {
            'blocked': False,
            'reason': 'No active risk controls configured',
            'risk_control': None
        }
    
    if not risk_control:
        return {
            'blocked': False,
            'reason': 'No active risk controls configured',
            'risk_control': None
        }
    
    # Check if already halted
    if risk_control.is_halted:
        # Check if should auto-reset
        if risk_control.should_auto_reset():
            risk_control.reset_halt()
        else:
            return {
                'blocked': True,
                'reason': f'Trading halted: {risk_control.halt_reason}',
                'risk_control': risk_control
            }
    
    # Get today's signals for this user
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_signals = Signal.objects.filter(
        user=user,
        received_at__gte=today_start
    ).order_by('received_at')
    
    # Check 1: Max daily trades
    total_today = today_signals.count()
    if total_today >= risk_control.max_daily_trades:
        reason = f'Daily trade limit reached ({total_today}/{risk_control.max_daily_trades})'
        risk_control.trigger_halt(reason)
        return {
            'blocked': True,
            'reason': reason,
            'risk_control': risk_control
        }
    
    # Check 2: Max red signals per day
    red_signals_today = today_signals.filter(is_allowed=False).count()
    if red_signals_today >= risk_control.max_red_signals_per_day:
        reason = f'Too many rejected signals today ({red_signals_today}/{risk_control.max_red_signals_per_day})'
        risk_control.trigger_halt(reason)
        return {
            'blocked': True,
            'reason': reason,
            'risk_control': risk_control
        }
    
    # Check 3: Consecutive losers (only count signals with outcomes)
    consecutive_losses = 0
    for signal in today_signals.filter(outcome__in=['win', 'loss']).order_by('-received_at'):
        if signal.outcome == 'loss':
            consecutive_losses += 1
        else:
            # Win breaks the streak
            break
    
    if consecutive_losses >= risk_control.max_consecutive_losers:
        reason = f'Consecutive loss limit reached ({consecutive_losses}/{risk_control.max_consecutive_losers})'
        risk_control.trigger_halt(reason)
        return {
            'blocked': True,
            'reason': reason,
            'risk_control': risk_control
        }
    
    # All checks passed
    return {
        'blocked': False,
        'reason': 'Risk controls passed',
        'risk_control': risk_control
    }


def check_signal_against_prop(signal_data, prop_rules=None):
    """
    Check if a signal complies with proprietary trading rules
    
    Args:
        signal_data: Dictionary containing signal data (symbol, side, confidence, etc.)
        prop_rules: PropRules instance (if None, uses active rule set)
    
    Returns:
        dict: {
            'allowed': bool,
            'reason': str,
            'prop_rule': PropRules instance or None
        }
    """
    # Get active prop rules if not provided
    if prop_rules is None:
        try:
            prop_rules = PropRules.objects.filter(is_active=True).first()
        except Exception:
            # If no prop rules exist or DB error, allow signal
            return {
                'allowed': True,
                'reason': 'No active prop rules configured',
                'prop_rule': None
            }
    
    if not prop_rules:
        return {
            'allowed': True,
            'reason': 'No active prop rules configured',
            'prop_rule': None
        }
    
    # Extract signal data
    symbol = signal_data.get('symbol', '').upper()
    confidence = signal_data.get('confidence', 0)
    
    # Check 1: Confidence score
    if confidence < prop_rules.min_confidence_score:
        return {
            'allowed': False,
            'reason': f'Confidence {confidence:.2f}% below minimum {prop_rules.min_confidence_score}%',
            'prop_rule': prop_rules
        }
    
    # Check 2: Symbol whitelist
    allowed_symbols = prop_rules.get_allowed_symbols_list()
    if allowed_symbols and symbol not in allowed_symbols:
        return {
            'allowed': False,
            'reason': f'Symbol {symbol} not in allowed list: {", ".join(allowed_symbols)}',
            'prop_rule': prop_rules
        }
    
    # Check 3: Symbol blacklist
    blacklisted_symbols = prop_rules.get_blacklisted_symbols_list()
    if symbol in blacklisted_symbols:
        return {
            'allowed': False,
            'reason': f'Symbol {symbol} is blacklisted',
            'prop_rule': prop_rules
        }
    
    # Check 4: Weekend trading
    if not prop_rules.allow_weekend_trading:
        current_time = timezone.now()
        if current_time.weekday() in [5, 6]:  # Saturday=5, Sunday=6
            return {
                'allowed': False,
                'reason': 'Weekend trading not allowed',
                'prop_rule': prop_rules
            }
    
    # Check 5: Trading hours
    if prop_rules.trading_start_time and prop_rules.trading_end_time:
        current_time = timezone.now().time()
        if not (prop_rules.trading_start_time <= current_time <= prop_rules.trading_end_time):
            return {
                'allowed': False,
                'reason': f'Outside trading hours ({prop_rules.trading_start_time} - {prop_rules.trading_end_time} UTC)',
                'prop_rule': prop_rules
            }
    
    # Check 6: Max trades per day
    try:
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_signals = Signal.objects.filter(
            received_at__gte=today_start,
            is_allowed=True
        ).count()
        
        if today_signals >= prop_rules.max_trades_per_day:
            return {
                'allowed': False,
                'reason': f'Daily trade limit reached ({today_signals}/{prop_rules.max_trades_per_day})',
                'prop_rule': prop_rules
            }
    except Exception as e:
        # If DB query fails, log but don't block signal
        pass
    
    # Check 7: Blackout period (time since last trade on same symbol)
    if prop_rules.blackout_minutes > 0:
        try:
            blackout_time = timezone.now() - timedelta(minutes=prop_rules.blackout_minutes)
            recent_signal = Signal.objects.filter(
                symbol=symbol,
                received_at__gte=blackout_time,
                is_allowed=True
            ).first()
            
            if recent_signal:
                return {
                    'allowed': False,
                    'reason': f'Blackout period active for {symbol} (wait {prop_rules.blackout_minutes} min between trades)',
                    'prop_rule': prop_rules
                }
        except Exception:
            pass
    
    # Check 8: Max open positions
    try:
        open_positions = Signal.objects.filter(
            is_allowed=True
        ).values('symbol').distinct().count()
        
        if open_positions >= prop_rules.max_open_positions:
            return {
                'allowed': False,
                'reason': f'Maximum open positions reached ({open_positions}/{prop_rules.max_open_positions})',
                'prop_rule': prop_rules
            }
    except Exception:
        pass
    
    # Check 9: Daily loss limit (requires tracking of P&L - placeholder)
    # This would need integration with actual trading results
    # For now, we'll skip this check as it requires position tracking
    
    # All checks passed
    return {
        'allowed': True,
        'reason': 'Signal passed all prop rules checks',
        'prop_rule': prop_rules
    }


class TradeJournalEntry(models.Model):
    """
    Model to store trade journal entries for post-trade analysis.
    Allows traders to log their decisions, outcomes, and reflections.
    """
    DECISION_CHOICES = [
        ('took', 'Took the Trade'),
        ('skipped', 'Skipped the Trade'),
        ('partial', 'Partial Entry'),
        ('early_exit', 'Early Exit'),
    ]
    
    OUTCOME_CHOICES = [
        ('win', 'Win'),
        ('loss', 'Loss'),
        ('breakeven', 'Breakeven'),
        ('pending', 'Pending'),
        ('scratch', 'Scratch Trade'),
    ]
    
    # Relationships
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='journal_entries',
        help_text="User who created this journal entry"
    )
    signal = models.ForeignKey(
        Signal,
        on_delete=models.CASCADE,
        related_name='journal_entries',
        null=True,
        blank=True,
        help_text="Associated signal (optional)"
    )
    
    # Trade details
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        help_text="What decision did you make?"
    )
    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        default='pending',
        help_text="What was the result?"
    )
    
    # Performance metrics
    pips = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Profit/loss in pips (positive for profit, negative for loss)"
    )
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="How long was the trade open (in minutes)?"
    )
    
    # Journal notes
    notes = models.TextField(
        blank=True,
        help_text="Your thoughts, observations, and lessons learned"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Trade Journal Entry'
        verbose_name_plural = 'Trade Journal Entries'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'outcome']),
            models.Index(fields=['decision']),
        ]
    
    def __str__(self):
        signal_info = f" (Signal #{self.signal.id})" if self.signal else ""
        return f"Journal Entry #{self.id} - {self.get_decision_display()} - {self.get_outcome_display()}{signal_info}"
    
    @property
    def risk_reward_ratio(self):
        """Calculate risk:reward ratio if signal is attached"""
        if not self.signal or not self.pips:
            return None
        
        try:
            # Calculate potential risk and reward from signal
            entry = float(self.signal.price) if self.signal.price else 0
            sl = float(self.signal.sl)
            tp = float(self.signal.tp)
            
            if entry == 0:
                return None
            
            if self.signal.side == 'buy':
                risk = abs(entry - sl)
                reward = abs(tp - entry)
            else:  # sell
                risk = abs(sl - entry)
                reward = abs(entry - tp)
            
            if risk == 0:
                return None
            
            return round(reward / risk, 2)
        except (ValueError, ZeroDivisionError, AttributeError):
            return None
    
    @property
    def session(self):
        """Get session from associated signal"""
        return self.signal.session if self.signal else None
    
    @property
    def strategy(self):
        """Get strategy from associated signal"""
        return self.signal.strategy if self.signal else None
    
    @property
    def regime(self):
        """Get regime from associated signal"""
        return self.signal.regime if self.signal else None


def summarize_journal(user):
    """
    Analyze a user's trade journal and return comprehensive statistics.
    
    Args:
        user: CustomUser instance
    
    Returns:
        dict: Dictionary containing journal statistics
    """
    from django.db.models import Avg, Count, Q
    from collections import defaultdict
    
    entries = TradeJournalEntry.objects.filter(user=user)
    
    if not entries.exists():
        return {
            'total_entries': 0,
            'message': 'No journal entries found'
        }
    
    # Basic counts
    total_entries = entries.count()
    took_trades = entries.filter(decision='took').count()
    skipped_trades = entries.filter(decision='skipped').count()
    
    # Outcome analysis (only for trades that were taken)
    taken_entries = entries.filter(decision='took')
    wins = taken_entries.filter(outcome='win').count()
    losses = taken_entries.filter(outcome='loss').count()
    breakeven = taken_entries.filter(outcome='breakeven').count()
    pending = taken_entries.filter(outcome='pending').count()
    
    # Win rate calculation
    completed_trades = wins + losses + breakeven
    win_rate = (wins / completed_trades * 100) if completed_trades > 0 else 0
    
    # Pips analysis
    entries_with_pips = taken_entries.exclude(pips__isnull=True)
    total_pips = sum(float(e.pips) for e in entries_with_pips if e.pips)
    avg_pips = (total_pips / entries_with_pips.count()) if entries_with_pips.exists() else 0
    
    # Winning vs losing pips
    winning_entries = entries_with_pips.filter(outcome='win')
    losing_entries = entries_with_pips.filter(outcome='loss')
    avg_win_pips = sum(float(e.pips) for e in winning_entries if e.pips) / winning_entries.count() if winning_entries.exists() else 0
    avg_loss_pips = sum(float(e.pips) for e in losing_entries if e.pips) / losing_entries.count() if losing_entries.exists() else 0
    
    # Risk:Reward analysis
    rr_ratios = [e.risk_reward_ratio for e in entries if e.risk_reward_ratio is not None]
    avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0
    
    # Best performing strategy
    strategy_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    for entry in taken_entries.exclude(signal__isnull=True):
        if entry.signal and entry.signal.strategy:
            strategy = entry.signal.strategy
            strategy_stats[strategy]['total'] += 1
            if entry.outcome == 'win':
                strategy_stats[strategy]['wins'] += 1
            elif entry.outcome == 'loss':
                strategy_stats[strategy]['losses'] += 1
    
    best_strategy = None
    best_strategy_win_rate = 0
    for strategy, stats in strategy_stats.items():
        completed = stats['wins'] + stats['losses']
        if completed > 0:
            wr = (stats['wins'] / completed * 100)
            if wr > best_strategy_win_rate and stats['total'] >= 3:  # Min 3 trades
                best_strategy = strategy
                best_strategy_win_rate = wr
    
    # Best performing session
    session_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    for entry in taken_entries.exclude(signal__isnull=True):
        if entry.signal and entry.signal.session:
            session = entry.signal.session
            session_stats[session]['total'] += 1
            if entry.outcome == 'win':
                session_stats[session]['wins'] += 1
            elif entry.outcome == 'loss':
                session_stats[session]['losses'] += 1
    
    best_session = None
    best_session_win_rate = 0
    for session, stats in session_stats.items():
        completed = stats['wins'] + stats['losses']
        if completed > 0:
            wr = (stats['wins'] / completed * 100)
            if wr > best_session_win_rate and stats['total'] >= 3:  # Min 3 trades
                best_session = session
                best_session_win_rate = wr
    
    # Best performing hours (from signal timestamps)
    hour_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    for entry in taken_entries.exclude(signal__isnull=True):
        if entry.signal and entry.signal.received_at:
            hour = entry.signal.received_at.hour
            hour_stats[hour]['total'] += 1
            if entry.outcome == 'win':
                hour_stats[hour]['wins'] += 1
            elif entry.outcome == 'loss':
                hour_stats[hour]['losses'] += 1
    
    best_hours = []
    for hour, stats in sorted(hour_stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:3]:
        completed = stats['wins'] + stats['losses']
        if completed > 0:
            wr = (stats['wins'] / completed * 100)
            best_hours.append({
                'hour': hour,
                'win_rate': round(wr, 1),
                'total_trades': stats['total']
            })
    
    # Average trade duration
    entries_with_duration = taken_entries.exclude(duration_minutes__isnull=True)
    avg_duration = entries_with_duration.aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
    
    # Regime analysis
    regime_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total': 0})
    for entry in taken_entries.exclude(signal__isnull=True):
        if entry.signal and entry.signal.regime:
            regime = entry.signal.regime
            regime_stats[regime]['total'] += 1
            if entry.outcome == 'win':
                regime_stats[regime]['wins'] += 1
            elif entry.outcome == 'loss':
                regime_stats[regime]['losses'] += 1
    
    best_regime = None
    best_regime_win_rate = 0
    for regime, stats in regime_stats.items():
        completed = stats['wins'] + stats['losses']
        if completed > 0:
            wr = (stats['wins'] / completed * 100)
            if wr > best_regime_win_rate and stats['total'] >= 3:
                best_regime = regime
                best_regime_win_rate = wr
    
    return {
        'total_entries': total_entries,
        'took_trades': took_trades,
        'skipped_trades': skipped_trades,
        'wins': wins,
        'losses': losses,
        'breakeven': breakeven,
        'pending': pending,
        'completed_trades': completed_trades,
        'win_rate': round(win_rate, 1),
        'total_pips': round(total_pips, 2),
        'avg_pips': round(avg_pips, 2),
        'avg_win_pips': round(avg_win_pips, 2),
        'avg_loss_pips': round(avg_loss_pips, 2),
        'avg_rr': round(avg_rr, 2),
        'avg_duration_minutes': round(avg_duration, 1),
        'best_strategy': {
            'name': best_strategy,
            'win_rate': round(best_strategy_win_rate, 1) if best_strategy else 0,
            'stats': dict(strategy_stats[best_strategy]) if best_strategy else {}
        },
        'best_session': {
            'name': best_session,
            'win_rate': round(best_session_win_rate, 1) if best_session else 0,
            'stats': dict(session_stats[best_session]) if best_session else {}
        },
        'best_regime': {
            'name': best_regime,
            'win_rate': round(best_regime_win_rate, 1) if best_regime else 0,
            'stats': dict(regime_stats[best_regime]) if best_regime else {}
        },
        'best_hours': best_hours,
        'strategy_breakdown': {k: dict(v) for k, v in strategy_stats.items()},
        'session_breakdown': {k: dict(v) for k, v in session_stats.items()},
        'regime_breakdown': {k: dict(v) for k, v in regime_stats.items()},
    }


def fetch_chart_snapshot(signal, bars_before=50, bars_after=10):
    """
    Generate or fetch a chart snapshot for a signal.
    
    This is a placeholder function that can be extended to:
    1. Fetch data from TradingView via their API
    2. Use a charting library to generate the image
    3. Store external screenshot URLs
    
    Args:
        signal: Signal instance
        bars_before: Number of bars to show before signal
        bars_after: Number of bars to show after signal
    
    Returns:
        dict: Chart data and metadata
    """
    from django.utils import timezone
    from datetime import timedelta
    import random
    
    # For now, we'll generate sample OHLCV data for demonstration
    # In production, you would fetch real data from your broker API or data provider
    
    # Parse signal timestamp
    signal_time = signal.received_at
    
    # Generate sample bars
    bars = []
    current_price = float(signal.price) if signal.price else 1.2000
    
    # Calculate timeframe in minutes
    timeframe_map = {
        '1m': 1, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '4h': 240, '1d': 1440
    }
    tf_minutes = timeframe_map.get(signal.timeframe, 15)
    
    # Generate bars before signal
    for i in range(bars_before, 0, -1):
        bar_time = signal_time - timedelta(minutes=tf_minutes * i)
        
        # Random OHLC generation (for demo)
        volatility = 0.002  # 0.2%
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, volatility))
        low_price = open_price * (1 - random.uniform(0, volatility))
        close_price = open_price + random.uniform(-volatility, volatility) * open_price
        volume = random.randint(100, 1000)
        
        bars.append({
            'time': int(bar_time.timestamp()),
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'volume': volume
        })
        
        current_price = close_price
    
    # Signal bar (entry point)
    entry_bar_index = len(bars)
    bars.append({
        'time': int(signal_time.timestamp()),
        'open': round(current_price, 5),
        'high': round(current_price * 1.001, 5),
        'low': round(current_price * 0.999, 5),
        'close': round(float(signal.price) if signal.price else current_price, 5),
        'volume': random.randint(500, 2000)
    })
    
    # Bars after signal
    current_price = float(signal.price) if signal.price else current_price
    sl_price = float(signal.sl)
    tp_price = float(signal.tp)
    
    exit_bar_index = None
    exit_reason = 'active'
    
    for i in range(1, bars_after + 1):
        bar_time = signal_time + timedelta(minutes=tf_minutes * i)
        
        volatility = 0.002
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, volatility * 2))
        low_price = open_price * (1 - random.uniform(0, volatility * 2))
        close_price = open_price + random.uniform(-volatility, volatility) * open_price
        volume = random.randint(100, 1000)
        
        # Check if SL or TP hit
        if signal.side == 'buy':
            if low_price <= sl_price and exit_bar_index is None:
                exit_bar_index = len(bars)
                exit_reason = 'sl_hit'
                close_price = sl_price
            elif high_price >= tp_price and exit_bar_index is None:
                exit_bar_index = len(bars)
                exit_reason = 'tp_hit'
                close_price = tp_price
        else:  # sell
            if high_price >= sl_price and exit_bar_index is None:
                exit_bar_index = len(bars)
                exit_reason = 'sl_hit'
                close_price = sl_price
            elif low_price <= tp_price and exit_bar_index is None:
                exit_bar_index = len(bars)
                exit_reason = 'tp_hit'
                close_price = tp_price
        
        bars.append({
            'time': int(bar_time.timestamp()),
            'open': round(open_price, 5),
            'high': round(high_price, 5),
            'low': round(low_price, 5),
            'close': round(close_price, 5),
            'volume': volume
        })
        
        current_price = close_price
        
        # Stop generating bars after exit
        if exit_bar_index is not None:
            break
    
    # Update signal with replay data
    signal.replay_data = {
        'bars': bars,
        'entry_price': float(signal.price) if signal.price else current_price,
        'sl': float(signal.sl),
        'tp': float(signal.tp),
        'side': signal.side,
        'symbol': signal.symbol,
        'timeframe': signal.timeframe
    }
    signal.entry_bar_index = entry_bar_index
    signal.exit_bar_index = exit_bar_index
    signal.exit_reason = exit_reason
    signal.save()
    
    return {
        'status': 'success',
        'bars': bars,
        'entry_bar_index': entry_bar_index,
        'exit_bar_index': exit_bar_index,
        'exit_reason': exit_reason
    }


# ==================== PROP CHALLENGE MODELS ====================

class PropChallengeConfig(models.Model):
    """Configuration for prop firm challenge rules"""
    
    FIRM_CHOICES = [
        ('funding_pips', 'Funding Pips'),
        ('ftmo', 'FTMO'),
        ('myforexfunds', 'MyForexFunds'),
        ('the5ers', 'The5%ers'),
        ('topstep', 'TopStep'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='prop_challenges')
    firm_name = models.CharField(max_length=50, choices=FIRM_CHOICES, default='ftmo')
    account_size = models.IntegerField(default=10000, help_text="Challenge account size in USD")
    
    # Risk limits
    max_daily_loss_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        help_text="Max daily loss as % of account (e.g., 5.00 = 5%)"
    )
    max_overall_loss_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Max overall drawdown as % of account (e.g., 10.00 = 10%)"
    )
    
    # Challenge requirements
    min_trading_days = models.IntegerField(default=5, help_text="Minimum number of trading days required")
    profit_target_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Profit target as % of account to pass (e.g., 10.00 = 10%)"
    )
    
    # Trading restrictions
    news_blackout_minutes = models.IntegerField(
        default=2, 
        help_text="Minutes before/after major news to block trading"
    )
    leverage = models.IntegerField(default=100, help_text="Maximum leverage allowed (e.g., 100 = 100:1)")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Is this challenge currently active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'signals_propchallengeconfig'
        verbose_name = 'Prop Challenge Config'
        verbose_name_plural = 'Prop Challenge Configs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_firm_name_display()} Challenge (${self.account_size})"
    
    @classmethod
    def get_firm_presets(cls, firm_name):
        """Return preset rules for popular prop firms"""
        presets = {
            'ftmo': {
                'max_daily_loss_pct': 5.00,
                'max_overall_loss_pct': 10.00,
                'min_trading_days': 4,
                'profit_target_pct': 10.00,
                'news_blackout_minutes': 2,
                'leverage': 100,
            },
            'funding_pips': {
                'max_daily_loss_pct': 4.00,
                'max_overall_loss_pct': 8.00,
                'min_trading_days': 5,
                'profit_target_pct': 8.00,
                'news_blackout_minutes': 5,
                'leverage': 100,
            },
            'myforexfunds': {
                'max_daily_loss_pct': 5.00,
                'max_overall_loss_pct': 10.00,
                'min_trading_days': 3,
                'profit_target_pct': 8.00,
                'news_blackout_minutes': 2,
                'leverage': 100,
            },
            'the5ers': {
                'max_daily_loss_pct': 5.00,
                'max_overall_loss_pct': 6.00,
                'min_trading_days': 5,
                'profit_target_pct': 6.00,
                'news_blackout_minutes': 0,
                'leverage': 50,
            },
            'topstep': {
                'max_daily_loss_pct': 2.00,
                'max_overall_loss_pct': 3.00,
                'min_trading_days': 5,
                'profit_target_pct': 6.00,
                'news_blackout_minutes': 2,
                'leverage': 50,
            },
        }
        return presets.get(firm_name, {})
    
    def get_max_daily_loss_amount(self):
        """Calculate max daily loss in dollars"""
        return float(self.account_size) * float(self.max_daily_loss_pct) / 100
    
    def get_max_overall_loss_amount(self):
        """Calculate max overall loss in dollars"""
        return float(self.account_size) * float(self.max_overall_loss_pct) / 100
    
    def get_profit_target_amount(self):
        """Calculate profit target in dollars"""
        return float(self.account_size) * float(self.profit_target_pct) / 100


class PropChallengeProgress(models.Model):
    """Track progress for an active prop challenge"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('paused', 'Paused'),
    ]
    
    challenge = models.OneToOneField(PropChallengeConfig, on_delete=models.CASCADE, related_name='progress')
    
    # P&L tracking
    total_pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total profit/loss in USD")
    daily_pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Today's profit/loss in USD")
    peak_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Highest balance reached")
    
    # Trading statistics
    trading_days = models.IntegerField(default=0, help_text="Number of days traded")
    total_trades = models.IntegerField(default=0, help_text="Total number of trades")
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    
    # Violations
    daily_loss_violations = models.IntegerField(default=0, help_text="Times daily loss limit was hit")
    overall_loss_violations = models.IntegerField(default=0, help_text="Times overall loss limit was hit")
    news_blackout_violations = models.IntegerField(default=0, help_text="Trades during news blackout")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    last_trade_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'signals_propchallengeprogress'
        verbose_name = 'Prop Challenge Progress'
        verbose_name_plural = 'Prop Challenge Progress'
    
    def __str__(self):
        return f"{self.challenge.user.username} - {self.get_status_display()} (${self.total_pnl})"
    
    def get_current_balance(self):
        """Calculate current account balance"""
        return float(self.challenge.account_size) + float(self.total_pnl)
    
    def get_daily_loss_remaining(self):
        """How much more can be lost today before hitting limit"""
        max_loss = self.challenge.get_max_daily_loss_amount()
        return max_loss + float(self.daily_pnl)  # daily_pnl is negative for losses
    
    def get_overall_drawdown(self):
        """Calculate current drawdown from peak"""
        if self.peak_balance == 0:
            self.peak_balance = self.challenge.account_size
        current_balance = self.get_current_balance()
        drawdown = float(self.peak_balance) - current_balance
        return max(0, drawdown)
    
    def get_overall_loss_remaining(self):
        """How much more can be lost overall before hitting limit"""
        max_loss = self.challenge.get_max_overall_loss_amount()
        current_drawdown = self.get_overall_drawdown()
        return max_loss - current_drawdown
    
    def get_profit_progress_pct(self):
        """What % of profit target has been achieved"""
        target = self.challenge.get_profit_target_amount()
        if target == 0:
            return 0
        return (float(self.total_pnl) / target) * 100
    
    def get_days_remaining(self):
        """How many more trading days needed to meet minimum"""
        return max(0, self.challenge.min_trading_days - self.trading_days)
    
    def check_daily_loss_limit(self):
        """Check if daily loss limit would be breached"""
        remaining = self.get_daily_loss_remaining()
        return remaining > 0
    
    def check_overall_loss_limit(self):
        """Check if overall loss limit would be breached"""
        remaining = self.get_overall_loss_remaining()
        return remaining > 0
    
    def check_challenge_passed(self):
        """Check if challenge has been passed"""
        profit_met = float(self.total_pnl) >= self.challenge.get_profit_target_amount()
        days_met = self.trading_days >= self.challenge.min_trading_days
        no_violations = (self.daily_loss_violations == 0 and self.overall_loss_violations == 0)
        return profit_met and days_met and no_violations
    
    def get_status_indicator(self):
        """Return status emoji: 🟢 on track, 🟡 danger, 🔴 failed"""
        if self.status == 'failed':
            return '🔴'
        elif self.status == 'passed':
            return '🟢'
        
        # Check danger zones
        daily_remaining_pct = (self.get_daily_loss_remaining() / self.challenge.get_max_daily_loss_amount()) * 100
        overall_remaining_pct = (self.get_overall_loss_remaining() / self.challenge.get_max_overall_loss_amount()) * 100
        
        if daily_remaining_pct < 20 or overall_remaining_pct < 20:
            return '🔴'  # Critical danger
        elif daily_remaining_pct < 50 or overall_remaining_pct < 50:
            return '🟡'  # Warning
        else:
            return '🟢'  # On track
    
    def get_safety_status(self):
        """
        Calculate safety status based on prop challenge limits.
        Returns: dict with status, icon, color, message
        """
        if not hasattr(self, 'challenge') or self.status == 'failed':
            return {
                'status': 'Breach',
                'icon': '🔥',
                'color': 'danger',
                'message': 'Breach Detected - Challenge Failed'
            }
        
        challenge = self.challenge
        
        # Calculate risk percentages
        daily_loss_limit = challenge.account_size * (challenge.max_daily_loss_pct / 100)
        overall_loss_limit = challenge.account_size * (challenge.max_overall_loss_pct / 100)
        
        daily_loss_pct = 0
        if daily_loss_limit > 0 and self.daily_pnl < 0:
            daily_loss_pct = (abs(self.daily_pnl) / daily_loss_limit) * 100
        
        overall_loss_pct = 0
        if overall_loss_limit > 0 and self.total_pnl < 0:
            overall_loss_pct = (abs(self.total_pnl) / overall_loss_limit) * 100
        
        max_risk_pct = max(daily_loss_pct, overall_loss_pct)
        
        # Determine status
        if max_risk_pct >= 100:
            return {
                'status': 'Breach',
                'icon': '🔥',
                'color': 'danger',
                'message': 'Breach Detected - Loss Limit Reached',
                'risk_pct': int(max_risk_pct)
            }
        elif max_risk_pct >= 60:
            return {
                'status': 'At Risk',
                'icon': '⚠️',
                'color': 'warning',
                'message': f'Rule at Risk - {int(max_risk_pct)}% of limit used',
                'risk_pct': int(max_risk_pct)
            }
        else:
            return {
                'status': 'Prop Safe',
                'icon': '🛡️',
                'color': 'success',
                'message': f'Prop Safe - {int(max_risk_pct)}% of limit used',
                'risk_pct': int(max_risk_pct)
            }

    def reset_daily_pnl(self):
        """Reset daily P&L at the start of a new trading day"""
        self.daily_pnl = 0.00
        self.save()


# =============================================================================
# AI Trade Score Predictor Models
# =============================================================================

class ScoringWeights(models.Model):
    """
    Configurable weights for ZenBot's AI scoring engine.
    Allows admin to tune scoring factors without code changes.
    """
    version = models.CharField(
        max_length=20,
        unique=True,
        help_text="Version identifier (e.g., 'v1.0', 'v2.1-optimized')"
    )
    weights = models.JSONField(
        default=dict,
        help_text="Weights dict: {signal_confidence: 0.32, atr_safety: 0.18, ...}"
    )
    min_score_threshold = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum acceptable score (used as dashboard default filter)"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Only one version should be active at a time"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(
        blank=True,
        help_text="Change notes or reasoning for this weight configuration"
    )
    
    class Meta:
        db_table = 'scoring_weights'
        ordering = ['-created_at']
        verbose_name = 'Scoring Weights'
        verbose_name_plural = 'Scoring Weights'
    
    def __str__(self):
        active_str = " (ACTIVE)" if self.is_active else ""
        return f"{self.version}{active_str}"
    
    @classmethod
    def get_active_weights(cls):
        """Get the currently active scoring weights"""
        active = cls.objects.filter(is_active=True).first()
        if not active:
            # Create default weights if none exist
            active = cls.objects.create(
                version='v1.0-default',
                is_active=True,
                weights={
                    'signal_confidence': 0.32,
                    'atr_safety': 0.18,
                    'strategy_bias': 0.16,
                    'regime_fit': 0.18,
                    'rolling_win_rate': 0.16
                },
                min_score_threshold=60,
                notes='Default scoring weights with balanced factor importance'
            )
        return active
    
    def save(self, *args, **kwargs):
        # Ensure only one active version
        if self.is_active:
            ScoringWeights.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class TradeScore(models.Model):
    """
    AI-generated score for each trading signal.
    Provides 0-100 score with detailed breakdown of contributing factors.
    """
    signal = models.OneToOneField(
        Signal,
        on_delete=models.CASCADE,
        related_name='ai_score',
        primary_key=True
    )
    ai_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True,
        help_text="AI-computed score (0-100, higher is better)"
    )
    score_breakdown = models.JSONField(
        default=list,
        help_text="List of dicts: [{factor, raw_value, weight, contribution, explanation}]"
    )
    version = models.CharField(
        max_length=20,
        help_text="ScoringWeights version used to compute this score"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Cached factors for quick filtering
    confidence_factor = models.FloatField(default=0.0, help_text="Normalized confidence 0-1")
    atr_safety_factor = models.FloatField(default=0.0, help_text="ATR safety score 0-1")
    strategy_bias_factor = models.FloatField(default=0.0, help_text="Strategy bias 0-1")
    regime_fit_factor = models.FloatField(default=0.0, help_text="Regime fit score 0-1")
    rolling_win_rate = models.FloatField(default=0.0, help_text="Rolling win rate 0-1")
    
    class Meta:
        db_table = 'trade_score'
        ordering = ['-ai_score', '-created_at']
        verbose_name = 'AI Trade Score'
        verbose_name_plural = 'AI Trade Scores'
        indexes = [
            models.Index(fields=['-ai_score', '-created_at']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self):
        return f"Score {self.ai_score} for {self.signal.symbol} (v{self.version})"
    
    def get_score_badge(self):
        """Return color and icon for score display"""
        if self.ai_score >= 80:
            return {'color': 'success', 'icon': '✅', 'label': 'Excellent'}
        elif self.ai_score >= 50:
            return {'color': 'warning', 'icon': '��', 'label': 'Medium'}
        else:
            return {'color': 'danger', 'icon': '🚫', 'label': 'Risky'}
    
    def get_key_factors(self):
        """Return list of standout factors for quick display"""
        factors = []
        if self.confidence_factor >= 0.8:
            factors.append(f"High Confidence ({int(self.confidence_factor*100)}%)")
        if self.atr_safety_factor >= 0.7:
            factors.append("ATR Safe")
        if self.regime_fit_factor >= 0.75:
            factors.append(f"{self.signal.regime} Fit")
        if self.rolling_win_rate >= 0.6:
            factors.append(f"WinRate {int(self.rolling_win_rate*100)}%")
        return factors
    
    def get_explanation_text(self):
        """Generate human-readable explanation"""
        badge = self.get_score_badge()
        explanation = f"Signal scored {self.ai_score} ({badge['label']})\n\n"
        
        if self.score_breakdown:
            explanation += "Score Breakdown:\n"
            for item in self.score_breakdown:
                factor = item.get('factor', 'Unknown')
                contribution = item.get('contribution', 0)
                raw_value = item.get('raw_value', 'N/A')
                explanation += f"• {factor}: {raw_value} → +{int(contribution*100)} points\n"
        
        explanation += f"\nVersion: {self.version}"
        return explanation



# =============================================================================
# Signal Handlers - Auto-scoring
# =============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Signal)
def auto_score_signal(sender, instance, created, **kwargs):
    """
    Automatically score new signals using ZenBot scoring engine.
    Runs synchronously for now - can be moved to Celery for async processing.
    """
    if created:  # Only score new signals
        try:
            from bot.score_engine import score_signal
            # Score the signal and save TradeScore
            score_signal(instance)
        except Exception as e:
            # Log error but don't block signal creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to auto-score signal {instance.id}: {e}")


# =============================================================================
# Webhook Configuration Model
# =============================================================================


class WebhookConfig(models.Model):
    """
    Webhook configuration for users to receive TradingView signals.
    Each user gets a unique UUID-based webhook URL.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhook_config'
    )
    webhook_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Unique UUID for webhook URL"
    )
    webhook_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Full webhook URL with UUID"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable webhook"
    )
    signal_count = models.IntegerField(
        default=0,
        help_text="Total signals received via this webhook"
    )
    last_signal_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last received signal"
    )
    hmac_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional HMAC secret for signature validation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'webhook_config'
        ordering = ['-created_at']
        verbose_name = 'Webhook Configuration'
        verbose_name_plural = 'Webhook Configurations'
    
    def __str__(self):
        return f"Webhook for {self.user.email} ({self.webhook_uuid})"
    
    def generate_webhook_url(self, base_url='http://127.0.0.1:8000'):
        """Generate full webhook URL with UUID"""
        self.webhook_url = f"{base_url}/api/v1/signal/{self.webhook_uuid}/"
        return self.webhook_url
    
    def increment_signal_count(self):
        """Increment signal count and update timestamp"""
        from django.utils import timezone
        self.signal_count += 1
        self.last_signal_at = timezone.now()
        self.save(update_fields=['signal_count', 'last_signal_at'])
    
    def regenerate_uuid(self):
        """Generate new UUID (useful if webhook is compromised)"""
        self.webhook_uuid = uuid.uuid4()
        self.generate_webhook_url()
        self.save()
        return self.webhook_uuid
    
    def generate_hmac_secret(self):
        """Generate a new HMAC secret for signature validation"""
        import secrets
        self.hmac_secret = secrets.token_urlsafe(32)
        self.save()
        return self.hmac_secret
    
    def verify_hmac_signature(self, signature, payload):
        """
        Verify HMAC signature from webhook request.
        
        Args:
            signature: Signature from X-ZenithEdge-Signature header (format: "sha256=<hex>")
            payload: Request body bytes
        
        Returns:
            bool: True if signature is valid
        """
        import hmac
        import hashlib
        
        if not self.hmac_secret:
            # No secret configured, skip validation
            return True
        
        try:
            # Extract hex digest from signature
            if signature.startswith('sha256='):
                provided_digest = signature[7:]
            else:
                return False
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.hmac_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison
            return hmac.compare_digest(expected_signature, provided_digest)
        except Exception:
            return False


class SignalEvaluation(models.Model):
    """
    Stores the validation/evaluation result of each incoming signal.
    Tracks which filters passed/failed and the final AI score.
    """
    BLOCKED_REASON_CHOICES = [
        ('passed', 'Passed All Checks'),
        ('news', 'News Blackout'),
        ('prop', 'Prop Challenge Violation'),
        ('score', 'Low AI Score'),
        ('strategy', 'Strategy Not Allowed'),
        ('manual', 'Manual Block'),
        ('multiple', 'Multiple Issues'),
    ]
    
    signal = models.OneToOneField(
        Signal,
        on_delete=models.CASCADE,
        related_name='evaluation',
        help_text="Signal being evaluated"
    )
    passed = models.BooleanField(
        default=False,
        help_text="Whether signal passed all validation checks"
    )
    blocked_reason = models.CharField(
        max_length=20,
        choices=BLOCKED_REASON_CHOICES,
        default='passed',
        help_text="Reason for blocking (if blocked)"
    )
    final_ai_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Final AI score from TradeScorer (0-100)"
    )
    
    # Individual check results
    news_check = models.BooleanField(
        default=True,
        help_text="Passed news blackout check"
    )
    prop_check = models.BooleanField(
        default=True,
        help_text="Passed prop challenge rules check"
    )
    score_check = models.BooleanField(
        default=True,
        help_text="Passed minimum AI score check"
    )
    strategy_check = models.BooleanField(
        default=True,
        help_text="Passed strategy match check"
    )
    
    evaluation_notes = models.TextField(
        blank=True,
        help_text="Detailed evaluation notes/reasons"
    )
    
    # Manual override fields
    is_overridden = models.BooleanField(
        default=False,
        help_text="Whether this evaluation was manually overridden by admin"
    )
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overridden_evaluations',
        help_text="Admin who performed the override"
    )
    overridden_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of override"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signal_evaluation'
        ordering = ['-created_at']
        verbose_name = 'Signal Evaluation'
        verbose_name_plural = 'Signal Evaluations'
    
    def __str__(self):
        status = "✅ PASSED" if self.passed else f"❌ BLOCKED ({self.get_blocked_reason_display()})"
        return f"{status} - Signal #{self.signal.id} (Score: {self.final_ai_score or 'N/A'})"
    
    def get_failed_checks(self):
        """Return list of failed check names"""
        failed = []
        if not self.news_check:
            failed.append('News Blackout')
        if not self.prop_check:
            failed.append('Prop Challenge')
        if not self.score_check:
            failed.append('Low AI Score')
        if not self.strategy_check:
            failed.append('Strategy Mismatch')
        return failed
    
    def create_override_log(self, admin_user, override_reason=''):
        """Create override log entry and update status"""
        from django.utils import timezone
        
        # Create log entry
        SignalOverrideLog.objects.create(
            signal=self.signal,
            admin_user=admin_user,
            old_reason=self.blocked_reason,
            new_reason='manual-override',
            override_reason=override_reason
        )
        
        # Update evaluation
        self.is_overridden = True
        self.overridden_by = admin_user
        self.overridden_at = timezone.now()
        self.passed = True  # Override allows signal to pass
        self.blocked_reason = 'passed'
        self.save()
    
    def get_status_display(self):
        """Return user-friendly status string"""
        if self.is_overridden:
            return 'Overridden'
        elif self.passed:
            return 'Approved'
        else:
            return 'Blocked'
    
    def get_status_icon(self):
        """Return emoji icon for status"""
        if self.is_overridden:
            return '🟣'
        elif self.passed:
            return '🟢'
        else:
            return '🔴'

    def get_badge_color(self):
        """Return Bootstrap color class based on status"""
        if self.passed:
            return 'success'
        elif self.blocked_reason == 'news':
            return 'warning'
        elif self.blocked_reason == 'score':
            return 'info'
        else:
            return 'danger'


class SignalOverrideLog(models.Model):
    """
    Audit log for admin overrides of blocked signals.
    Tracks who overrode what signal and when.
    """
    signal = models.ForeignKey(
        Signal,
        on_delete=models.CASCADE,
        related_name='override_logs',
        help_text="Signal that was overridden"
    )
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='signal_overrides',
        help_text="Admin who performed the override"
    )
    old_reason = models.CharField(
        max_length=20,
        help_text="Original blocked reason before override"
    )
    new_reason = models.CharField(
        max_length=20,
        default='manual-override',
        help_text="New reason after override"
    )
    override_reason = models.TextField(
        blank=True,
        help_text="Admin's explanation for the override"
    )
    override_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'signal_override_log'
        ordering = ['-override_at']
        verbose_name = 'Signal Override Log'
        verbose_name_plural = 'Signal Override Logs'
    
    def __str__(self):
        return f"Override by {self.admin_user.email} - Signal #{self.signal.id} ({self.override_at.strftime('%Y-%m-%d %H:%M')})"


class TradeValidation(models.Model):
    """
    AI Validation results for trading signals.
    
    Stores output from the Truth Filter (validation_engine.py) including
    Truth Index score, validation status, breakdown by criteria, and
    human-readable narrative context from contextualizer.py.
    """
    signal = models.OneToOneField(
        Signal,
        on_delete=models.CASCADE,
        related_name='validation',
        help_text="Associated signal being validated"
    )
    
    # Truth Index score (0-100)
    truth_index = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="AI-calculated truth score (0-100)"
    )
    
    # Validation status
    STATUS_CHOICES = [
        ('approved', 'Approved (≥80)'),
        ('conditional', 'Conditional (60-79)'),
        ('rejected', 'Rejected (<60)'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='rejected',
        help_text="Validation decision"
    )
    
    # Detailed breakdown (JSON)
    breakdown = models.JSONField(
        default=dict,
        help_text="Sub-scores for each validation criterion (technical, volatility, regime, sentiment, historical, psychological)"
    )
    
    # Validation notes (list of strings)
    validation_notes = models.JSONField(
        default=list,
        help_text="List of validation check results and warnings"
    )
    
    # Human-readable narrative context
    context_summary = models.TextField(
        blank=True,
        help_text="AI-generated narrative explaining the signal with context"
    )
    
    # Recommendation text
    recommendation = models.TextField(
        blank=True,
        help_text="AI recommendation for trader action"
    )
    
    # Accuracy tracking (for reputation system)
    accuracy_history = models.JSONField(
        default=dict,
        help_text="Historical accuracy data for reputation scoring"
    )
    
    # Narrative quality metrics (from Narrative Composer)
    quality_metrics = models.JSONField(
        default=dict,
        help_text="Narrative quality metrics: insight_index, linguistic_uniqueness, generation_time_ms"
    )
    
    # KB concepts used in narrative
    kb_concepts_used = models.IntegerField(
        default=0,
        help_text="Number of Knowledge Base concepts used in narrative generation"
    )
    
    # Timestamps
    validated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When validation was performed"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    
    class Meta:
        db_table = 'trade_validation'
        ordering = ['-validated_at']
        verbose_name = 'Trade Validation'
        verbose_name_plural = 'Trade Validations'
        indexes = [
            models.Index(fields=['-truth_index']),
            models.Index(fields=['status']),
            models.Index(fields=['-validated_at']),
        ]
    
    def __str__(self):
        return f"Validation #{self.id} - Signal #{self.signal.id} ({self.truth_index}/100, {self.status})"
    
    def get_status_badge_color(self):
        """Return Bootstrap color class for status badge"""
        if self.status == 'approved':
            return 'success'
        elif self.status == 'conditional':
            return 'warning'
        else:
            return 'danger'
    
    def get_status_icon(self):
        """Return emoji icon for status"""
        if self.status == 'approved':
            return '✅'
        elif self.status == 'conditional':
            return '⚠️'
        else:
            return '❌'
    
    def get_quality_label(self):
        """Return quality description based on truth index"""
        if self.truth_index >= 85:
            return 'High Confidence'
        elif self.truth_index >= 75:
            return 'Solid'
        elif self.truth_index >= 65:
            return 'Moderate'
        elif self.truth_index >= 60:
            return 'Conditional'
        else:
            return 'Low Quality'
    
    def get_breakdown_display(self):
        """Format breakdown scores for display"""
        if not self.breakdown:
            return "No breakdown available"
        
        lines = []
        for key, value in self.breakdown.items():
            label = key.replace('_', ' ').title()
            score = float(value) * 100  # Convert 0-1 to percentage
            lines.append(f"{label}: {score:.0f}%")
        
        return "\n".join(lines)


class ValidationScore(models.Model):
    """
    Aggregated validation statistics and reputation tracking.
    
    Stores monthly/strategy-level accuracy metrics for the AI validation system.
    Used for transparency and continuous improvement.
    """
    # Scope identifiers
    period_month = models.DateField(
        help_text="Month for this aggregation (YYYY-MM-01)"
    )
    strategy_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Strategy name (blank for all strategies)"
    )
    symbol = models.CharField(
        max_length=20,
        blank=True,
        help_text="Trading symbol (blank for all symbols)"
    )
    
    # Validation metrics
    total_signals = models.IntegerField(
        default=0,
        help_text="Total signals validated this period"
    )
    approved_count = models.IntegerField(
        default=0,
        help_text="Number of approved signals (≥80)"
    )
    conditional_count = models.IntegerField(
        default=0,
        help_text="Number of conditional signals (60-79)"
    )
    rejected_count = models.IntegerField(
        default=0,
        help_text="Number of rejected signals (<60)"
    )
    
    # Average scores
    avg_truth_index = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Average truth index for this period"
    )
    avg_technical_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Average technical integrity score"
    )
    avg_sentiment_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Average sentiment coherence score"
    )
    
    # Accuracy tracking (outcome-based)
    validated_outcomes = models.IntegerField(
        default=0,
        help_text="Number of signals with known outcomes"
    )
    correct_predictions = models.IntegerField(
        default=0,
        help_text="Number of correct predictions"
    )
    accuracy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Prediction accuracy percentage"
    )
    
    # False positive/negative tracking
    false_positives = models.IntegerField(
        default=0,
        help_text="Approved signals that failed (SL hit)"
    )
    false_negatives = models.IntegerField(
        default=0,
        help_text="Rejected signals that would have succeeded"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'validation_score'
        ordering = ['-period_month', 'strategy_name']
        verbose_name = 'Validation Score'
        verbose_name_plural = 'Validation Scores'
        unique_together = [['period_month', 'strategy_name', 'symbol']]
        indexes = [
            models.Index(fields=['-period_month']),
            models.Index(fields=['strategy_name']),
            models.Index(fields=['-accuracy_rate']),
        ]
    
    def __str__(self):
        scope = f"{self.strategy_name or 'All'} - {self.symbol or 'All Symbols'}"
        return f"Validation Stats {self.period_month.strftime('%Y-%m')} - {scope}"
    
    def calculate_approval_rate(self):
        """Calculate percentage of approved signals"""
        if self.total_signals == 0:
            return 0
        return (self.approved_count / self.total_signals) * 100
    
    def calculate_rejection_rate(self):
        """Calculate percentage of rejected signals"""
        if self.total_signals == 0:
            return 0
        return (self.rejected_count / self.total_signals) * 100
    
    def get_quality_grade(self):
        """Return letter grade based on accuracy rate"""
        if self.accuracy_rate >= 90:
            return 'A+'
        elif self.accuracy_rate >= 85:
            return 'A'
        elif self.accuracy_rate >= 80:
            return 'B+'
        elif self.accuracy_rate >= 75:
            return 'B'
        elif self.accuracy_rate >= 70:
            return 'C+'
        elif self.accuracy_rate >= 65:
            return 'C'
        else:
            return 'D'
