"""
ZenithMentor Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ApprenticeProfile, Lesson, LessonStep, Scenario,
    SimulationRun, TradeEntry, SkillBadge, BadgeAward,
    AssessmentResult, CoachingSession, MLModel
)


@admin.register(ApprenticeProfile)
class ApprenticeProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill_level', 'learner_type', 'lessons_completed', 
                    'win_rate', 'discipline_score', 'is_certified', 'pass_probability']
    list_filter = ['skill_level', 'learner_type', 'is_certified', 'coaching_mode']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'pass_probability']
    
    fieldsets = [
        ('User', {'fields': ['id', 'user', 'current_lesson']}),
        ('Progress', {'fields': ['lessons_completed', 'total_scenarios_attempted', 
                                 'total_scenarios_passed', 'skill_level']}),
        ('Performance Metrics', {'fields': ['overall_expectancy', 'win_rate', 
                                            'avg_risk_per_trade', 'risk_consistency_score',
                                            'stop_loss_adherence', 'avg_reward_risk_ratio', 
                                            'max_drawdown']}),
        ('Discipline & Psychology', {'fields': ['discipline_score', 'journaling_quality_score',
                                                'emotional_control_score', 'revenge_trade_count',
                                                'overconfidence_incidents']}),
        ('ML Classification', {'fields': ['learner_type', 'pass_probability', 'strategy_proficiency']}),
        ('Adaptive Settings', {'fields': ['current_difficulty', 'max_position_size', 'coaching_mode']}),
        ('Certification', {'fields': ['is_certified', 'certification_date', 'certification_level']}),
        ('Metadata', {'fields': ['created_at', 'updated_at']}),
    ]
    
    actions = ['recalculate_metrics']
    
    def recalculate_metrics(self, request, queryset):
        for profile in queryset:
            profile.update_metrics()
        self.message_user(request, f"Recalculated metrics for {queryset.count()} apprentices.")
    recalculate_metrics.short_description = "Recalculate all metrics"


class LessonStepInline(admin.TabularInline):
    model = LessonStep
    extra = 1
    fields = ['order', 'step_type', 'title', 'is_required']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'week', 'order', 'category', 'difficulty', 'is_published']
    list_filter = ['week', 'category', 'difficulty', 'is_published']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonStepInline]
    
    fieldsets = [
        ('Basic Info', {'fields': ['title', 'slug', 'category', 'week', 'order', 'description']}),
        ('Content', {'fields': ['learning_objectives', 'theory_content', 'demo_chart_url', 'video_url']}),
        ('Prerequisites', {'fields': ['prerequisites']}),
        ('Settings', {'fields': ['difficulty', 'min_skill_level', 'estimated_duration_minutes']}),
        ('Pass Criteria', {'fields': ['min_pass_score', 'required_scenarios']}),
        ('Status', {'fields': ['is_published', 'created_at', 'updated_at']}),
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LessonStep)
class LessonStepAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'order', 'step_type', 'title', 'is_required']
    list_filter = ['step_type', 'is_required', 'lesson__category']
    search_fields = ['title', 'content', 'lesson__title']


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'regime', 'strategy_focus', 'difficulty', 'session', 
                    'usage_count', 'avg_pass_rate', 'is_active']
    list_filter = ['regime', 'difficulty', 'session', 'strategy_focus', 'is_active']
    search_fields = ['name', 'description', 'tags']
    readonly_fields = ['id', 'usage_count', 'avg_pass_rate', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Info', {'fields': ['id', 'name', 'description']}),
        ('Classification', {'fields': ['regime', 'session', 'strategy_focus', 'difficulty', 'tags']}),
        ('Market Data', {'fields': ['symbol', 'timeframe', 'start_date', 'end_date', 'candle_data']}),
        ('Synthetic Modifications', {'fields': ['has_synthetic_news', 'synthetic_news_events', 'volatility_multiplier']}),
        ('Optimal Solution', {'fields': ['optimal_direction', 'optimal_entry_price', 
                                         'optimal_stop_loss', 'optimal_take_profit']}),
        ('Grading', {'fields': ['grading_criteria']}),
        ('Statistics', {'fields': ['usage_count', 'avg_pass_rate']}),
        ('Meta', {'fields': ['created_by', 'is_active', 'created_at', 'updated_at']}),
    ]
    
    actions = ['update_pass_rates']
    
    def update_pass_rates(self, request, queryset):
        for scenario in queryset:
            scenario.update_pass_rate()
        self.message_user(request, f"Updated pass rates for {queryset.count()} scenarios.")
    update_pass_rates.short_description = "Update pass rates"


class TradeEntryInline(admin.TabularInline):
    model = TradeEntry
    extra = 0
    fields = ['direction', 'entry_price', 'stop_loss', 'position_size', 'status', 'pnl']
    readonly_fields = ['pnl']


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ['apprentice', 'scenario', 'status', 'overall_score', 'passed', 
                    'trades_count', 'final_pnl', 'started_at']
    list_filter = ['status', 'passed', 'scenario__regime', 'scenario__difficulty']
    search_fields = ['apprentice__user__email', 'scenario__name']
    readonly_fields = ['id', 'started_at', 'completed_at']
    inlines = [TradeEntryInline]
    
    fieldsets = [
        ('Basic Info', {'fields': ['id', 'apprentice', 'scenario', 'lesson_step', 'status']}),
        ('Timing', {'fields': ['started_at', 'completed_at']}),
        ('Replay Control', {'fields': ['current_candle_index', 'playback_speed']}),
        ('Performance', {'fields': ['initial_balance', 'final_balance', 'final_pnl', 
                                    'max_drawdown', 'trades_count', 'winning_trades', 'losing_trades']}),
        ('Scores', {'fields': ['technical_score', 'risk_mgmt_score', 'execution_score',
                               'journaling_score', 'discipline_score', 'overall_score', 'passed']}),
        ('Feedback', {'fields': ['coach_feedback', 'strengths', 'weaknesses', 'suggestions']}),
        ('Audit', {'fields': ['trades_log', 'journal_entries', 'coaching_interactions']}),
    ]


@admin.register(TradeEntry)
class TradeEntryAdmin(admin.ModelAdmin):
    list_display = ['simulation_run', 'direction', 'entry_price', 'status', 
                    'pnl', 'technical_validity', 'zenbot_score']
    list_filter = ['direction', 'status', 'technical_validity', 'was_winner']
    search_fields = ['simulation_run__apprentice__user__email', 'rationale']
    readonly_fields = ['id', 'created_at']


@admin.register(SkillBadge)
class SkillBadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'color_badge', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    
    def color_badge(self, obj):
        return format_html(
            '<i class="bi bi-{}" style="color: {}; font-size: 1.5em;"></i>',
            obj.icon_name, obj.color
        )
    color_badge.short_description = 'Badge Preview'


@admin.register(BadgeAward)
class BadgeAwardAdmin(admin.ModelAdmin):
    list_display = ['apprentice', 'badge', 'awarded_at']
    list_filter = ['badge__category', 'awarded_at']
    search_fields = ['apprentice__user__email', 'badge__name']


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ['apprentice', 'assessment_type', 'score', 'max_score', 'passed', 'attempted_at']
    list_filter = ['assessment_type', 'passed', 'lesson']
    search_fields = ['apprentice__user__email', 'lesson__title']
    readonly_fields = ['id', 'attempted_at']


@admin.register(CoachingSession)
class CoachingSessionAdmin(admin.ModelAdmin):
    list_display = ['apprentice', 'topic', 'triggered_by', 'apprentice_acknowledged', 'created_at']
    list_filter = ['triggered_by', 'apprentice_acknowledged']
    search_fields = ['apprentice__user__email', 'topic', 'message']
    readonly_fields = ['id', 'created_at']


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['model_type', 'version', 'is_active', 'training_accuracy', 
                    'training_samples', 'deployed_at']
    list_filter = ['model_type', 'is_active']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = [
        ('Model Info', {'fields': ['id', 'model_type', 'version']}),
        ('Artifacts', {'fields': ['model_file_path', 'feature_names']}),
        ('Training', {'fields': ['training_samples', 'training_accuracy', 'training_notes']}),
        ('Deployment', {'fields': ['is_active', 'deployed_at', 'created_at']}),
    ]
