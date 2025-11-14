from django.contrib import admin
from .models import MarketBar, BacktestRun, BacktestTrade


@admin.register(MarketBar)
class MarketBarAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume')
    list_filter = ('symbol', 'timeframe', 'timestamp')
    search_fields = ('symbol',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Identification', {
            'fields': ('symbol', 'timeframe', 'timestamp')
        }),
        ('OHLCV Data', {
            'fields': ('open', 'high', 'low', 'close', 'volume')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy', 'symbol', 'timeframe', 'status', 'total_trades', 
                   'win_rate', 'total_pnl_percent', 'created_at')
    list_filter = ('status', 'strategy', 'symbol', 'timeframe', 'created_at')
    search_fields = ('name', 'symbol', 'strategy')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    readonly_fields = ('status', 'total_trades', 'winning_trades', 'losing_trades',
                      'total_pnl', 'total_pnl_percent', 'max_drawdown', 'win_rate',
                      'profit_factor', 'average_win', 'average_loss', 'expectancy',
                      'sharpe_ratio', 'execution_time', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'strategy', 'symbol', 'timeframe', 'created_by')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Risk Parameters', {
            'fields': ('initial_capital', 'risk_per_trade', 'commission')
        }),
        ('Strategy Parameters', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('status', 'total_trades', 'winning_trades', 'losing_trades',
                      'total_pnl', 'total_pnl_percent', 'max_drawdown', 'max_drawdown_value')
        }),
        ('Performance Metrics', {
            'fields': ('win_rate', 'profit_factor', 'average_win', 'average_loss',
                      'expectancy', 'sharpe_ratio'),
            'classes': ('collapse',)
        }),
        ('Execution', {
            'fields': ('execution_time', 'error_message', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BacktestTrade)
class BacktestTradeAdmin(admin.ModelAdmin):
    list_display = ('trade_number', 'symbol', 'side', 'entry_time', 'entry_price',
                   'exit_price', 'status', 'pnl', 'pnl_pips', 'exit_reason')
    list_filter = ('backtest_run', 'symbol', 'side', 'status', 'exit_reason')
    search_fields = ('symbol', 'entry_reason')
    date_hierarchy = 'entry_time'
    ordering = ('-entry_time',)
    
    readonly_fields = ('backtest_run', 'trade_number', 'pnl', 'pnl_percent', 
                      'pnl_pips', 'commission_paid', 'mae', 'mfe', 'created_at')
    
    fieldsets = (
        ('Trade Identification', {
            'fields': ('backtest_run', 'trade_number', 'symbol', 'side')
        }),
        ('Entry', {
            'fields': ('entry_time', 'entry_price', 'entry_reason', 
                      'confidence_score', 'ai_score')
        }),
        ('Position', {
            'fields': ('position_size', 'risk_amount', 'stop_loss', 'take_profit')
        }),
        ('Exit', {
            'fields': ('exit_time', 'exit_price', 'exit_reason', 'status')
        }),
        ('Results', {
            'fields': ('pnl', 'pnl_percent', 'pnl_pips', 'commission_paid', 'mae', 'mfe')
        }),
        ('Metadata', {
            'fields': ('strategy_tags', 'structure_data', 'created_at'),
            'classes': ('collapse',)
        }),
    )
