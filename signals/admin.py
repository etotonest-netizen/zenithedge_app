from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Signal, PropRules, StrategyPerformance, SessionRule, RiskControl, 
    TradeJournalEntry, WebhookConfig, SignalEvaluation, SignalOverrideLog,
    MarketInsight  # NEW: AI Decision Intelligence Console model
)


@admin.register(RiskControl)
class RiskControlAdmin(admin.ModelAdmin):
    """Admin interface for RiskControl model"""
    
    list_display = [
        'user',
        'is_active',
        'is_halted',
        'max_consecutive_losers',
        'max_daily_trades',
        'max_red_signals_per_day',
        'halt_triggered_at',
        'updated_at'
    ]
    
    list_filter = [
        'is_active',
        'is_halted',
        'halt_until_reset',
        'user'
    ]
    
    search_fields = ['user__email', 'halt_reason', 'notes']
    
    readonly_fields = ['halt_triggered_at', 'last_reset_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Risk Thresholds', {
            'fields': ('max_consecutive_losers', 'max_daily_trades', 'max_red_signals_per_day')
        }),
        ('Control Settings', {
            'fields': ('is_active', 'halt_until_reset')
        }),
        ('Halt Status', {
            'fields': ('is_halted', 'halt_reason', 'halt_triggered_at', 'last_reset_at'),
            'classes': ('wide',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_halt_action']
    
    def reset_halt_action(self, request, queryset):
        """Admin action to reset halt status"""
        count = 0
        for risk_control in queryset:
            risk_control.reset_halt()
            count += 1
        self.message_user(request, f'Successfully reset halt status for {count} risk control(s).')
    reset_halt_action.short_description = "Reset halt status"
    
    def get_queryset(self, request):
        """Filter risk controls based on user role"""
        qs = super().get_queryset(request)
        if not request.user.is_admin and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs


@admin.register(SessionRule)
class SessionRuleAdmin(admin.ModelAdmin):
    """Admin interface for SessionRule model"""
    
    list_display = [
        'session',
        'user',
        'weight',
        'is_blocked',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'session',
        'is_blocked',
        'user'
    ]
    
    search_fields = ['user__email', 'notes']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Session Configuration', {
            'fields': ('session', 'user', 'weight', 'is_blocked')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter session rules based on user role"""
        qs = super().get_queryset(request)
        if not request.user.is_admin and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs


@admin.register(PropRules)
class PropRulesAdmin(admin.ModelAdmin):
    """Admin interface for PropRules model"""
    
    list_display = [
        'name',
        'is_active',
        'max_daily_loss_pct',
        'max_trades_per_day',
        'max_open_positions',
        'min_confidence_score',
        'blackout_minutes',
        'allow_weekend_trading'
    ]
    
    list_filter = [
        'is_active',
        'allow_weekend_trading'
    ]
    
    search_fields = ['name']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active', 'account_balance')
        }),
        ('Daily Limits', {
            'fields': ('max_daily_loss_pct', 'max_daily_loss_amount', 'max_trades_per_day')
        }),
        ('Position Management', {
            'fields': ('max_open_positions', 'max_position_size_pct', 'max_risk_per_trade_pct')
        }),
        ('Time Restrictions', {
            'fields': ('blackout_minutes', 'trading_start_time', 'trading_end_time', 'allow_weekend_trading')
        }),
        ('Symbol Restrictions', {
            'fields': ('allowed_symbols', 'blacklisted_symbols'),
            'description': 'Enter comma-separated symbol names (e.g., BTCUSDT, ETHUSDT)'
        }),
        ('Quality Filters', {
            'fields': ('min_confidence_score',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    """Admin interface for Signal model"""
    
    list_display = [
        'id',
        'symbol',
        'timeframe',
        'side',
        'regime',
        'session',
        'strategy',
        'confidence',
        'user',
        'is_allowed',
        'price',
        'sl',
        'tp',
        'received_at'
    ]
    
    list_filter = [
        'is_allowed',
        'side',
        'regime',
        'session',
        'strategy',
        'timeframe',
        'user',
        'prop_rule_checked',
        'received_at'
    ]
    
    search_fields = [
        'symbol',
        'strategy',
        'regime',
        'user__email'
    ]
    
    def get_queryset(self, request):
        """Filter signals based on user role"""
        qs = super().get_queryset(request)
        if not request.user.is_admin and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs
    
    readonly_fields = [
        'received_at',
        'updated_at'
    ]
    
    ordering = ['-received_at']
    
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Signal Information', {
            'fields': ('symbol', 'timeframe', 'side', 'regime', 'session', 'strategy')
        }),
        ('Price Levels', {
            'fields': ('price', 'sl', 'tp', 'confidence')
        }),
        ('Prop Rules Validation', {
            'fields': ('is_allowed', 'rejection_reason', 'prop_rule_checked'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'received_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual adding of signals through admin"""
        return False


@admin.register(MarketInsight)
class MarketInsightAdmin(admin.ModelAdmin):
    """
    Admin interface for MarketInsight model (AI Decision Intelligence Console)
    
    Displays market intelligence without trading signal language.
    Focus on narrative, bias, and AI reasoning quality.
    """
    
    list_display = [
        'id',
        'symbol',
        'timeframe',
        'regime',
        'session',
        'bias_display',
        'market_phase_display',
        'insight_index_display',
        'confidence_score_display',
        'is_high_quality',
        'narrative_preview',
        'user',
        'received_at'
    ]
    
    list_filter = [
        'is_high_quality',
        'bias',
        'market_phase',
        'regime',
        'session',
        'strategy',
        'timeframe',
        'user',
        'received_at'
    ]
    
    search_fields = [
        'symbol',
        'strategy',
        'regime',
        'narrative',
        'user__email'
    ]
    
    readonly_fields = [
        'received_at',
        'updated_at',
        'narrative_full',
        'follow_up_cue_full',
        'original_signal'
    ]
    
    ordering = ['-received_at']
    
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Market Context', {
            'fields': ('symbol', 'timeframe', 'regime', 'session', 'strategy')
        }),
        ('AI Intelligence Analysis', {
            'fields': ('bias', 'market_phase', 'insight_index', 'confidence_score'),
            'classes': ('wide',)
        }),
        ('AI Narrative', {
            'fields': ('narrative_full', 'follow_up_cue_full'),
            'classes': ('wide',)
        }),
        ('Quality Control', {
            'fields': ('is_high_quality', 'quality_notes'),
            'classes': ('collapse',)
        }),
        ('Observation Data', {
            'fields': ('observation_price', 'outcome'),
            'classes': ('collapse',)
        }),
        ('Legacy Data (Migration Only)', {
            'fields': ('legacy_side', 'legacy_sl', 'legacy_tp', 'original_signal'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'received_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter insights based on user role"""
        qs = super().get_queryset(request)
        if not request.user.is_admin and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs
    
    def has_add_permission(self, request):
        """Disable manual adding of insights through admin (use webhook)"""
        return False
    
    # Custom display methods (NO TRADING LANGUAGE)
    @admin.display(description='Bias')
    def bias_display(self, obj):
        """Display bias with color coding (no directional icons)"""
        colors = {
            'bearish': '#d69e2e',  # amber
            'neutral': '#4a5568',  # steel gray
            'bullish': '#2c7a7b',  # teal
        }
        color = colors.get(obj.bias, '#4a5568')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.bias.upper()
        )
    
    @admin.display(description='Market Phase')
    def market_phase_display(self, obj):
        """Display market phase"""
        return obj.market_phase.title()
    
    @admin.display(description='Insight Index')
    def insight_index_display(self, obj):
        """Display insight index with quality indicator"""
        if obj.insight_index >= 80:
            color = '#2c7a7b'  # teal (excellent)
            label = 'Excellent'
        elif obj.insight_index >= 65:
            color = '#1e3a5f'  # blue (good)
            label = 'Good'
        elif obj.insight_index >= 50:
            color = '#d69e2e'  # amber (modest)
            label = 'Modest'
        else:
            color = '#4a5568'  # gray (low)
            label = 'Low'
        
        return format_html(
            '<span style="color: {};">{:.0f}/100 ({})</span>',
            color,
            obj.insight_index,
            label
        )
    
    @admin.display(description='Confidence')
    def confidence_score_display(self, obj):
        """Display AI confidence score"""
        return f"{obj.confidence_score:.0f}%"
    
    @admin.display(description='Narrative (Preview)')
    def narrative_preview(self, obj):
        """Display first 80 characters of narrative"""
        if len(obj.narrative) > 80:
            return obj.narrative[:80] + '...'
        return obj.narrative
    
    @admin.display(description='Full Narrative')
    def narrative_full(self, obj):
        """Display full narrative (readonly field)"""
        return obj.narrative
    
    @admin.display(description='Follow-up Observation Cue')
    def follow_up_cue_full(self, obj):
        """Display full follow-up cue (readonly field)"""
        return obj.follow_up_cue or 'No specific follow-up suggestion.'


@admin.register(StrategyPerformance)
class StrategyPerformanceAdmin(admin.ModelAdmin):
    """Admin interface for StrategyPerformance model"""
    
    list_display = [
        'id',
        'strategy_name',
        'regime',
        'symbol',
        'timeframe',
        'total_trades',
        'win_rate',
        'avg_rr',
        'profit_factor',
        'is_profitable',
        'user',
        'last_updated'
    ]
    
    list_filter = [
        'regime',
        'symbol',
        'timeframe',
        'user',
        'last_updated'
    ]
    
    search_fields = [
        'strategy_name',
        'symbol',
        'user__email'
    ]
    
    readonly_fields = [
        'last_updated',
        'created_at',
        'performance_score'
    ]
    
    ordering = ['-win_rate', '-total_trades']
    
    fieldsets = (
        ('Strategy Information', {
            'fields': ('strategy_name', 'regime', 'symbol', 'timeframe', 'user')
        }),
        ('Trade Statistics', {
            'fields': ('total_trades', 'winning_trades', 'losing_trades', 'win_rate')
        }),
        ('Risk-Reward Metrics', {
            'fields': ('avg_rr', 'total_rr', 'avg_confidence')
        }),
        ('Profitability', {
            'fields': ('total_pnl', 'avg_win', 'avg_loss', 'profit_factor')
        }),
        ('Drawdown', {
            'fields': ('max_drawdown', 'current_drawdown')
        }),
        ('Analysis Period', {
            'fields': ('analysis_period_start', 'analysis_period_end', 'last_updated', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Performance Score', {
            'fields': ('performance_score',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter performance records based on user role"""
        qs = super().get_queryset(request)
        if not request.user.is_admin and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs


@admin.register(TradeJournalEntry)
class TradeJournalEntryAdmin(admin.ModelAdmin):
    """Admin interface for TradeJournalEntry model"""
    
    list_display = [
        'id',
        'user',
        'signal',
        'decision',
        'outcome',
        'pips',
        'duration_minutes',
        'created_at'
    ]
    
    list_filter = [
        'decision',
        'outcome',
        'user',
        'created_at'
    ]
    
    search_fields = [
        'user__email',
        'notes',
        'signal__symbol',
        'signal__strategy'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'display_risk_reward', 'display_session', 'display_strategy']
    
    fieldsets = (
        ('Entry Information', {
            'fields': ('user', 'signal', 'decision', 'outcome')
        }),
        ('Performance Metrics', {
            'fields': ('pips', 'duration_minutes', 'display_risk_reward')
        }),
        ('Signal Context', {
            'fields': ('display_session', 'display_strategy'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def display_risk_reward(self, obj):
        """Display risk:reward ratio"""
        rr = obj.risk_reward_ratio
        return f"{rr}:1" if rr else "N/A"
    display_risk_reward.short_description = "Risk:Reward"
    
    def display_session(self, obj):
        """Display session from signal"""
        return obj.session or "N/A"
    display_session.short_description = "Session"
    
    def display_strategy(self, obj):
        """Display strategy from signal"""
        return obj.strategy or "N/A"
    display_strategy.short_description = "Strategy"
    
    def get_queryset(self, request):
        """Filter journal entries based on user role"""
        qs = super().get_queryset(request)
        if not request.user.is_admin and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit signal and user choices based on current user"""
        if db_field.name == "signal":
            if not request.user.is_admin and not request.user.is_staff:
                kwargs["queryset"] = Signal.objects.filter(user=request.user)
        if db_field.name == "user":
            if not request.user.is_admin and not request.user.is_staff:
                kwargs["queryset"] = request.user.__class__.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(WebhookConfig)
class WebhookConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'webhook_uuid', 'is_active', 'signal_count', 'last_signal_at', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'webhook_uuid']
    readonly_fields = ['webhook_uuid', 'webhook_url', 'signal_count', 'last_signal_at', 'created_at', 'updated_at']
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Webhook Configuration', {'fields': ('webhook_uuid', 'webhook_url', 'is_active')}),
        ('Statistics', {'fields': ('signal_count', 'last_signal_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    actions = ['activate_webhooks', 'deactivate_webhooks']

    def activate_webhooks(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} webhook(s)')
    activate_webhooks.short_description = 'Activate selected webhooks'

    def deactivate_webhooks(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {queryset.count()} webhook(s)')
    deactivate_webhooks.short_description = 'Deactivate selected webhooks'


@admin.register(SignalEvaluation)
class SignalEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'signal_id',
        'user_email',
        'passed_status',
        'blocked_reason',
        'final_ai_score',
        'news_check_icon',
        'prop_check_icon',
        'score_check_icon',
        'strategy_check_icon',
        'created_at'
    ]
    list_filter = [
        'passed',
        'blocked_reason',
        'news_check',
        'prop_check',
        'score_check',
        'strategy_check',
        'created_at'
    ]
    search_fields = [
        'signal__id',
        'signal__user__email',
        'signal__symbol',
        'evaluation_notes'
    ]
    readonly_fields = [
        'signal',
        'passed',
        'blocked_reason',
        'final_ai_score',
        'news_check',
        'prop_check',
        'score_check',
        'strategy_check',
        'evaluation_notes',
        'created_at'
    ]
    fieldsets = (
        ('Signal Info', {
            'fields': ('signal', 'passed', 'blocked_reason', 'final_ai_score')
        }),
        ('Validation Checks', {
            'fields': ('news_check', 'prop_check', 'score_check', 'strategy_check')
        }),
        ('Details', {
            'fields': ('evaluation_notes', 'created_at')
        }),
    )
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def signal_id(self, obj):
        return f"Signal #{obj.signal.id}"
    signal_id.short_description = 'Signal'
    
    def user_email(self, obj):
        return obj.signal.user.email
    user_email.short_description = 'User'
    
    def passed_status(self, obj):
        if obj.passed:
            return '✅ PASSED'
        else:
            return f'❌ BLOCKED'
    passed_status.short_description = 'Status'
    
    def news_check_icon(self, obj):
        return '✅' if obj.news_check else '❌'
    news_check_icon.short_description = 'News'
    
    def prop_check_icon(self, obj):
        return '✅' if obj.prop_check else '❌'
    prop_check_icon.short_description = 'Prop'
    
    def score_check_icon(self, obj):
        return '✅' if obj.score_check else '❌'
    score_check_icon.short_description = 'Score'
    
    def strategy_check_icon(self, obj):
        return '✅' if obj.strategy_check else '❌'
    strategy_check_icon.short_description = 'Strategy'

# SignalOverrideLog Admin
@admin.register(SignalOverrideLog)
class SignalOverrideLogAdmin(admin.ModelAdmin):
    list_display = ['signal_id', 'admin_email', 'old_reason', 'new_reason', 'override_reason_short', 'override_at']
    list_filter = ['override_at', 'admin_user']
    search_fields = ['signal__id', 'admin_user__email', 'override_reason']
    readonly_fields = ['signal', 'admin_user', 'old_reason', 'new_reason', 'override_reason', 'override_at']
    ordering = ['-override_at']
    
    def signal_id(self, obj):
        return f"Signal #{obj.signal.id}"
    signal_id.short_description = 'Signal'
    
    def admin_email(self, obj):
        return obj.admin_user.email
    admin_email.short_description = 'Admin User'
    
    def override_reason_short(self, obj):
        return obj.override_reason[:50] + ('...' if len(obj.override_reason) > 50 else '')
    override_reason_short.short_description = 'Override Reason'
    
    def has_add_permission(self, request):
        # Override logs should only be created via the override view
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should never be deleted
        return False
