"""
ZenNews Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import NewsEvent, NewsTopic, NewsAlert


@admin.register(NewsEvent)
class NewsEventAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'headline_short', 'sentiment_badge', 'impact_badge', 'source', 'timestamp', 'created_at']
    list_filter = ['impact_level', 'symbol', 'source', 'timestamp']
    search_fields = ['headline', 'symbol', 'topic']
    readonly_fields = ['id', 'content_hash', 'created_at']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('News Content', {
            'fields': ('headline', 'source', 'source_url', 'timestamp')
        }),
        ('Analysis', {
            'fields': ('symbol', 'sentiment', 'impact_level', 'topic')
        }),
        ('Metadata', {
            'fields': ('id', 'content_hash', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def headline_short(self, obj):
        return obj.headline[:80] + '...' if len(obj.headline) > 80 else obj.headline
    headline_short.short_description = 'Headline'
    
    def sentiment_badge(self, obj):
        color = 'green' if obj.sentiment > 0.3 else 'red' if obj.sentiment < -0.3 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            f'{obj.sentiment:.2f}'
        )
    sentiment_badge.short_description = 'Sentiment'
    sentiment_badge.admin_order_field = 'sentiment'
    
    def impact_badge(self, obj):
        colors = {'high': 'red', 'medium': 'orange', 'low': 'blue'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.impact_level, 'gray'),
            obj.impact_level.upper()
        )
    impact_badge.short_description = 'Impact'
    impact_badge.admin_order_field = 'impact_level'


@admin.register(NewsTopic)
class NewsTopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'news_count', 'avg_sentiment', 'last_updated']
    search_fields = ['name', 'keyword_list']
    readonly_fields = ['last_updated', 'created_at']
    ordering = ['-news_count']


@admin.register(NewsAlert)
class NewsAlertAdmin(admin.ModelAdmin):
    list_display = ['news_event_symbol', 'alert_type', 'message_short', 'is_read', 'created_at']
    list_filter = ['alert_type', 'is_read', 'created_at']
    search_fields = ['message', 'news_event__headline']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def news_event_symbol(self, obj):
        return obj.news_event.symbol
    news_event_symbol.short_description = 'Symbol'
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'
