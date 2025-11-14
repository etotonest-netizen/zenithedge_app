from django.contrib import admin
from .models import InsightNotification, NotificationPreference, NotificationDeliveryLog


@admin.register(InsightNotification)
class InsightNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'signal', 'title', 'priority', 'confidence', 'read', 'delivered', 'created_at']
    list_filter = ['read', 'delivered', 'priority', 'created_at']
    search_fields = ['user__email', 'title', 'snippet', 'signal__symbol']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'signal', 'title', 'snippet', 'confidence', 'priority')
        }),
        ('News Context', {
            'fields': ('news_headline',)
        }),
        ('Status', {
            'fields': ('read', 'read_at', 'delivered', 'created_at')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'web_enabled', 'push_enabled', 'email_digest_enabled', 'min_confidence', 'high_priority_only']
    list_filter = ['web_enabled', 'push_enabled', 'email_digest_enabled', 'quiet_hours_enabled', 'high_priority_only']
    search_fields = ['user__email']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channels', {
            'fields': ('web_enabled', 'push_enabled', 'email_digest_enabled')
        }),
        ('Filters', {
            'fields': ('min_confidence', 'strategies_filter', 'symbols_filter', 'high_priority_only')
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_start_time', 'quiet_end_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationDeliveryLog)
class NotificationDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'notification', 'channel', 'success', 'attempted_at']
    list_filter = ['channel', 'success', 'attempted_at']
    search_fields = ['notification__title', 'error_message']
    readonly_fields = ['attempted_at']
    date_hierarchy = 'attempted_at'
