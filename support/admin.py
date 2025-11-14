from django.contrib import admin
from .models import SupportThread, SupportMessage


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ['from_user', 'is_admin_message', 'created_at']
    fields = ['from_user', 'message', 'is_admin_message', 'attachment', 'created_at']


@admin.register(SupportThread)
class SupportThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'user_email', 'status', 'signal_link', 
                    'has_unread_user_message', 'has_unread_admin_message', 
                    'last_message_at', 'created_at']
    list_filter = ['status', 'has_unread_user_message', 'has_unread_admin_message', 'created_at']
    search_fields = ['subject', 'user__email', 'id']
    readonly_fields = ['created_at', 'updated_at', 'last_message_at']
    inlines = [SupportMessageInline]
    
    fieldsets = (
        ('Thread Info', {
            'fields': ('user', 'subject', 'status', 'signal_id')
        }),
        ('Unread Status', {
            'fields': ('has_unread_user_message', 'has_unread_admin_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def signal_link(self, obj):
        if obj.signal_id:
            return f"Signal #{obj.signal_id}"
        return "-"
    signal_link.short_description = 'Related Signal'


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread_subject', 'sender', 'message_preview', 
                    'is_admin_message', 'created_at']
    list_filter = ['is_admin_message', 'created_at']
    search_fields = ['message', 'thread__subject', 'from_user__email']
    readonly_fields = ['created_at']
    
    def thread_subject(self, obj):
        return f"#{obj.thread.id} - {obj.thread.subject}"
    thread_subject.short_description = 'Thread'
    
    def sender(self, obj):
        if obj.is_admin_message:
            return "Admin"
        return obj.from_user.email if obj.from_user else "Unknown"
    sender.short_description = 'From'
    
    def message_preview(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
