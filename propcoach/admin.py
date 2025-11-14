from django.contrib import admin
from django.utils.html import format_html
from .models import (
    FirmTemplate, PropChallenge, TradeRecord,
    PropRuleViolation, CoachingFeedback, PropTrainingSession
)


@admin.register(FirmTemplate)
class FirmTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'template_name', 'firm_name', 'phase', 'account_size',
        'profit_target_percent', 'max_daily_drawdown_percent',
        'max_total_drawdown_percent', 'is_active'
    ]
    list_filter = ['firm_name', 'phase', 'is_active']
    search_fields = ['template_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('firm_name', 'phase', 'template_name', 'description', 'is_active')
        }),
        ('Account Settings', {
            'fields': ('account_size', 'profit_target_percent', 'profit_split_percent')
        }),
        ('Risk Limits', {
            'fields': ('max_daily_drawdown_percent', 'max_total_drawdown_percent')
        }),
        ('Trading Rules', {
            'fields': (
                'challenge_duration_days', 'min_trading_days',
                'min_trade_duration_minutes', 'max_leverage',
                'allow_weekend_holding', 'allow_news_trading',
                'max_position_size_percent'
            )
        }),
        ('Custom Rules', {
            'fields': ('custom_rules',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class TradeRecordInline(admin.TabularInline):
    model = TradeRecord
    extra = 0
    fields = ['symbol', 'side', 'entry_price', 'exit_price', 'profit_loss', 'status', 'has_violations']
    readonly_fields = fields
    can_delete = False
    max_num = 10


@admin.register(PropChallenge)
class PropChallengeAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'template', 'status_badge', 'current_balance',
        'total_profit_loss', 'profit_progress', 'win_rate',
        'violation_count', 'days_remaining', 'funding_readiness_score'
    ]
    list_filter = ['status', 'template__firm_name', 'start_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'start_date', 'created_at', 'updated_at',
        'profit_progress', 'win_rate_display', 'days_info'
    ]
    inlines = [TradeRecordInline]
    
    fieldsets = (
        ('Challenge Info', {
            'fields': ('user', 'template', 'status')
        }),
        ('Balance & Progress', {
            'fields': (
                'initial_balance', 'current_balance', 'peak_balance',
                'total_profit_loss', 'profit_progress'
            )
        }),
        ('Trading Statistics', {
            'fields': (
                'total_trades', 'winning_trades', 'losing_trades',
                'win_rate_display', 'violation_count'
            )
        }),
        ('Drawdown Tracking', {
            'fields': (
                'current_daily_drawdown', 'max_daily_drawdown_reached',
                'current_total_drawdown', 'max_total_drawdown_reached'
            )
        }),
        ('Timeline', {
            'fields': (
                'start_date', 'end_date', 'days_info',
                'trading_days_count', 'last_trade_date'
            )
        }),
        ('AI Scores', {
            'fields': ('funding_readiness_score', 'pass_probability')
        }),
        ('Completion', {
            'fields': ('completion_date', 'completion_notes'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': '#4CAF50',
            'passed': '#2196F3',
            'failed': '#f44336',
            'paused': '#FF9800',
            'abandoned': '#9E9E9E'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#666'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    def profit_progress(self, obj):
        percent = obj.profit_progress_percent
        color = '#4CAF50' if percent >= 100 else '#2196F3' if percent >= 50 else '#FF9800'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, f'{percent:.1f}'
        )
    profit_progress.short_description = 'Progress'
    
    def win_rate_display(self, obj):
        wr = obj.win_rate
        color = '#4CAF50' if wr >= 60 else '#FF9800' if wr >= 50 else '#f44336'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, f'{wr:.1f}'
        )
    win_rate_display.short_description = 'Win Rate'
    
    def days_info(self, obj):
        return f"{obj.days_elapsed} elapsed / {obj.days_remaining} remaining"
    days_info.short_description = 'Days'


@admin.register(TradeRecord)
class TradeRecordAdmin(admin.ModelAdmin):
    list_display = [
        'challenge', 'symbol', 'side', 'entry_price', 'exit_price',
        'profit_loss_display', 'status', 'has_violations', 'entry_time'
    ]
    list_filter = ['status', 'side', 'has_violations', 'challenge__template__firm_name']
    search_fields = ['challenge__user__username', 'symbol', 'strategy_used']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Trade Info', {
            'fields': ('challenge', 'symbol', 'side', 'status')
        }),
        ('Prices & Position', {
            'fields': (
                'entry_price', 'exit_price', 'lot_size',
                'position_size_percent', 'leverage_used'
            )
        }),
        ('Risk Management', {
            'fields': ('stop_loss', 'take_profit', 'risk_reward_ratio')
        }),
        ('Results', {
            'fields': ('profit_loss', 'profit_loss_percent')
        }),
        ('Timing', {
            'fields': ('entry_time', 'exit_time', 'hold_duration_minutes')
        }),
        ('Analysis', {
            'fields': (
                'strategy_used', 'confidence_score', 'trader_sentiment'
            )
        }),
        ('Violations', {
            'fields': ('has_violations', 'violation_notes')
        }),
    )
    
    def profit_loss_display(self, obj):
        color = '#4CAF50' if obj.profit_loss >= 0 else '#f44336'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${}</span>',
            color, f'{obj.profit_loss:.2f}'
        )
    profit_loss_display.short_description = 'P/L'


