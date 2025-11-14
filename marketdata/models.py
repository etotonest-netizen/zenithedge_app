from django.db import models
from django.utils import timezone


class OHLCVCandle(models.Model):
    """
    Historical OHLCV (Open, High, Low, Close, Volume) candle data.
    
    Used by AutopsyLoop to evaluate real-world outcomes of trading insights.
    Stores tick/candle data at various timeframes for deterministic replay.
    """
    
    symbol = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Trading pair (e.g., EURUSD, GBPUSD, BTCUSD)"
    )
    
    timeframe = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Candle timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)"
    )
    
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Candle open time (UTC)"
    )
    
    # Price data (high precision for forex)
    open_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Opening price"
    )
    
    high = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Highest price during period"
    )
    
    low = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Lowest price during period"
    )
    
    close = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Closing price"
    )
    
    volume = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Trading volume (may not be available for forex)"
    )
    
    # Metadata
    source = models.CharField(
        max_length=50,
        default='manual',
        help_text="Data source (broker API, CSV import, etc.)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'marketdata_ohlcv'
        verbose_name = 'OHLCV Candle'
        verbose_name_plural = 'OHLCV Candles'
        
        # Ensure no duplicate candles for same symbol/timeframe/timestamp
        unique_together = ('symbol', 'timeframe', 'timestamp')
        
        # Optimize queries by symbol, timeframe, and timestamp range
        indexes = [
            models.Index(fields=['symbol', 'timeframe', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.symbol} {self.timeframe} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def body_size(self):
        """Calculate candle body size (close - open)"""
        return abs(self.close - self.open_price)
    
    @property
    def wick_size(self):
        """Calculate total wick size (high-low - body)"""
        return (self.high - self.low) - self.body_size
    
    @property
    def is_bullish(self):
        """True if close > open"""
        return self.close > self.open_price
    
    @property
    def range_pips(self):
        """Calculate range in pips (forex-oriented)"""
        pip_multiplier = 100 if 'JPY' in self.symbol else 10000
        return float((self.high - self.low) * pip_multiplier)


class DataSource(models.Model):
    """
    Track data sources and their sync status.
    """
    
    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('broker_api', 'Broker API'),
            ('csv_import', 'CSV Import'),
            ('manual', 'Manual Entry'),
            ('websocket', 'WebSocket Stream'),
        ],
        default='broker_api'
    )
    
    is_active = models.BooleanField(default=True)
    
    # Connection details (stored as JSON)
    config = models.JSONField(
        default=dict,
        help_text="API keys, endpoints, etc. (encrypted in production)"
    )
    
    # Sync tracking
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, default='pending')
    last_sync_message = models.TextField(blank=True)
    
    # Stats
    total_candles_synced = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'marketdata_datasource'
        verbose_name = 'Data Source'
        verbose_name_plural = 'Data Sources'
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    def mark_sync_success(self, candles_synced=0):
        """Mark sync as successful"""
        self.last_sync_at = timezone.now()
        self.last_sync_status = 'success'
        self.total_candles_synced += candles_synced
        self.save()
    
    def mark_sync_failed(self, error_message):
        """Mark sync as failed"""
        self.last_sync_at = timezone.now()
        self.last_sync_status = 'failed'
        self.last_sync_message = error_message
        self.save()
