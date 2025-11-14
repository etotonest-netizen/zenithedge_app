"""
Signal handlers to trigger notifications when insights are created/updated
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='signals.TradeValidation')
def notify_new_validation(sender, instance, created, **kwargs):
    """
    Trigger notification when a TradeValidation (AI Insight) is created
    
    This fires after validation is saved, ensuring we have full context
    """
    if created:
        # Lazy import to avoid circular dependency
        from .manager import NotificationManager
        
        signal = instance.signal
        logger.info(f"New validation created for signal #{signal.id} - triggering notification")
        
        # Push notification to user
        NotificationManager.push(signal)


@receiver(post_save, sender='signals.Signal')
def notify_signal_update(sender, instance, created, **kwargs):
    """
    Optionally notify on signal updates (e.g., outcome changes)
    
    Currently disabled - notifications only sent when validation is created
    """
    # Uncomment to enable notifications on signal updates
    # if not created and instance.outcome:
    #     logger.info(f"Signal #{instance.id} outcome updated to {instance.outcome}")
    #     # Could send update notification here
    pass
