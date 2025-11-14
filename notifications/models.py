"""
Notification models for real-time AI Insight alerts
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class InsightNotification(models.Model):
    """
    Stores notification records for AI Insights sent to users
    """
    PRIORITY_CHOICES = [
        ('high', 'High Priority'),
        ('medium', 'Medium Priority'),
        ('low', 'Low Priority'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='insight_notifications',
        help_text="User who receives this notification"
    )
    signal = models.ForeignKey(
        'signals.Signal',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Signal/Insight this notification is about"
    )
    title = models.CharField(
        max_length=120,
        help_text="Notification title (e.g., 'New Insight – EURUSD (1H)')"
    )
    snippet = models.TextField(
        help_text="Short narrative summary (1-2 lines)"
    )
    confidence = models.FloatField(
        help_text="AI confidence score (0-100)"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Notification priority level"
    )
    news_headline = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Optional news headline reference"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When notification was created"
    )
    read = models.BooleanField(
        default=False,
        help_text="Whether user has read this notification"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was read"
    )
    delivered = models.BooleanField(
        default=False,
        help_text="Whether notification was successfully delivered via WebSocket"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'read']),
        ]
    
    def __str__(self):
        return f"{self.title} → {self.user.email} ({'read' if self.read else 'unread'})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'snippet': self.snippet,
            'confidence': self.confidence,
            'priority': self.priority,
            'news_headline': self.news_headline,
            'signal_id': self.signal.id,
            'symbol': self.signal.symbol,
            'timeframe': self.signal.timeframe,
            'side': self.signal.side,
            'created_at': self.created_at.isoformat(),
            'read': self.read,
            'url': f'/signals/insight/{self.signal.id}/'
        }


class NotificationPreference(models.Model):
    """
    User preferences for notification delivery
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        help_text="User these preferences belong to"
    )
    
    # Channel toggles
    web_enabled = models.BooleanField(
        default=True,
        help_text="Enable in-app web notifications"
    )
    push_enabled = models.BooleanField(
        default=False,
        help_text="Enable browser push notifications"
    )
    email_digest_enabled = models.BooleanField(
        default=False,
        help_text="Enable daily email digest"
    )
    
    # Filtering preferences
    min_confidence = models.IntegerField(
        default=65,
        help_text="Minimum confidence threshold for notifications (0-100)"
    )
    strategies_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="List of strategies to receive notifications for (empty = all)"
    )
    symbols_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="List of symbols to receive notifications for (empty = all)"
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(
        default=False,
        help_text="Enable quiet hours (no notifications during specified time)"
    )
    quiet_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Quiet hours start time (e.g., 22:00)"
    )
    quiet_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Quiet hours end time (e.g., 08:00)"
    )
    
    # Priority filtering
    high_priority_only = models.BooleanField(
        default=False,
        help_text="Only receive high priority notifications"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
    
    def should_notify(self, signal, priority='medium'):
        """Check if user should receive notification for this signal"""
        if not self.web_enabled:
            return False
        
        if self.high_priority_only and priority != 'high':
            return False
        
        if signal.confidence < self.min_confidence:
            return False
        
        if self.strategies_filter and signal.strategy not in self.strategies_filter:
            return False
        
        if self.symbols_filter and signal.symbol not in self.symbols_filter:
            return False
        
        if self.quiet_hours_enabled and self.quiet_start_time and self.quiet_end_time:
            current_time = timezone.now().time()
            if self.quiet_start_time < self.quiet_end_time:
                if self.quiet_start_time <= current_time or current_time <= self.quiet_end_time:
                    return False
            else:
                if self.quiet_start_time <= current_time <= self.quiet_end_time:
                    return False
        
        return True


class NotificationDeliveryLog(models.Model):
    """Tracks delivery attempts and status for debugging"""
    notification = models.ForeignKey(
        InsightNotification,
        on_delete=models.CASCADE,
        related_name='delivery_logs'
    )
    channel = models.CharField(
        max_length=20,
        help_text="Delivery channel (websocket, push, email)"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether delivery was successful"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if delivery failed"
    )
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-attempted_at']
    
    def __str__(self):
        status = 'Success' if self.success else 'Failed'
        return f"{self.channel} delivery: {status} at {self.attempted_at}"
