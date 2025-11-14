"""
ZenithMentor Models
Core database schema for the training system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid
import json

User = get_user_model()


class ApprenticeProfile(models.Model):
    """Extended profile for trainees tracking progress and ML features."""
    
    LEARNER_TYPE_CHOICES = [
        ('analytical', 'Analytical - Detail-Oriented'),
        ('intuitive', 'Intuitive - Pattern Recognizer'),
        ('aggressive', 'Aggressive - High Risk Tolerance'),
        ('conservative', 'Conservative - Risk Averse'),
        ('undetermined', 'Undetermined'),
    ]
    
    SKILL_LEVEL_CHOICES = [
        ('novice', 'Novice'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='apprentice_profile')
    
    # Progress tracking
    current_lesson = models.ForeignKey('Lesson', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_apprentices')
    lessons_completed = models.IntegerField(default=0)
    total_scenarios_attempted = models.IntegerField(default=0)
    total_scenarios_passed = models.IntegerField(default=0)
    
    # Performance metrics (ML features)
    overall_expectancy = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    avg_risk_per_trade = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)  # percentage
    risk_consistency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    stop_loss_adherence = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    avg_reward_risk_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Discipline & psychology
    discipline_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    journaling_quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    emotional_control_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    revenge_trade_count = models.IntegerField(default=0)
    overconfidence_incidents = models.IntegerField(default=0)
    
    # ML classification
    learner_type = models.CharField(max_length=20, choices=LEARNER_TYPE_CHOICES, default='undetermined')
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default='novice')
    pass_probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # ML predicted
    
    # Strategy preferences (JSON: strategy_name -> proficiency_score)
    strategy_proficiency = models.JSONField(default=dict)
    
    # Adaptive settings
    current_difficulty = models.IntegerField(default=1)  # 1-10
    max_position_size = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    coaching_mode = models.CharField(max_length=20, default='assisted', 
                                     choices=[('assisted', 'Assisted'), ('suggestions', 'Suggestions Only'), ('autonomous', 'Autonomous')])
    
    # Certification
    is_certified = models.BooleanField(default=False)
    certification_date = models.DateTimeField(null=True, blank=True)
    certification_level = models.CharField(max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'zenithmentor_apprentice_profile'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.skill_level} ({self.learner_type})"
    
    def update_metrics(self):
        """Recalculate all metrics from simulation runs."""
        runs = self.simulation_runs.filter(status='completed')
        if not runs.exists():
            return
        
        # Aggregate performance
        total_trades = sum(run.trades_count for run in runs)
        winning_trades = sum(run.winning_trades for run in runs)
        
        if total_trades > 0:
            self.win_rate = Decimal(winning_trades / total_trades * 100)
        
        # Calculate expectancy
        total_pnl = sum(run.final_pnl for run in runs)
        if total_trades > 0:
            self.overall_expectancy = Decimal(total_pnl / total_trades)
        
        # Discipline metrics
        disciplined_runs = runs.filter(discipline_score__gte=70).count()
        self.discipline_score = Decimal(disciplined_runs / runs.count() * 100) if runs.count() > 0 else 0
        
        self.save()


class Lesson(models.Model):
    """A lesson in the curriculum covering a specific topic/strategy."""
    
    WEEK_CHOICES = [(i, f'Week {i}') for i in range(13)]
    
    CATEGORY_CHOICES = [
        ('foundation', 'Foundation'),
        ('trend', 'Trend Trading'),
        ('breakout', 'Breakout Trading'),
        ('mean_reversion', 'Mean Reversion'),
        ('volatility', 'Volatility Trading'),
        ('session_bias', 'Session & VWAP'),
        ('smc', 'Smart Money Concepts'),
        ('scalping', 'Scalping'),
        ('supply_demand', 'Supply & Demand'),
        ('prop_prep', 'Prop Challenge Prep'),
        ('certification', 'Certification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    week = models.IntegerField(choices=WEEK_CHOICES)
    order = models.IntegerField(default=0)
    
    # Content
    description = models.TextField()
    learning_objectives = models.TextField(help_text="Bullet points of what trainee will learn")
    theory_content = models.TextField(help_text="Markdown formatted lesson content")
    
    # Media
    demo_chart_url = models.URLField(blank=True, help_text="Link to annotated chart example")
    video_url = models.URLField(blank=True)
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='unlocks')
    
    # Difficulty & requirements
    difficulty = models.IntegerField(default=1, help_text="1-10 scale")
    min_skill_level = models.CharField(max_length=20, default='novice')
    estimated_duration_minutes = models.IntegerField(default=30)
    
    # Pass criteria
    min_pass_score = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    required_scenarios = models.IntegerField(default=5, help_text="Number of scenarios trainee must complete")
    
    # Status
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'zenithmentor_lesson'
        ordering = ['week', 'order']
        unique_together = [['week', 'order']]
    
    def __str__(self):
        return f"Week {self.week} - {self.title}"
    
    def get_next_lesson(self):
        """Get the next lesson in sequence."""
        return Lesson.objects.filter(
            week__gte=self.week,
            order__gt=self.order,
            is_published=True
        ).first()


class LessonStep(models.Model):
    """Individual steps within a lesson (micro-lessons)."""
    
    STEP_TYPE_CHOICES = [
        ('concept', 'Concept Explanation'),
        ('rules', 'Trading Rules'),
        ('demo', 'Annotated Demo'),
        ('mistakes', 'Common Mistakes'),
        ('risk_mgmt', 'Risk Management'),
        ('quiz', 'Knowledge Check'),
        ('simulation', 'Practice Simulation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField(default=0)
    step_type = models.CharField(max_length=20, choices=STEP_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Markdown or HTML content")
    
    # For quiz steps
    quiz_questions = models.JSONField(null=True, blank=True, help_text="Array of question objects")
    
    # For simulation steps
    required_scenarios = models.ManyToManyField('Scenario', blank=True, related_name='lesson_steps')
    
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'zenithmentor_lesson_step'
        ordering = ['lesson', 'order']
        unique_together = [['lesson', 'order']]
    
    def __str__(self):
        return f"{self.lesson.title} - Step {self.order}: {self.title}"


class Scenario(models.Model):
    """A replayable market scenario for training."""
    
    REGIME_CHOICES = [
        ('trending_bull', 'Trending Bull'),
        ('trending_bear', 'Trending Bear'),
        ('ranging', 'Ranging/Choppy'),
        ('high_volatility', 'High Volatility'),
        ('low_volatility', 'Low Volatility'),
        ('breakout', 'Breakout Event'),
        ('reversal', 'Reversal Pattern'),
        ('news_driven', 'News-Driven'),
    ]
    
    SESSION_CHOICES = [
        ('asian', 'Asian Session'),
        ('london', 'London Session'),
        ('newyork', 'New York Session'),
        ('overlap', 'Session Overlap'),
        ('any', 'Any Session'),
    ]
    
    DIFFICULTY_CHOICES = [(i, f'Level {i}') for i in range(1, 11)]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Classification
    regime = models.CharField(max_length=30, choices=REGIME_CHOICES)
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, default='any')
    strategy_focus = models.CharField(max_length=50, help_text="Primary strategy this scenario teaches")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    
    # Historical data
    symbol = models.CharField(max_length=20, default='EURUSD')
    timeframe = models.CharField(max_length=10, default='15m')
    start_date = models.DateTimeField(help_text="Historical window start")
    end_date = models.DateTimeField(help_text="Historical window end")
    candle_data = models.JSONField(help_text="Array of OHLCV candles")
    
    # Synthetic modifications
    has_synthetic_news = models.BooleanField(default=False)
    synthetic_news_events = models.JSONField(null=True, blank=True, help_text="Injected news events")
    volatility_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    # Expected solution
    optimal_entry_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    optimal_stop_loss = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    optimal_take_profit = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    optimal_direction = models.CharField(max_length=10, choices=[('long', 'Long'), ('short', 'Short'), ('neutral', 'Neutral')], default='neutral')
    
    # Grading rubric
    grading_criteria = models.JSONField(default=dict, help_text="Scoring weights and thresholds")
    
    # Tags for filtering
    tags = models.JSONField(default=list, help_text="Array of string tags")
    
    # Meta
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_scenarios')
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    avg_pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'zenithmentor_scenario'
        ordering = ['difficulty', 'strategy_focus']
        indexes = [
            models.Index(fields=['regime', 'difficulty']),
            models.Index(fields=['strategy_focus']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.regime}, Lvl {self.difficulty})"
    
    def increment_usage(self):
        """Track scenario usage."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def update_pass_rate(self):
        """Recalculate average pass rate from simulation runs."""
        runs = self.simulation_runs.filter(status='completed')
        if not runs.exists():
            return
        
        passed = runs.filter(passed=True).count()
        self.avg_pass_rate = Decimal(passed / runs.count() * 100)
        self.save(update_fields=['avg_pass_rate'])


