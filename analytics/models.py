from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class DailyPerformanceCache(models.Model):
    """
    Cached daily performance statistics to reduce dashboard query load.
    Updated by a daily aggregation job (Celery or cron).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_performance_cache'
    )
    date = models.DateField(db_index=True, help_text="Date for this performance snapshot")
    
    # Signal counts
    total_signals = models.IntegerField(default=0)
    allowed_signals = models.IntegerField(default=0)
    rejected_signals = models.IntegerField(default=0)
    
    # Trade outcomes
    win_count = models.IntegerField(default=0)
    loss_count = models.IntegerField(default=0)
    breakeven_count = models.IntegerField(default=0)
    
    # Performance metrics
    total_pips = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    avg_ai_score = models.FloatField(default=0.0)
    
    # Best performers
    best_strategy = models.CharField(max_length=50, blank=True)
    best_session = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_daily_performance_cache'
        ordering = ['-date']
        verbose_name = 'Daily Performance Cache'
        verbose_name_plural = 'Daily Performance Caches'
        unique_together = [['user', 'date']]
        indexes = [
            models.Index(fields=['user', '-date'], name='daily_perf_user_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"
    
    @property
    def win_rate(self):
        """Calculate win rate"""
        total = self.win_count + self.loss_count
        if total == 0:
            return 0.0
        return (self.win_count / total) * 100


class BacktestRun(models.Model):
    """
    Stores a historical backtest run with parameters and results.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='backtest_runs'
    )
    
    # Backtest Parameters
    strategy = models.CharField(max_length=100, help_text="Trading strategy name")
    symbol = models.CharField(max_length=20, blank=True, help_text="Symbol filter (blank = all)")
    timeframe = models.CharField(max_length=10, blank=True, help_text="Timeframe filter")
    start_date = models.DateField(help_text="Start date for backtest period")
    end_date = models.DateField(help_text="End date for backtest period")
    
    # Additional filters stored as JSON
    params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional parameters: min_score, ignore_news, etc."
    )
    
    # Backtest Results
    total_trades = models.IntegerField(default=0, help_text="Total number of trades in backtest")
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0, help_text="Win rate as percentage (0-100)")
    avg_rr = models.FloatField(default=0.0, help_text="Average Risk/Reward ratio")
    max_drawdown = models.FloatField(default=0.0, help_text="Maximum drawdown percentage")
    profit_factor = models.FloatField(default=0.0, help_text="Profit factor (gross profit / gross loss)")
    total_pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total P&L in pips/points")
    
    # Equity curve data (stored as JSON for charting)
    equity_curve = models.JSONField(
        default=list,
        blank=True,
        help_text="List of equity values over time [{date, equity}, ...]"
    )
    
    # Trade details (stored as JSON)
    trade_details = models.JSONField(
        default=list,
        blank=True,
        help_text="List of individual trade results for replay"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_saved = models.BooleanField(
        default=False,
        help_text="User explicitly saved this backtest for future reference"
    )
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional name for saved backtests"
    )
    
    class Meta:
        db_table = 'analytics_backtest_run'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['strategy', 'symbol']),
        ]
    
    def __str__(self):
        symbol_part = f" {self.symbol}" if self.symbol else " (All)"
        return f"{self.strategy}{symbol_part} - {self.start_date} to {self.end_date}"
    
    def get_summary(self):
        """Return formatted summary for display"""
        return {
            'total_trades': self.total_trades,
            'win_rate': f"{self.win_rate:.2f}%",
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_rr': f"{self.avg_rr:.2f}",
            'max_drawdown': f"{self.max_drawdown:.2f}%",
            'profit_factor': f"{self.profit_factor:.2f}",
            'total_pnl': f"{self.total_pnl:+.2f}",
            'period': f"{self.start_date} to {self.end_date}",
        }
    
    def get_performance_badge(self):
        """Return color badge based on win rate"""
        if self.win_rate >= 70:
            return 'success'
        elif self.win_rate >= 55:
            return 'info'
        elif self.win_rate >= 45:
            return 'warning'
        else:
            return 'danger'
