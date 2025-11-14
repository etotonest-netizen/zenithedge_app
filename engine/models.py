"""
Engine Models for Market Data Storage and Backtesting

Models:
- MarketBar: OHLCV candlestick data storage
- BacktestRun: Backtest configuration and results
- BacktestTrade: Individual trades from backtesting
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class MarketBar(models.Model):
    """
    OHLCV candlestick storage for multiple symbols and timeframes.
    Optimized for fast retrieval with composite index.
    """
    symbol = models.CharField(max_length=20, db_index=True, help_text="Trading symbol (e.g., EURUSD, BTCUSD)")
    timeframe = models.CharField(max_length=10, db_index=True, help_text="Timeframe (1, 5, 15, 30, 1H, 4H, D, W, M)")
    timestamp = models.DateTimeField(db_index=True, help_text="Bar open time (UTC)")
    
    # OHLCV data
    open = models.DecimalField(max_digits=20, decimal_places=8, help_text="Open price")
    high = models.DecimalField(max_digits=20, decimal_places=8, help_text="High price")
    low = models.DecimalField(max_digits=20, decimal_places=8, help_text="Low price")
    close = models.DecimalField(max_digits=20, decimal_places=8, help_text="Close price")
    volume = models.DecimalField(max_digits=20, decimal_places=2, default=0, help_text="Volume")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'engine_market_bar'
        ordering = ['symbol', 'timeframe', '-timestamp']
        unique_together = ('symbol', 'timeframe', 'timestamp')
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'timestamp'], name='marketbar_lookup_idx'),
            models.Index(fields=['timestamp'], name='marketbar_time_idx'),
        ]
        verbose_name = 'Market Bar'
        verbose_name_plural = 'Market Bars'
    
    def __str__(self):
        return f"{self.symbol} {self.timeframe} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def ohlc_dict(self):
        """Return OHLC as dictionary for easy processing"""
        return {
            'timestamp': self.timestamp,
            'open': float(self.open),
            'high': float(self.high),
            'low': float(self.low),
            'close': float(self.close),
            'volume': float(self.volume),
        }


class BacktestRun(models.Model):
    """
    Backtest configuration and aggregate results.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=200, help_text="Descriptive name for this backtest")
    strategy = models.CharField(max_length=50, help_text="Strategy name (SMC, ICT, Trend, etc.)")
    symbol = models.CharField(max_length=20, help_text="Trading symbol")
    timeframe = models.CharField(max_length=10, help_text="Primary timeframe")
    
    # Backtest parameters
    start_date = models.DateTimeField(help_text="Backtest start date")
    end_date = models.DateTimeField(help_text="Backtest end date")
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=10000, help_text="Starting capital")
    risk_per_trade = models.DecimalField(max_digits=5, decimal_places=2, default=2.0, 
                                        validators=[MinValueValidator(0.1), MaxValueValidator(100)],
                                        help_text="Risk percentage per trade (0.1-100)")
    commission = models.DecimalField(max_digits=6, decimal_places=4, default=0.0010, help_text="Commission per trade (e.g., 0.001 = 0.1%)")
    
    # Strategy-specific parameters (JSON)
    parameters = models.JSONField(default=dict, blank=True, help_text="Strategy-specific parameters")
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_trades = models.IntegerField(default=0, help_text="Total number of trades")
    winning_trades = models.IntegerField(default=0, help_text="Number of winning trades")
    losing_trades = models.IntegerField(default=0, help_text="Number of losing trades")
    
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total profit/loss")
    total_pnl_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total P&L %")
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Maximum drawdown %")
    max_drawdown_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Maximum drawdown value")
    
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Win rate %")
    profit_factor = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Profit factor (gross profit / gross loss)")
    average_win = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Average winning trade")
    average_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Average losing trade")
    expectancy = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Expectancy per trade")
    
    sharpe_ratio = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=True, blank=True, help_text="Sharpe ratio")
    
    # Execution details
    execution_time = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Execution time in seconds")
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='engine_backtest_runs')
    
    class Meta:
        db_table = 'engine_backtest_run'
        ordering = ['-created_at']
        verbose_name = 'Backtest Run'
        verbose_name_plural = 'Backtest Runs'
    
    def __str__(self):
        return f"{self.name} ({self.symbol} {self.timeframe}) - {self.status}"
    
    @property
    def metrics_dict(self):
        """Return all metrics as dictionary"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': float(self.total_pnl),
            'total_pnl_percent': float(self.total_pnl_percent),
            'max_drawdown': float(self.max_drawdown),
            'win_rate': float(self.win_rate),
            'profit_factor': float(self.profit_factor),
            'average_win': float(self.average_win),
            'average_loss': float(self.average_loss),
            'expectancy': float(self.expectancy),
            'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else None,
        }


class BacktestTrade(models.Model):
    """
    Individual trade from backtesting simulation.
    """
    SIDE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    
    EXIT_REASON_CHOICES = [
        ('tp', 'Take Profit Hit'),
        ('sl', 'Stop Loss Hit'),
        ('timeout', 'Timeout'),
        ('manual', 'Manual Close'),
        ('signal', 'Opposite Signal'),
    ]
    
    backtest_run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='trades')
    
    # Trade identification
    trade_number = models.IntegerField(help_text="Sequential trade number in backtest")
    symbol = models.CharField(max_length=20)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    
    # Entry
    entry_time = models.DateTimeField(help_text="Entry timestamp")
    entry_price = models.DecimalField(max_digits=20, decimal_places=8, help_text="Entry price")
    entry_reason = models.CharField(max_length=100, help_text="Entry signal reason")
    
    # Position sizing
    position_size = models.DecimalField(max_digits=20, decimal_places=8, help_text="Position size (units)")
    risk_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Risk amount in base currency")
    
    # Exit levels
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, help_text="Stop loss price")
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, help_text="Take profit price")
    
    # Exit (null if still open)
    exit_time = models.DateTimeField(null=True, blank=True, help_text="Exit timestamp")
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Exit price")
    exit_reason = models.CharField(max_length=20, choices=EXIT_REASON_CHOICES, null=True, blank=True)
    
    # Results
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Profit/loss in base currency")
    pnl_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="P&L as % of risk")
    pnl_pips = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="P&L in pips")
    commission_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total commission")
    
    # Trade metadata
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Signal confidence (0-100)")
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="AI/ZenBot score")
    strategy_tags = models.JSONField(default=list, blank=True, help_text="Strategy-specific tags")
    structure_data = models.JSONField(default=dict, blank=True, help_text="Market structure data at entry")
    
    # MAE/MFE (Maximum Adverse/Favorable Excursion)
    mae = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Max adverse excursion in pips")
    mfe = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Max favorable excursion in pips")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'engine_backtest_trade'
        ordering = ['backtest_run', 'trade_number']
        indexes = [
            models.Index(fields=['backtest_run', 'trade_number'], name='bt_trade_lookup_idx'),
            models.Index(fields=['entry_time'], name='bt_entry_time_idx'),
        ]
        verbose_name = 'Backtest Trade'
        verbose_name_plural = 'Backtest Trades'
    
    def __str__(self):
        return f"Trade #{self.trade_number}: {self.symbol} {self.side} @ {self.entry_price}"
    
    @property
    def duration_minutes(self):
        """Calculate trade duration in minutes"""
        if self.exit_time:
            delta = self.exit_time - self.entry_time
            return delta.total_seconds() / 60
        return None
    
    @property
    def r_multiple(self):
        """Calculate R-multiple (profit as multiple of risk)"""
        if self.risk_amount and self.risk_amount > 0:
            return float(self.pnl / self.risk_amount)
        return 0