class SimulationRun(models.Model):
    """A trainee's attempt at a scenario."""
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apprentice = models.ForeignKey(ApprenticeProfile, on_delete=models.CASCADE, related_name='simulation_runs')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='simulation_runs')
    lesson_step = models.ForeignKey(LessonStep, on_delete=models.SET_NULL, null=True, blank=True, related_name='simulation_runs')
    
    # Run state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Replay control
    current_candle_index = models.IntegerField(default=0)
    playback_speed = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    # Performance
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    final_balance = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    final_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    trades_count = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    
    # Grading
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    risk_mgmt_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    execution_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    journaling_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    discipline_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # weighted average
    
    passed = models.BooleanField(default=False)
    
    # AI feedback
    coach_feedback = models.TextField(blank=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    
    # Audit trail
    trades_log = models.JSONField(default=list, help_text="Array of trade objects")
    journal_entries = models.JSONField(default=list, help_text="Array of journal text entries")
    coaching_interactions = models.JSONField(default=list, help_text="Array of coach messages")
    
    class Meta:
        db_table = 'zenithmentor_simulation_run'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['apprentice', 'status']),
            models.Index(fields=['scenario', 'passed']),
        ]
    
    def __str__(self):
        return f"{self.apprentice.user.email} - {self.scenario.name} ({self.status})"
    
    def calculate_overall_score(self):
        """Calculate weighted overall score."""
        weights = {
            'technical': 0.30,
            'risk_mgmt': 0.25,
            'execution': 0.20,
            'journaling': 0.15,
            'discipline': 0.10,
        }
        
        self.overall_score = (
            self.technical_score * Decimal(str(weights['technical'])) +
            self.risk_mgmt_score * Decimal(str(weights['risk_mgmt'])) +
            self.execution_score * Decimal(str(weights['execution'])) +
            self.journaling_score * Decimal(str(weights['journaling'])) +
            self.discipline_score * Decimal(str(weights['discipline']))
        )
        
        # Check if passed
        self.passed = self.overall_score >= self.scenario.grading_criteria.get('min_pass_score', 70)
        self.save()


class TradeEntry(models.Model):
    """A trade submitted during a simulation."""
    
    DIRECTION_CHOICES = [
        ('long', 'Long'),
        ('short', 'Short'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    simulation_run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='trades')
    
    # Trade details
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    entry_price = models.DecimalField(max_digits=20, decimal_places=5)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=5)
    take_profit = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    position_size = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Risk calculation
    risk_amount = models.DecimalField(max_digits=15, decimal_places=2)
    risk_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    reward_risk_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Execution
    entry_candle_index = models.IntegerField()
    entry_timestamp = models.DateTimeField()
    exit_price = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)
    exit_candle_index = models.IntegerField(null=True, blank=True)
    exit_timestamp = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Outcome
    pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pnl_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    was_winner = models.BooleanField(null=True)
    
    # Trainee documentation
    rationale = models.TextField(help_text="Why trainee took this trade")
    rules_followed = models.JSONField(default=list, help_text="Array of rule names")
    rules_broken = models.JSONField(default=list, help_text="Array of rule violations")
    
    # Coach evaluation
    zenbot_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    coach_verdict = models.TextField(blank=True)
    technical_validity = models.CharField(max_length=20, 
                                          choices=[('valid', 'Valid'), ('marginal', 'Marginal'), ('invalid', 'Invalid')],
                                          default='valid')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'zenithmentor_trade_entry'
        ordering = ['entry_candle_index']
    
    def __str__(self):
        return f"{self.direction.upper()} @ {self.entry_price} ({self.status})"
    
    def calculate_risk(self, account_balance):
        """Calculate risk metrics."""
        if self.direction == 'long':
            pips_risked = abs(self.entry_price - self.stop_loss)
        else:
            pips_risked = abs(self.stop_loss - self.entry_price)
        
        self.risk_amount = self.position_size * pips_risked
        self.risk_percentage = (self.risk_amount / account_balance) * 100
        
        if self.take_profit:
            if self.direction == 'long':
                pips_reward = abs(self.take_profit - self.entry_price)
            else:
                pips_reward = abs(self.entry_price - self.take_profit)
            
            self.reward_risk_ratio = pips_reward / pips_risked if pips_risked > 0 else 0
        
        self.save()


