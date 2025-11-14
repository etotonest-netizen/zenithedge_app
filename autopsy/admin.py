"""
AutopsyLoop Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    InsightAudit, AuditRCA, AutopsyJob, RetrainRequest, 
    ModelVersion, LabelingRule
)


@admin.register(InsightAudit)
class InsightAuditAdmin(admin.ModelAdmin):
    list_display = ['id', 'insight_link', 'symbol_display', 'outcome_badge', 'horizon', 
                    'pnl_display', 'evaluated_at', 'needs_manual_review']
    list_filter = ['outcome', 'horizon', 'needs_manual_review', 'replay_verified', 
                   'user_acted', 'evaluated_at']
    search_fields = ['insight__symbol', 'insight__id', 'reviewer_notes']
    readonly_fields = ['evaluated_at', 'created_at', 'updated_at', 'replay_snapshot', 
                       'config_snapshot']
    
    fieldsets = [
        ('Core Information', {
            'fields': ['insight', 'user', 'horizon', 'outcome', 'evaluated_at']
        }),
        ('Performance Metrics', {
            'fields': ['pnl_pct', 'max_drawdown', 'duration_minutes', 'risk_reward_actual']
        }),
        ('Price Action', {
            'fields': ['entry_price', 'exit_price', 'high_price', 'low_price', 'slippage_pips']
        }),
        ('Verification', {
            'fields': ['replay_verified', 'user_acted', 'needs_manual_review']
        }),
        ('Human Review', {
            'fields': ['reviewer', 'reviewed_at', 'reviewer_notes'],
            'classes': ['collapse']
        }),
        ('Snapshots', {
            'fields': ['replay_snapshot', 'config_snapshot'],
            'classes': ['collapse']
        }),
    ]
    
    def insight_link(self, obj):
        url = reverse('admin:signals_signal_change', args=[obj.insight.id])
        return format_html('<a href="{}">{}</a>', url, f"Signal #{obj.insight.id}")
    insight_link.short_description = 'Insight'
    
    def symbol_display(self, obj):
        return f"{obj.insight.symbol} ({obj.insight.timeframe})"
    symbol_display.short_description = 'Symbol/TF'
    
    def outcome_badge(self, obj):
        colors = {
            'succeeded': '#28a745',
            'failed': '#dc3545',
            'neutral': '#6c757d',
            'pending': '#ffc107',
            'filtered_out': '#17a2b8',
            'needs_review': '#fd7e14'
        }
        color = colors.get(obj.outcome, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, obj.get_outcome_display()
        )
    outcome_badge.short_description = 'Outcome'
    
    def pnl_display(self, obj):
        if obj.pnl_pct is None:
            return '-'
        color = '#28a745' if obj.pnl_pct > 0 else '#dc3545'
        sign = '+' if obj.pnl_pct >= 0 else ''
        formatted_pnl = f"{float(obj.pnl_pct):.2f}"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}{}%</span>',
            color, sign, formatted_pnl
        )
    pnl_display.short_description = 'P&L'
    
    actions = ['mark_for_review', 'mark_reviewed']
    
    def mark_for_review(self, request, queryset):
        updated = queryset.update(needs_manual_review=True)
        self.message_user(request, f'{updated} audits marked for review.')
    mark_for_review.short_description = 'Mark for manual review'
    
    def mark_reviewed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            needs_manual_review=False,
            reviewer=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} audits marked as reviewed.')
    mark_reviewed.short_description = 'Mark as reviewed'


@admin.register(AuditRCA)
class AuditRCAAdmin(admin.ModelAdmin):
    list_display = ['id', 'audit_link', 'cause_badge', 'confidence_bar', 'rank', 'created_at']
    list_filter = ['cause', 'rank', 'created_at']
    search_fields = ['audit__insight__symbol', 'summary']
    readonly_fields = ['created_at', 'evidence', 'explain_shap', 'news_references']
    
    fieldsets = [
        ('Root Cause', {
            'fields': ['audit', 'cause', 'confidence', 'rank']
        }),
        ('Evidence', {
            'fields': ['summary', 'evidence', 'explain_shap', 'news_references']
        }),
    ]
    
    def audit_link(self, obj):
        url = reverse('admin:autopsy_insightaudit_change', args=[obj.audit.id])
        return format_html('<a href="{}">Audit #{}</a>', url, obj.audit.id)
    audit_link.short_description = 'Audit'
    
    def cause_badge(self, obj):
        return format_html(
            '<span style="background:#007bff; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            obj.get_cause_display()
        )
    cause_badge.short_description = 'Cause'
    
    def confidence_bar(self, obj):
        width = min(100, float(obj.confidence))
        color = '#28a745' if width > 70 else '#ffc107' if width > 40 else '#dc3545'
        return format_html(
            '<div style="background:#e9ecef; border-radius:3px; width:150px;">'
            '<div style="background:{}; color:white; text-align:center; border-radius:3px; width:{}px; padding:2px;">{}%</div>'
            '</div>',
            color, width * 1.5, int(obj.confidence)
        )
    confidence_bar.short_description = 'Confidence'


@admin.register(AutopsyJob)
class AutopsyJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'status_badge', 'progress_display', 'started_at', 
                    'duration_display', 'requested_by']
    list_filter = ['status', 'created_at']
    search_fields = ['job_id']
    readonly_fields = ['job_id', 'started_at', 'finished_at', 'created_at']
    
    fieldsets = [
        ('Job Info', {
            'fields': ['job_id', 'status', 'requested_by']
        }),
        ('Scope', {
            'fields': ['from_date', 'to_date', 'horizons', 'insight_ids']
        }),
        ('Configuration', {
            'fields': ['params']
        }),
        ('Progress', {
            'fields': ['total_insights', 'completed_audits', 'failed_audits', 
                      'started_at', 'finished_at']
        }),
        ('Errors', {
            'fields': ['error_message'],
            'classes': ['collapse']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'running': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#ffc107'
        }
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def progress_display(self, obj):
        if obj.total_insights == 0:
            return '0%'
        pct = (obj.completed_audits / obj.total_insights) * 100
        return format_html('{}/{} ({}%)', obj.completed_audits, obj.total_insights, int(pct))
    progress_display.short_description = 'Progress'
    
    def duration_display(self, obj):
        duration = obj.get_duration()
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}m {seconds}s"
        return '-'
    duration_display.short_description = 'Duration'


@admin.register(RetrainRequest)
class RetrainRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'strategy', 'status_badge', 'audit_count', 
                    'uplift_display', 'requested_by', 'created_at']
    list_filter = ['status', 'strategy', 'created_at']
    search_fields = ['request_id', 'strategy', 'reason']
    readonly_fields = ['request_id', 'created_at', 'updated_at', 'metrics_before', 
                       'metrics_after_simulation', 'metrics_after_production']
    
    fieldsets = [
        ('Request Info', {
            'fields': ['request_id', 'strategy', 'status', 'requested_by']
        }),
        ('Dataset', {
            'fields': ['dataset_path', 'audit_count']
        }),
        ('Justification', {
            'fields': ['reason', 'suggested_changes']
        }),
        ('Metrics', {
            'fields': ['metrics_before', 'metrics_after_simulation', 'metrics_after_production']
        }),
        ('Review', {
            'fields': ['reviewed_by', 'reviewed_at', 'reviewer_notes']
        }),
        ('Model Versions', {
            'fields': ['old_model_version', 'new_model_version']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'requested': '#6c757d',
            'simulating': '#17a2b8',
            'pending_approval': '#ffc107',
            'approved': '#28a745',
            'training': '#007bff',
            'completed': '#28a745',
            'rejected': '#dc3545',
            'rolled_back': '#fd7e14'
        }
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px; font-size:11px;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def uplift_display(self, obj):
        if not obj.metrics_after_simulation or not obj.metrics_before:
            return '-'
        
        before = obj.metrics_before.get('accuracy', 0)
        after = obj.metrics_after_simulation.get('accuracy', 0)
        diff = after - before
        
        color = '#28a745' if diff > 0 else '#dc3545'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{:+.1f}%</span>',
            color, diff
        )
    uplift_display.short_description = 'Simulated Uplift'
    
    actions = ['approve_retrain', 'reject_retrain']
    
    def approve_retrain(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending_approval').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} retrain requests approved.')
    approve_retrain.short_description = 'Approve selected retrains'
    
    def reject_retrain(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending_approval').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} retrain requests rejected.')
    reject_retrain.short_description = 'Reject selected retrains'


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ['version_id', 'strategy', 'model_type', 'is_production_badge', 
                    'is_active', 'accuracy_display', 'created_at']
    list_filter = ['is_production', 'is_active', 'model_type', 'strategy', 'created_at']
    search_fields = ['version_id', 'strategy', 'notes']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Version Info', {
            'fields': ['version_id', 'strategy', 'model_type', 'is_active', 'is_production']
        }),
        ('Artifacts', {
            'fields': ['model_path', 'config']
        }),
        ('Training', {
            'fields': ['dataset_path', 'dataset_size', 'train_date_from', 'train_date_to']
        }),
        ('Metrics', {
            'fields': ['metrics', 'validation_metrics', 'feature_importance']
        }),
        ('Metadata', {
            'fields': ['trained_by', 'notes', 'created_at']
        }),
    ]
    
    def is_production_badge(self, obj):
        if obj.is_production:
            return format_html(
                '<span style="background:#28a745; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">PRODUCTION</span>'
            )
        return format_html(
            '<span style="background:#6c757d; color:white; padding:3px 8px; border-radius:3px;">Dev</span>'
        )
    is_production_badge.short_description = 'Environment'
    
    def accuracy_display(self, obj):
        acc = obj.metrics.get('accuracy', 0) * 100 if 'accuracy' in obj.metrics else None
        if acc:
            return f"{acc:.1f}%"
        return '-'
    accuracy_display.short_description = 'Accuracy'
    
    actions = ['set_active', 'set_production']
    
    def set_active(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Select exactly one version to activate.', level='error')
            return
        
        version = queryset.first()
        version.activate()
        self.message_user(request, f'Version {version.version_id} activated.')
    set_active.short_description = 'Set as active version'
    
    def set_production(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Select exactly one version for production.', level='error')
            return
        
        version = queryset.first()
        ModelVersion.objects.filter(strategy=version.strategy, is_production=True).update(is_production=False)
        version.is_production = True
        version.is_active = True
        version.save()
        self.message_user(request, f'Version {version.version_id} deployed to production.')
    set_production.short_description = 'Deploy to production'


@admin.register(LabelingRule)
class LabelingRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'scope_display', 'horizon', 'priority', 'is_active', 'created_at']
    list_filter = ['is_active', 'horizon', 'strategy', 'symbol', 'timeframe']
    search_fields = ['strategy', 'symbol', 'notes']
    
    fieldsets = [
        ('Scope', {
            'fields': ['strategy', 'symbol', 'timeframe', 'horizon']
        }),
        ('Success Criteria', {
            'fields': ['success_tp_pips', 'success_rr_ratio']
        }),
        ('Failure Criteria', {
            'fields': ['fail_sl_pips', 'fail_adverse_pct']
        }),
        ('Neutral Zone', {
            'fields': ['neutral_band_pips']
        }),
        ('Configuration', {
            'fields': ['is_active', 'priority', 'notes']
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at']
        }),
    ]
    
    def scope_display(self, obj):
        parts = []
        if obj.strategy:
            parts.append(f"Strategy: {obj.strategy}")
        if obj.symbol:
            parts.append(f"Symbol: {obj.symbol}")
        if obj.timeframe:
            parts.append(f"TF: {obj.timeframe}")
        return ' | '.join(parts) if parts else 'All Insights'
    scope_display.short_description = 'Applies To'


# ============================================================================
# ZENITH MARKET ANALYST - VISUAL INSIGHTS MODE ADMIN
# ============================================================================

from .models import MarketInsight, VariationVocabulary, InsightTemplate


@admin.register(MarketInsight)
class MarketInsightAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'timeframe', 'regime_badge', 'structure_badge', 
                    'insight_index_display', 'session', 'timestamp']
    list_filter = ['regime', 'structure', 'session', 'momentum', 'volume_state', 'created_at']
    search_fields = ['symbol', 'insight_text', 'suggestion']
    readonly_fields = ['vocabulary_hash', 'created_at', 'raw_metadata']
    date_hierarchy = 'timestamp'
    
    fieldsets = [
        ('Identification', {
            'fields': ['symbol', 'timeframe', 'timestamp']
        }),
        ('Market State', {
            'fields': ['regime', 'structure', 'momentum', 'volume_state', 'session']
        }),
        ('Context', {
            'fields': ['expected_behavior', 'strength', 'risk_notes']
        }),
        ('AI-Generated Content', {
            'fields': ['insight_text', 'suggestion', 'insight_index']
        }),
        ('Scoring Breakdown', {
            'fields': ['structure_clarity', 'regime_stability', 'volume_quality',
                      'momentum_alignment', 'session_validity', 'risk_level'],
            'classes': ['collapse']
        }),
        ('News Integration', {
            'fields': ['news_impact', 'news_context'],
            'classes': ['collapse']
        }),
        ('Chart Display', {
            'fields': ['chart_labels'],
            'classes': ['collapse']
        }),
        ('Variation Tracking', {
            'fields': ['vocabulary_hash', 'sentence_structure_id'],
            'classes': ['collapse']
        }),
        ('Raw Data', {
            'fields': ['raw_metadata'],
            'classes': ['collapse']
        }),
    ]
    
    def regime_badge(self, obj):
        colors = {
            'trending': '#10b981',
            'ranging': '#f59e0b',
            'volatile': '#ef4444',
            'consolidation': '#3b82f6',
        }
        color = colors.get(obj.regime, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px; font-weight:bold;">{}</span>',
            color, obj.get_regime_display()
        )
    regime_badge.short_description = 'Regime'
    
    def structure_badge(self, obj):
        colors = {
            'bos': '#8b5cf6',
            'choch': '#ec4899',
            'liquidity_sweep': '#f97316',
            'fvg': '#eab308',
            'order_block': '#06b6d4',
        }
        color = colors.get(obj.structure, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, obj.get_structure_display()
        )
    structure_badge.short_description = 'Structure'
    
    def insight_index_display(self, obj):
        if obj.insight_index >= 80:
            color = '#10b981'
            label = 'Exceptional'
        elif obj.insight_index >= 65:
            color = '#3b82f6'
            label = 'High'
        elif obj.insight_index >= 50:
            color = '#f59e0b'
            label = 'Moderate'
        else:
            color = '#ef4444'
            label = 'Low'
        
        return format_html(
            '<div style="display:flex; align-items:center; gap:8px;">'
            '<span style="color:{}; font-weight:bold; font-size:16px;">{}</span>'
            '<span style="color:#6b7280; font-size:12px;">{}</span>'
            '</div>',
            color, obj.insight_index, label
        )
    insight_index_display.short_description = 'Index'
    
    actions = ['export_insights_csv']
    
    def export_insights_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="market_insights.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Symbol', 'Timeframe', 'Timestamp', 'Regime', 'Structure',
                        'Insight Index', 'Insight Text', 'Suggestion'])
        
        for insight in queryset:
            writer.writerow([
                insight.id,
                insight.symbol,
                insight.timeframe,
                insight.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                insight.get_regime_display(),
                insight.get_structure_display(),
                insight.insight_index,
                insight.insight_text,
                insight.suggestion,
            ])
        
        return response
    export_insights_csv.short_description = 'Export selected insights to CSV'


@admin.register(VariationVocabulary)
class VariationVocabularyAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'subcategory', 'base_phrase', 'variations_count',
                    'usage_count', 'priority', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['base_phrase', 'category', 'subcategory']
    readonly_fields = ['usage_count', 'last_used', 'created_at']
    
    fieldsets = [
        ('Category', {
            'fields': ['category', 'subcategory']
        }),
        ('Phrases', {
            'fields': ['base_phrase', 'variations']
        }),
        ('Context Rules', {
            'fields': ['appropriate_for', 'avoid_with'],
            'classes': ['collapse']
        }),
        ('Configuration', {
            'fields': ['is_active', 'priority']
        }),
        ('Usage Statistics', {
            'fields': ['usage_count', 'last_used'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_by', 'notes'],
            'classes': ['collapse']
        }),
    ]
    
    def variations_count(self, obj):
        count = len(obj.variations) if obj.variations else 0
        return format_html(
            '<span style="background:#3b82f6; color:white; padding:2px 8px; border-radius:3px;">{}</span>',
            count
        )
    variations_count.short_description = 'Variations'


@admin.register(InsightTemplate)
class InsightTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_id', 'structure_preview', 'slots_count', 'usage_count',
                    'priority', 'is_active']
    list_filter = ['is_active']
    search_fields = ['template_id', 'structure']
    readonly_fields = ['usage_count', 'last_used', 'created_at']
    
    fieldsets = [
        ('Template', {
            'fields': ['template_id', 'structure', 'slots']
        }),
        ('Filters', {
            'fields': ['regime_filter', 'structure_filter'],
            'classes': ['collapse']
        }),
        ('Configuration', {
            'fields': ['is_active', 'priority']
        }),
        ('Usage Statistics', {
            'fields': ['usage_count', 'last_used'],
            'classes': ['collapse']
        }),
    ]
    
    def structure_preview(self, obj):
        preview = obj.structure[:80] + '...' if len(obj.structure) > 80 else obj.structure
        return format_html('<code style="color:#6b7280;">{}</code>', preview)
    structure_preview.short_description = 'Structure'
    
    def slots_count(self, obj):
        count = len(obj.slots) if obj.slots else 0
        return format_html(
            '<span style="background:#10b981; color:white; padding:2px 8px; border-radius:3px;">{} slots</span>',
            count
        )
    slots_count.short_description = 'Slots'