@admin.register(PropRuleViolation)
class PropRuleViolationAdmin(admin.ModelAdmin):
    list_display = [
        'challenge', 'violation_type', 'severity_badge',
        'value_breached', 'limit_value', 'auto_detected',
        'challenge_failed', 'timestamp'
    ]
    list_filter = ['severity', 'violation_type', 'auto_detected', 'challenge_failed', 'resolved']
    search_fields = ['challenge__user__username', 'description']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Violation Info', {
            'fields': ('challenge', 'trade', 'violation_type', 'severity')
        }),
        ('Details', {
            'fields': ('description', 'value_breached', 'limit_value')
        }),
        ('Detection', {
            'fields': ('auto_detected', 'challenge_failed', 'timestamp')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolution_notes'),
            'classes': ('collapse',)
        }),
    )
    
    def severity_badge(self, obj):
        colors = {
            'critical': '#f44336',
            'major': '#FF9800',
            'minor': '#FFC107',
            'warning': '#2196F3'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            colors.get(obj.severity, '#666'),
            obj.get_severity_display().upper()
        )
    severity_badge.short_description = 'Severity'


@admin.register(CoachingFeedback)
class CoachingFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'challenge', 'user', 'feedback_type', 'title',
        'priority_display', 'is_read', 'is_actionable', 'timestamp'
    ]
    list_filter = ['feedback_type', 'is_read', 'is_actionable', 'priority']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Feedback Info', {
            'fields': ('challenge', 'user', 'feedback_type', 'title')
        }),
        ('Message', {
            'fields': ('message', 'metrics_data')
        }),
        ('Psychology', {
            'fields': ('emotional_tone', 'detected_biases', 'discipline_score')
        }),
        ('Recommendations', {
            'fields': ('recommendations', 'priority', 'is_actionable')
        }),
        ('Status', {
            'fields': ('is_read', 'action_taken', 'timestamp')
        }),
    )
    
    def priority_display(self, obj):
        color = '#f44336' if obj.priority >= 8 else '#FF9800' if obj.priority >= 5 else '#4CAF50'
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 50%; font-weight: bold;">{}</span>',
            color, obj.priority
        )
    priority_display.short_description = 'Priority'


@admin.register(PropTrainingSession)
class PropTrainingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_date', 'challenges_attempted',
        'challenges_passed', 'challenges_failed',
        'avg_win_rate', 'readiness_score'
    ]
    list_filter = ['session_date']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_date')
        }),
        ('Challenge Stats', {
            'fields': (
                'challenges_attempted', 'challenges_passed', 'challenges_failed'
            )
        }),
        ('Performance Metrics', {
            'fields': (
                'avg_win_rate', 'avg_profit_factor', 'avg_max_drawdown',
                'rule_violations_count'
            )
        }),
        ('Progress', {
            'fields': ('discipline_improvement', 'readiness_score')
        }),
        ('Insights', {
            'fields': ('learning_insights',),
            'classes': ('collapse',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = "ZenithEdge PropCoach Administration"
admin.site.site_title = "PropCoach Admin"
admin.site.index_title = "Prop Firm Training Management"
