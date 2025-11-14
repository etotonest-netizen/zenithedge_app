from django.db import models
from django.conf import settings
from django.utils import timezone


class SupportThread(models.Model):
    """
    Represents a support conversation thread between a user and admin.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('admin_replied', 'Admin Replied'),
        ('user_replied', 'User Replied'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_threads'
    )
    subject = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    # Link to related signal for context (ForeignKey instead of IntegerField)
    signal = models.ForeignKey(
        'signals.Signal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_threads',
        help_text="Optionally attach a signal to this support thread"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(default=timezone.now)
    
    # Track unread status
    has_unread_user_message = models.BooleanField(default=False)
    has_unread_admin_message = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-last_message_at']
        db_table = 'support_thread'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-last_message_at']),
        ]
    
    def __str__(self):
        return f"#{self.id} - {self.subject} ({self.user.email})"
    
    def get_last_message(self):
        """Get the most recent message in this thread"""
        return self.messages.order_by('-created_at').first()
    
    def mark_as_read_by_admin(self):
        """Mark all user messages as read by admin"""
        self.has_unread_user_message = False
        self.save(update_fields=['has_unread_user_message'])
    
    def mark_as_read_by_user(self):
        """Mark all admin messages as read by user"""
        self.has_unread_admin_message = False
        self.save(update_fields=['has_unread_admin_message'])
    
    @classmethod
    def get_unread_count_for_user(cls, user):
        """Get count of threads with unread admin messages for a specific user"""
        return cls.objects.filter(
            user=user,
            has_unread_admin_message=True
        ).count()
    
    @classmethod
    def get_unread_count_for_admins(cls):
        """Get count of threads with unread user messages (for admin badge)"""
        return cls.objects.filter(
            has_unread_user_message=True
        ).count()
    
    def get_related_signal(self):
        """Get the related Signal object"""
        return self.signal
    
    def get_related_journal(self):
        """Get the related TradeJournalEntry if it exists"""
        signal = self.get_related_signal()
        if signal:
            from signals.models import TradeJournalEntry
            try:
                return TradeJournalEntry.objects.get(signal=signal)
            except TradeJournalEntry.DoesNotExist:
                return None
        return None


class SupportMessage(models.Model):
    """
    Individual message within a support thread.
    """
    thread = models.ForeignKey(
        SupportThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_messages_sent'
    )
    message = models.TextField()
    is_admin_message = models.BooleanField(default=False)
    
    # Optional file attachment
    attachment = models.FileField(
        upload_to='support_attachments/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        db_table = 'support_message'
        indexes = [
            models.Index(fields=['thread', 'created_at']),
        ]
    
    def __str__(self):
        sender = "Admin" if self.is_admin_message else self.from_user.email
        return f"{sender}: {self.message[:50]}"
    
    def save(self, *args, **kwargs):
        # Update thread status and timestamps when message is created
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update thread's last_message_at
            self.thread.last_message_at = self.created_at
            
            # Update thread status and unread flags
            if self.is_admin_message:
                self.thread.status = 'admin_replied'
                self.thread.has_unread_admin_message = True
            else:
                self.thread.status = 'user_replied'
                self.thread.has_unread_user_message = True
            
            self.thread.save(update_fields=['last_message_at', 'status', 
                                           'has_unread_user_message', 
                                           'has_unread_admin_message'])
