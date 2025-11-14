from django.contrib import admin
from django.utils.html import format_html
from .models import OHLCVCandle, DataSource


@admin.register(OHLCVCandle)
class OHLCVCandleAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'timeframe', 'timestamp', 
        'colored_open', 'colored_high', 'colored_low', 'colored_close',
        'volume', 'source'
    )
    
    list_filter = ('symbol', 'timeframe', 'source', 'timestamp')
    
    search_fields = ('symbol',)
    
    date_hierarchy = 'timestamp'
    
    readonly_fields = ('created_at', 'body_size', 'wick_size', 'is_bullish', 'range_pips')
    
    fieldsets = (
        ('Identification', {
            'fields': ('symbol', 'timeframe', 'timestamp', 'source')
        }),
        ('OHLCV Data', {
            'fields': ('open_price', 'high', 'low', 'close', 'volume')
        }),
        ('Calculated Metrics', {
            'fields': ('body_size', 'wick_size', 'is_bullish', 'range_pips'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def colored_open(self, obj):
        """Display open price with color"""
        return format_html(
            '<span style="color: gray;">{:.5f}</span>',
            obj.open_price
        )
    colored_open.short_description = 'Open'
    colored_open.admin_order_field = 'open_price'
    
    def colored_high(self, obj):
        """Display high price in green"""
        return format_html(
            '<span style="color: green; font-weight: bold;">{:.5f}</span>',
            obj.high
        )
    colored_high.short_description = 'High'
    colored_high.admin_order_field = 'high'
    
    def colored_low(self, obj):
        """Display low price in red"""
        return format_html(
            '<span style="color: red; font-weight: bold;">{:.5f}</span>',
            obj.low
        )
    colored_low.short_description = 'Low'
    colored_low.admin_order_field = 'low'
    
    def colored_close(self, obj):
        """Display close price with bullish/bearish color"""
        color = 'green' if obj.is_bullish else 'red'
        return format_html(
            '<span style="color: {};">{:.5f}</span>',
            color, obj.close
        )
    colored_close.short_description = 'Close'
    colored_close.admin_order_field = 'close'


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'source_type', 'colored_is_active', 
        'last_sync_at', 'colored_status', 'total_candles_synced'
    )
    
    list_filter = ('source_type', 'is_active', 'last_sync_status')
    
    search_fields = ('name',)
    
    readonly_fields = ('last_sync_at', 'total_candles_synced', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'source_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Sync Status', {
            'fields': ('last_sync_at', 'last_sync_status', 'last_sync_message', 'total_candles_synced')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_is_active(self, obj):
        """Display active status with color"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ Inactive</span>'
        )
    colored_is_active.short_description = 'Status'
    colored_is_active.admin_order_field = 'is_active'
    
    def colored_status(self, obj):
        """Display sync status with color"""
        colors = {
            'success': 'green',
            'failed': 'red',
            'pending': 'orange',
        }
        color = colors.get(obj.last_sync_status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.last_sync_status.upper()
        )
    colored_status.short_description = 'Last Sync'
    colored_status.admin_order_field = 'last_sync_status'
