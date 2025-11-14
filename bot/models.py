from django.db import models
from django.conf import settings


class BotQA(models.Model):
    """
    Knowledge base for ZenBot Q&A system.
    Stores question-answer pairs with categories and metadata.
    """
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('strategy', 'Trading Strategy'),
        ('risk', 'Risk Management'),
        ('challenge', 'Prop Challenge'),
        ('technical', 'Technical Support'),
        ('signals', 'Signal Information'),
        ('journal', 'Trade Journal'),
        ('replay', 'Trade Replay'),
    ]
    
    question = models.TextField(
        help_text="Question or query phrase (supports multiple variations separated by |)"
    )
    answer = models.TextField(
        help_text="Bot response to this question"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        db_index=True
    )
    keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated keywords for better matching"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Higher priority answers shown first (0-100)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bot_qas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this answer was used"
    )
    
    class Meta:
        db_table = 'bot_qa'
        ordering = ['-priority', '-usage_count', '-created_at']
        verbose_name = 'Bot Q&A'
        verbose_name_plural = 'Bot Q&As'
    
    def __str__(self):
        return f"{self.category}: {self.question[:50]}..."
    
    def increment_usage(self):
        """Track answer usage for analytics"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class BotConversation(models.Model):
    """
    Stores user conversation history for context awareness.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bot_conversations'
    )
    session_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Browser session identifier"
    )
    user_message = models.TextField()
    bot_response = models.TextField()
    matched_qa = models.ForeignKey(
        BotQA,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    confidence_score = models.FloatField(
        default=0.0,
        help_text="Match confidence (0-100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bot_conversation'
        ordering = ['-created_at']
        verbose_name = 'Bot Conversation'
        verbose_name_plural = 'Bot Conversations'
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class BotSettings(models.Model):
    """
    Global bot configuration and training settings.
    """
    match_threshold = models.FloatField(
        default=60.0,
        help_text="Minimum similarity score for Q&A matching (0-100)"
    )
    enable_user_stats = models.BooleanField(
        default=True,
        help_text="Allow bot to query user-specific data"
    )
    enable_signal_queries = models.BooleanField(
        default=True,
        help_text="Allow bot to query signal database"
    )
    enable_learning = models.BooleanField(
        default=False,
        help_text="Enable bot to learn from conversations (future feature)"
    )
    default_fallback_message = models.TextField(
        default="I'm not sure about that. Could you rephrase your question or ask about strategies, signals, risk management, or your challenge status?",
        help_text="Response when no match is found"
    )
    max_conversation_history = models.IntegerField(
        default=100,
        help_text="Maximum conversation records per user"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'bot_settings'
        verbose_name = 'Bot Settings'
        verbose_name_plural = 'Bot Settings'
    
    def __str__(self):
        return f"Bot Settings (Updated: {self.updated_at})"
    
    @classmethod
    def get_settings(cls):
        """Get or create singleton settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class BotChatHistory(models.Model):
    """
    Stores all ZenBot chat interactions for admin review and analysis.
    Enables tracking user queries, bot responses, and conversation patterns.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bot_chats'
    )
    prompt = models.TextField(help_text="User's input/query")
    response = models.TextField(help_text="Bot's response")
    
    # Command tracking
    is_command = models.BooleanField(
        default=False,
        help_text="True if prompt was a slash command"
    )
    command_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Command type: score, prop, strategy, etc."
    )
    
    # Response metadata
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken to generate response (milliseconds)"
    )
    matched_qa = models.ForeignKey(
        BotQA,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_history'
    )
    confidence_score = models.FloatField(
        default=0.0,
        help_text="Match confidence if using Q&A system"
    )
    
    # Context
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Browser session identifier for conversation threading"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'bot_chat_history'
        ordering = ['-created_at']
        verbose_name = 'Bot Chat History'
        verbose_name_plural = 'Bot Chat Histories'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_command', 'command_type']),
        ]
    
    def __str__(self):
        cmd_str = f" [{self.command_type}]" if self.is_command else ""
        return f"{self.user.username}{cmd_str} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def preview(self):
        """Return shortened preview of prompt for admin list"""
        return self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt
