"""
Django Admin Interface for Knowledge Base Management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Source, KnowledgeEntry, ConceptRelationship, 
    CrawlLog, KBSnapshot, QueryCache
)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'trust_level_badge', 'total_entries', 'last_crawled', 'active_status']
    list_filter = ['trust_level', 'active', 'last_crawled']
    search_fields = ['name', 'domain', 'base_url']
    ordering = ['-trust_level', 'name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'domain', 'base_url', 'trust_level', 'active')
        }),
        ('Crawl Configuration', {
            'fields': ('respect_robots_txt', 'rate_limit_seconds', 'max_depth')
        }),
        ('Statistics', {
            'fields': ('last_crawled', 'total_entries'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['last_crawled', 'total_entries']
    
    def trust_level_badge(self, obj):
        colors = {
            'high': '#10b981',
            'medium': '#f59e0b',
            'low': '#6b7280',
            'blacklisted': '#ef4444'
        }
        color = colors.get(obj.trust_level, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem;">{}</span>',
            color, obj.get_trust_level_display()
        )
    trust_level_badge.short_description = 'Trust Level'
    
    def active_status(self, obj):
        if obj.active:
            return format_html('<span style="color: #10b981;">✅ Active</span>')
        return format_html('<span style="color: #ef4444;">❌ Inactive</span>')
    active_status.short_description = 'Status'


@admin.register(KnowledgeEntry)
class KnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = ['term', 'category_badge', 'quality_indicator', 'difficulty', 'source_link', 'view_count', 'is_verified_badge']
    list_filter = ['category', 'difficulty', 'is_verified', 'is_active', 'source__trust_level', 'created_at']
    search_fields = ['term', 'aliases', 'summary', 'definition']
    ordering = ['-quality_score', 'term']
    
    fieldsets = (
        ('Core Content', {
            'fields': ('term', 'aliases', 'summary', 'definition', 'examples')
        }),
        ('Classification', {
            'fields': ('category', 'difficulty', 'asset_classes')
        }),
        ('Quality Metrics', {
            'fields': ('quality_score', 'relevance_score', 'completeness_score'),
            'classes': ('collapse',)
        }),
        ('Provenance', {
            'fields': ('source', 'source_url', 'crawl_date', 'license_info')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'version')
        }),
        ('Analytics', {
            'fields': ('view_count', 'last_used'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['view_count', 'last_used', 'crawl_date', 'created_at', 'updated_at']
    
    actions = ['verify_entries', 'deactivate_entries', 'activate_entries']
    
    def category_badge(self, obj):
        colors = {
            'smc': '#3b82f6',
            'ict': '#8b5cf6',
            'ta': '#10b981',
            'risk': '#f59e0b',
            'orderflow': '#06b6d4',
            'other': '#6b7280'
        }
        color = colors.get(obj.category, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def quality_indicator(self, obj):
        score = obj.quality_score
        if score >= 0.8:
            color, icon = '#10b981', '⭐⭐⭐'
        elif score >= 0.6:
            color, icon = '#f59e0b', '⭐⭐'
        elif score >= 0.4:
            color, icon = '#6b7280', '⭐'
        else:
            color, icon = '#ef4444', '⚠️'
        
        return format_html(
            '<span style="color: {}; font-weight: 600;">{} {:.2f}</span>',
            color, icon, score
        )
    quality_indicator.short_description = 'Quality'
    
    def source_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank" style="color: #3b82f6;">{}</a>',
            obj.source_url, obj.source.name
        )
    source_link.short_description = 'Source'
    
    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: #10b981;">✓ Verified</span>')
        return format_html('<span style="color: #6b7280;">○ Unverified</span>')
    is_verified_badge.short_description = 'Verified'
    
    def verify_entries(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} entries marked as verified')
    verify_entries.short_description = 'Mark as verified'
    
    def deactivate_entries(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} entries deactivated')
    deactivate_entries.short_description = 'Deactivate entries'
    
    def activate_entries(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} entries activated')
    activate_entries.short_description = 'Activate entries'


@admin.register(ConceptRelationship)
class ConceptRelationshipAdmin(admin.ModelAdmin):
    list_display = ['source_term', 'relationship_type_badge', 'target_term', 'strength_indicator', 'is_verified_badge']
    list_filter = ['relationship_type', 'is_verified', 'is_auto_detected']
    search_fields = ['source_concept__term', 'target_concept__term', 'description']
    ordering = ['-strength', 'relationship_type']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('source_concept', 'target_concept', 'relationship_type', 'strength')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('is_auto_detected', 'is_verified', 'created_at')
        })
    )
    
    readonly_fields = ['created_at']
    
    def source_term(self, obj):
        return obj.source_concept.term
    source_term.short_description = 'Source'
    
    def target_term(self, obj):
        return obj.target_concept.term
    target_term.short_description = 'Target'
    
    def relationship_type_badge(self, obj):
        colors = {
            'related_to': '#3b82f6',
            'is_subconcept_of': '#8b5cf6',
            'prerequisite_for': '#10b981',
            'contraindicates': '#ef4444',
            'common_with': '#f59e0b',
            'alternative_to': '#06b6d4'
        }
        color = colors.get(obj.relationship_type, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem;">{}</span>',
            color, obj.get_relationship_type_display()
        )
    relationship_type_badge.short_description = 'Type'
    
    def strength_indicator(self, obj):
        strength = obj.strength
        width = int(strength * 100)
        color = '#10b981' if strength >= 0.7 else '#f59e0b' if strength >= 0.4 else '#6b7280'
        return format_html(
            '<div style="background: #e5e7eb; border-radius: 4px; width: 100px; height: 8px;">'
            '<div style="background: {}; width: {}%; height: 100%; border-radius: 4px;"></div>'
            '</div>',
            color, width
        )
    strength_indicator.short_description = 'Strength'
    
    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: #10b981;">✓</span>')
        return format_html('<span style="color: #6b7280;">○</span>')
    is_verified_badge.short_description = 'Verified'


@admin.register(CrawlLog)
class CrawlLogAdmin(admin.ModelAdmin):
    list_display = ['source', 'started_at', 'status_badge', 'entries_created', 'entries_updated', 'duration_display']
    list_filter = ['status', 'source', 'started_at']
    search_fields = ['source__name', 'error_log']
    ordering = ['-started_at']
    
    fieldsets = (
        ('Crawl Info', {
            'fields': ('source', 'started_at', 'completed_at', 'status')
        }),
        ('Statistics', {
            'fields': ('urls_discovered', 'urls_crawled', 'entries_created', 'entries_updated', 'entries_skipped')
        }),
        ('Errors', {
            'fields': ('errors_count', 'error_log'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('config_snapshot',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['started_at', 'completed_at']
    
    def status_badge(self, obj):
        colors = {
            'completed': '#10b981',
            'running': '#3b82f6',
            'failed': '#ef4444',
            'partial': '#f59e0b',
            'pending': '#6b7280'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.85rem;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        return obj.duration()
    duration_display.short_description = 'Duration'


@admin.register(KBSnapshot)
class KBSnapshotAdmin(admin.ModelAdmin):
    list_display = ['version', 'created_at', 'total_entries', 'total_relationships', 'is_current_badge']
    list_filter = ['is_current', 'created_at']
    ordering = ['-version']
    
    fieldsets = (
        ('Version Info', {
            'fields': ('version', 'created_at', 'is_current')
        }),
        ('Statistics', {
            'fields': ('total_entries', 'total_relationships', 'total_sources')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Backup', {
            'fields': ('backup_path',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']
    
    def is_current_badge(self, obj):
        if obj.is_current:
            return format_html('<span style="color: #10b981; font-weight: 600;">✓ Current</span>')
        return ''
    is_current_badge.short_description = 'Current'


@admin.register(QueryCache)
class QueryCacheAdmin(admin.ModelAdmin):
    list_display = ['query_text_short', 'symbol', 'hit_count', 'last_accessed', 'expires_at']
    list_filter = ['symbol', 'expires_at', 'created_at']
    search_fields = ['query_text', 'symbol']
    ordering = ['-hit_count', '-last_accessed']
    
    fieldsets = (
        ('Query', {
            'fields': ('query_text', 'query_hash', 'symbol')
        }),
        ('Cache Data', {
            'fields': ('results', 'concept_tags'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('hit_count', 'created_at', 'last_accessed', 'expires_at')
        })
    )
    
    readonly_fields = ['query_hash', 'hit_count', 'created_at', 'last_accessed']
    
    actions = ['clear_expired_cache']
    
    def query_text_short(self, obj):
        text = obj.query_text[:60]
        if len(obj.query_text) > 60:
            text += '...'
        return text
    query_text_short.short_description = 'Query'
    
    def clear_expired_cache(self, request, queryset):
        from django.utils import timezone
        deleted = queryset.filter(expires_at__lt=timezone.now()).delete()[0]
        self.message_user(request, f'{deleted} expired cache entries cleared')
    clear_expired_cache.short_description = 'Clear expired cache'
