"""
Notification Manager - Handles creation and delivery of AI Insight notifications
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import InsightNotification, NotificationPreference, NotificationDeliveryLog

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Central manager for creating and delivering notifications
    """
    
    @staticmethod
    def calculate_priority(signal):
        """
        Calculate notification priority based on signal attributes
        
        Criteria:
        - Confidence > 80 → High
        - News impact present → High  
        - Recent duplicate strategy → Low
        
        Args:
            signal: Signal object
            
        Returns:
            str: 'high', 'medium', or 'low'
        """
        # High confidence signals are high priority
        if signal.confidence >= 80:
            return 'high'
        
        # Check if signal has high-impact news
        if hasattr(signal, 'validation') and signal.validation:
            quality_metrics = signal.validation.quality_metrics or {}
            news_context = quality_metrics.get('news_context', '')
            if news_context and len(news_context) > 50:  # Has substantial news
                return 'high'
        
        # Check for recent duplicates (same strategy within 10 minutes)
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        recent_same_strategy = signal.__class__.objects.filter(
            user=signal.user,
            strategy=signal.strategy,
            received_at__gte=ten_minutes_ago
        ).count()
        
        if recent_same_strategy > 3:  # Too many recent signals
            return 'low'
        
        # Default to medium
        return 'medium'
    
    @staticmethod
    def format_message(signal):
        """
        Format the notification message with narrative snippet
        
        Args:
            signal: Signal object with validation
            
        Returns:
            dict: {title, snippet, news_headline}
        """
        # Build title
        side_emoji = "🟢" if signal.side.lower() == 'buy' else "🔴"
        title = f"{side_emoji} New Insight – {signal.symbol} ({signal.timeframe})"
        
        # Extract AI narrative snippet
        snippet = "AI analysis in progress..."
        news_headline = None
        
        if hasattr(signal, 'validation') and signal.validation:
            # Get context summary (already formatted by contextualizer)
            context = signal.validation.context_summary or ""
            
            # Extract first 1-2 sentences (max 200 chars)
            if context:
                sentences = context.split('. ')
                snippet_parts = []
                char_count = 0
                
                for sentence in sentences[:3]:
                    if char_count + len(sentence) > 200:
                        break
                    snippet_parts.append(sentence)
                    char_count += len(sentence)
                
                snippet = '. '.join(snippet_parts)
                if not snippet.endswith('.'):
                    snippet += '.'
            
            # Extract news headline if available
            quality_metrics = signal.validation.quality_metrics or {}
            news_context = quality_metrics.get('news_context', '')
            if news_context:
                # Extract first news headline from format "2h ago: Headline | 3h ago: Another"
                news_parts = news_context.split('|')[0].strip()
                if ':' in news_parts:
                    news_headline = news_parts.split(':', 1)[1].strip()[:150]
        
        # Add color coding based on confidence
        if signal.confidence >= 85:
            snippet = f"🎯 High confidence ({signal.confidence:.0f}%). {snippet}"
        elif signal.confidence >= 75:
            snippet = f"✅ Solid ({signal.confidence:.0f}%). {snippet}"
        elif signal.confidence >= 65:
            snippet = f"⚠️ Moderate ({signal.confidence:.0f}%). {snippet}"
        else:
            snippet = f"📊 Conditional ({signal.confidence:.0f}%). {snippet}"
        
        return {
            'title': title,
            'snippet': snippet,
            'news_headline': news_headline
        }
    
    @staticmethod
    def create_notification(signal, user=None):
        """
        Create notification record for a signal
        
        Args:
            signal: Signal object
            user: User object (if None, uses signal.user)
            
        Returns:
            InsightNotification or None
        """
        if user is None:
            user = signal.user
        
        if not user:
            logger.warning(f"Cannot create notification for signal #{signal.id} - no user")
            return None
        
        # Get or create user preferences
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        
        # Calculate priority
        priority = NotificationManager.calculate_priority(signal)
        
        # Check if user should receive this notification
        if not prefs.should_notify(signal, priority):
            logger.info(f"User {user.email} preferences blocked notification for signal #{signal.id}")
            return None
        
        # Format message
        message_data = NotificationManager.format_message(signal)
        
        # Create notification record
        notification = InsightNotification.objects.create(
            user=user,
            signal=signal,
            title=message_data['title'],
            snippet=message_data['snippet'],
            confidence=signal.confidence,
            priority=priority,
            news_headline=message_data['news_headline']
        )
        
        logger.info(f"Created notification #{notification.id} for {user.email} - Signal #{signal.id}")
        return notification
    
    @staticmethod
    def push(signal, user=None):
        """
        Main entry point: Create and deliver notification
        
        Args:
            signal: Signal object
            user: User object (if None, uses signal.user)
            
        Returns:
            bool: True if notification was created and delivered
        """
        try:
            # Create notification record
            notification = NotificationManager.create_notification(signal, user)
            
            if not notification:
                return False
            
            # Deliver via WebSocket
            delivered = NotificationManager.deliver_websocket(notification)
            
            if delivered:
                notification.delivered = True
                notification.save(update_fields=['delivered'])
            
            return delivered
            
        except Exception as e:
            logger.error(f"Error pushing notification for signal #{signal.id}: {e}")
            return False
    
    @staticmethod
    def deliver_websocket(notification):
        """
        Deliver notification via Django Channels WebSocket
        
        Args:
            notification: InsightNotification object
            
        Returns:
            bool: True if delivered successfully
        """
        try:
            channel_layer = get_channel_layer()
            
            if not channel_layer:
                logger.error("Channel layer not configured!")
                NotificationManager.log_delivery(notification, 'websocket', False, 
                                                "Channel layer not available")
                return False
            
            # Send to user's personal group
            group_name = f"user_{notification.user.id}_notifications"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_message',
                    'notification': notification.to_dict()
                }
            )
            
            logger.info(f"Delivered notification #{notification.id} via WebSocket to {group_name}")
            NotificationManager.log_delivery(notification, 'websocket', True)
            return True
            
        except Exception as e:
            logger.error(f"WebSocket delivery failed for notification #{notification.id}: {e}")
            NotificationManager.log_delivery(notification, 'websocket', False, str(e))
            return False
    
    @staticmethod
    def log_delivery(notification, channel, success, error_message=None):
        """
        Log delivery attempt
        
        Args:
            notification: InsightNotification object
            channel: str (websocket, push, email)
            success: bool
            error_message: str (optional)
        """
        try:
            NotificationDeliveryLog.objects.create(
                notification=notification,
                channel=channel,
                success=success,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to log delivery: {e}")
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for user"""
        return InsightNotification.objects.filter(user=user, read=False).count()
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for user"""
        unread = InsightNotification.objects.filter(user=user, read=False)
        count = unread.update(read=True, read_at=timezone.now())
        logger.info(f"Marked {count} notifications as read for {user.email}")
        return count
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """
        Delete old read notifications
        
        Args:
            days: int, delete notifications older than this many days
            
        Returns:
            int: Number of notifications deleted
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        old_notifications = InsightNotification.objects.filter(
            read=True,
            read_at__lt=cutoff_date
        )
        count = old_notifications.count()
        old_notifications.delete()
        logger.info(f"Cleaned up {count} old notifications (older than {days} days)")
        return count
