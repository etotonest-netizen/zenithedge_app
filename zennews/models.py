"""
ZenNews Models - Financial News Integration
Stores and tracks financial news events with sentiment analysis
"""
import uuid
from django.db import models
from django.utils import timezone


class NewsEvent(models.Model):
    """
    Represents a single financial news event with sentiment analysis
    """
    IMPACT_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=20, db_index=True, help_text="Trading symbol (e.g., EURUSD, XAUUSD)")
    headline = models.TextField(help_text="News headline")
    content_extract = models.TextField(blank=True, help_text="Brief content extract (25 words max)")
    sentiment = models.FloatField(default=0.0, help_text="Sentiment score: -1.0 (negative) to 1.0 (positive)")
    sentiment_score = models.FloatField(default=0.0, db_index=True, help_text="Alias for sentiment (backward compat)")
    impact_level = models.CharField(
        max_length=10, 
        choices=IMPACT_CHOICES, 
        default='low',
        help_text="Impact level based on content analysis"
    )
    relevance_rank = models.IntegerField(default=50, db_index=True, help_text="Relevance ranking 0-100 (higher = more relevant)")
    symbol_tags = models.JSONField(default=list, help_text="List of related symbols [EURUSD, GBP, EUR]")
    topic = models.CharField(max_length=100, blank=True, null=True, help_text="Detected topic/category")
    source = models.CharField(max_length=100, help_text="News source name")
    source_url = models.URLField(blank=True, null=True, help_text="Original article URL")
    content_hash = models.CharField(max_length=64, db_index=True, help_text="SHA256 hash for deduplication")
    timestamp = models.DateTimeField(db_index=True, help_text="Publication timestamp")
    published_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Alias for timestamp")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['impact_level', 'timestamp']),
            models.Index(fields=['content_hash']),
        ]
        verbose_name = "News Event"
        verbose_name_plural = "News Events"
    
    def __str__(self):
        return f"{self.symbol} - {self.headline[:50]}... ({self.timestamp})"
    
    def get_sentiment_label(self):
        """Get human-readable sentiment label"""
        if self.sentiment > 0.3:
            return "Positive"
        elif self.sentiment < -0.3:
            return "Negative"
        else:
            return "Neutral"
    
    def get_sentiment_badge_class(self):
        """Get Bootstrap badge class for sentiment display"""
        if self.sentiment > 0.3:
            return "badge-success"
        elif self.sentiment < -0.3:
            return "badge-danger"
        else:
            return "badge-secondary"
    
    def get_impact_badge_class(self):
        """Get Bootstrap badge class for impact level"""
        if self.impact_level == 'high':
            return "badge-danger"
        elif self.impact_level == 'medium':
            return "badge-warning"
        else:
            return "badge-info"
    
    def get_time_ago(self):
        """Get human-readable time since publication"""
        from datetime import datetime, timedelta
        now = timezone.now()
        pub_time = self.published_at or self.timestamp
        diff = now - pub_time
        
        if diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago" if minutes > 0 else "just now"
        elif diff < timedelta(hours=24):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = diff.days
            return f"{days}d ago"
    
    def get_short_extract(self, max_words=25):
        """Get shortened content extract"""
        if not self.content_extract:
            return ""
        words = self.content_extract.split()
        if len(words) <= max_words:
            return self.content_extract
        return ' '.join(words[:max_words]) + '...'
    
    def matches_symbol(self, symbol):
        """Check if news is relevant to given symbol"""
        if not symbol:
            return False
        symbol = symbol.upper()
        
        # Direct match
        if symbol == self.symbol.upper():
            return True
        
        # Check symbol_tags
        if self.symbol_tags:
            for tag in self.symbol_tags:
                if symbol in tag.upper() or tag.upper() in symbol:
                    return True
        
        return False


class NewsTopic(models.Model):
    """
    Represents clustered topics extracted from news
    """
    name = models.CharField(max_length=100, unique=True)
    keyword_list = models.TextField(help_text="Comma-separated keywords")
    news_count = models.IntegerField(default=0, help_text="Number of related news items")
    avg_sentiment = models.FloatField(default=0.0, help_text="Average sentiment of related news")
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-news_count', 'name']
        verbose_name = "News Topic"
        verbose_name_plural = "News Topics"
    
    def __str__(self):
        return f"{self.name} ({self.news_count} articles)"


class NewsAlert(models.Model):
    """
    High-impact news alerts for dashboard notifications
    """
    news_event = models.ForeignKey(NewsEvent, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, default='high_impact')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "News Alert"
        verbose_name_plural = "News Alerts"
    
    def __str__(self):
        return f"Alert: {self.news_event.symbol} - {self.alert_type}"