class SkillBadge(models.Model):
    """Gamification badges for achievements."""
    
    CATEGORY_CHOICES = [
        ('discipline', 'Discipline'),
        ('performance', 'Performance'),
        ('consistency', 'Consistency'),
        ('milestone', 'Milestone'),
        ('mastery', 'Strategy Mastery'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Requirements
    requirement_criteria = models.JSONField(help_text="Dict of requirements to earn badge")
    
    # Visual
    icon_name = models.CharField(max_length=50, help_text="Bootstrap icon name")
    color = models.CharField(max_length=20, default='gold')
    
    # Earned by
    apprentices = models.ManyToManyField(ApprenticeProfile, through='BadgeAward', related_name='badges')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'zenithmentor_skill_badge'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class BadgeAward(models.Model):
    """Junction table tracking when apprentices earn badges."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apprentice = models.ForeignKey(ApprenticeProfile, on_delete=models.CASCADE)
    badge = models.ForeignKey(SkillBadge, on_delete=models.CASCADE)
    
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_for = models.TextField(help_text="Description of what triggered the award")
    
    class Meta:
        db_table = 'zenithmentor_badge_award'
        unique_together = [['apprentice', 'badge']]
        ordering = ['-awarded_at']
    
    def __str__(self):
        return f"{self.apprentice.user.email} earned {self.badge.name}"


class AssessmentResult(models.Model):
    """Results from end-of-module assessments and certification exams."""
    
    ASSESSMENT_TYPE_CHOICES = [
        ('quiz', 'Knowledge Quiz'),
        ('simulation', 'Graded Simulation'),
        ('prop_challenge', 'Prop Challenge'),
        ('certification', 'Certification Exam'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apprentice = models.ForeignKey(ApprenticeProfile, on_delete=models.CASCADE, related_name='assessments')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assessments', null=True, blank=True)
    
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES)
    
    # Results
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    passed = models.BooleanField(default=False)
    
    # Details
    questions_total = models.IntegerField(null=True, blank=True)
    questions_correct = models.IntegerField(null=True, blank=True)
    simulation_runs = models.ManyToManyField(SimulationRun, blank=True, related_name='assessments')
    
    # Feedback
    feedback = models.TextField(blank=True)
    areas_of_strength = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    
    # Metadata
    attempted_at = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'zenithmentor_assessment_result'
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.apprentice.user.email} - {self.assessment_type} ({self.score}/{self.max_score})"


class CoachingSession(models.Model):
    """Records of adaptive coaching interactions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apprentice = models.ForeignKey(ApprenticeProfile, on_delete=models.CASCADE, related_name='coaching_sessions')
    simulation_run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, null=True, blank=True, related_name='coaching_sessions')
    
    # Coaching content
    topic = models.CharField(max_length=200)
    message = models.TextField()
    recommendation = models.TextField(blank=True)
    
    # Context
    triggered_by = models.CharField(max_length=100, help_text="What event triggered this coaching")
    datapoints = models.JSONField(default=dict, help_text="Technical/psychological data that informed the coaching")
    
    # ML features used
    ml_features_snapshot = models.JSONField(default=dict, help_text="Apprentice features at time of coaching")
    
    # Apprentice response
    apprentice_acknowledged = models.BooleanField(default=False)
    apprentice_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'zenithmentor_coaching_session'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Coaching: {self.apprentice.user.email} - {self.topic}"


class MLModel(models.Model):
    """Tracking for ML models used in adaptive coaching."""
    
    MODEL_TYPE_CHOICES = [
        ('apprentice_classifier', 'Apprentice Type Classifier'),
        ('pass_predictor', 'Pass Probability Predictor'),
        ('difficulty_recommender', 'Difficulty Recommender'),
        ('sentiment_analyzer', 'Journal Sentiment Analyzer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES)
    version = models.CharField(max_length=20)
    
    # Model artifacts
    model_file_path = models.CharField(max_length=500, help_text="Path to pickled model")
    feature_names = models.JSONField(help_text="List of feature names in training order")
    
    # Training metadata
    training_samples = models.IntegerField()
    training_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    training_notes = models.TextField(blank=True)
    
    # Deployment
    is_active = models.BooleanField(default=False)
    deployed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'zenithmentor_ml_model'
        ordering = ['-created_at']
        unique_together = [['model_type', 'version']]
    
    def __str__(self):
        return f"{self.model_type} v{self.version} ({'Active' if self.is_active else 'Inactive'})"
