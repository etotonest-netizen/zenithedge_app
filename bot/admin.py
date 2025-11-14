from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import csv
import io

from .models import BotQA, BotConversation, BotSettings


@admin.register(BotQA)
class BotQAAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'category', 'priority', 'usage_count', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer', 'keywords']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    list_editable = ['is_active', 'priority']
    actions = ['import_csv', 'export_csv', 'activate_selected', 'deactivate_selected']
    
    fieldsets = (
        ('Question & Answer', {
            'fields': ('question', 'answer', 'category')
        }),
        ('Matching Settings', {
            'fields': ('keywords', 'priority', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'
    
    def import_csv(self, request, queryset):
        """Custom action to import Q&As from CSV"""
        if 'apply' in request.POST:
            csv_file = request.FILES.get('csv_file')
            
            if not csv_file:
                self.message_user(request, "No file selected", level=messages.ERROR)
                return redirect("admin:bot_botqa_changelist")
            
            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "File must be CSV format", level=messages.ERROR)
                return redirect("admin:bot_botqa_changelist")
            
            try:
                # Read CSV file
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                imported_count = 0
                for row in reader:
                    BotQA.objects.create(
                        question=row.get('question', ''),
                        answer=row.get('answer', ''),
                        category=row.get('category', 'general'),
                        keywords=row.get('keywords', ''),
                        priority=int(row.get('priority', 0)),
                        is_active=row.get('is_active', 'True').lower() == 'true',
                        created_by=request.user
                    )
                    imported_count += 1
                
                self.message_user(
                    request,
                    f"Successfully imported {imported_count} Q&A entries",
                    level=messages.SUCCESS
                )
                return redirect("admin:bot_botqa_changelist")
                
            except Exception as e:
                self.message_user(
                    request,
                    f"Error importing CSV: {str(e)}",
                    level=messages.ERROR
                )
                return redirect("admin:bot_botqa_changelist")
        
        # Show upload form
        return render(request, 'admin/bot/import_csv.html', {
            'title': 'Import Q&As from CSV',
            'opts': self.model._meta,
        })
    
    import_csv.short_description = "Import Q&As from CSV"
    
    def export_csv(self, request, queryset):
        """Export selected Q&As to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="botqa_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['question', 'answer', 'category', 'keywords', 'priority', 'is_active'])
        
        for qa in queryset:
            writer.writerow([
                qa.question,
                qa.answer,
                qa.category,
                qa.keywords,
                qa.priority,
                qa.is_active
            ])
        
        self.message_user(request, f"Exported {queryset.count()} Q&A entries")
        return response
    
    export_csv.short_description = "Export selected to CSV"
    
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} Q&A entries")
    activate_selected.short_description = "Activate selected Q&As"
    
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} Q&A entries")
    deactivate_selected.short_description = "Deactivate selected Q&As"
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BotConversation)
class BotConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message_preview', 'confidence_score', 'matched_qa', 'created_at']
    list_filter = ['created_at', 'confidence_score']
    search_fields = ['user__username', 'user_message', 'bot_response']
    readonly_fields = ['user', 'session_id', 'user_message', 'bot_response', 
                       'matched_qa', 'confidence_score', 'created_at']
    date_hierarchy = 'created_at'
    actions = ['delete_old_conversations']
    
    def message_preview(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    message_preview.short_description = 'Message'
    
    def delete_old_conversations(self, request, queryset):
        """Delete conversations older than 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted = BotConversation.objects.filter(created_at__lt=cutoff_date).delete()
        
        self.message_user(
            request,
            f"Deleted {deleted[0]} old conversations",
            level=messages.SUCCESS
        )
    
    delete_old_conversations.short_description = "Delete conversations older than 30 days"
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ['match_threshold', 'enable_user_stats', 'enable_signal_queries', 
                    'enable_learning', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Matching Settings', {
            'fields': ('match_threshold', 'default_fallback_message')
        }),
        ('Feature Toggles', {
            'fields': ('enable_user_stats', 'enable_signal_queries', 'enable_learning')
        }),
        ('Data Management', {
            'fields': ('max_conversation_history',)
        }),
        ('Metadata', {
            'fields': ('updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not BotSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion of settings
