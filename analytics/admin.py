from django.contrib import admin
from .models import BacktestRun


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_email', 'strategy', 'symbol', 'timeframe', 'date_range', 'total_trades', 'win_rate', 'is_saved', 'created_at']
    list_filter = ['is_saved', 'strategy', 'created_at', 'user']
    search_fields = ['user__email', 'strategy', 'symbol', 'name']
    readonly_fields = ['created_at', 'updated_at', 'equity_curve', 'trade_details']
    
    fieldsets = (
        ('Backtest Parameters', {
            'fields': ('user', 'strategy', 'symbol', 'timeframe', 'start_date', 'end_date', 'params')
        }),
        ('Results', {
            'fields': ('total_trades', 'winning_trades', 'losing_trades', 'win_rate', 'avg_rr', 'max_drawdown', 'profit_factor', 'total_pnl')
        }),
        ('Data', {
            'fields': ('equity_curve', 'trade_details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_saved', 'name', 'created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def date_range(self, obj):
        return f"{obj.start_date} to {obj.end_date}"
    date_range.short_description = 'Date Range'
