"""
Notification System for PropCoach

Handles in-app and email notifications for:
- Rule violations
- Challenge completion
- Performance milestones
- Risk warnings
"""

from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_violation_alert(violation):
    """
    Send immediate alert for rule violation.
    
    Args:
        violation: PropRuleViolation instance
    """
    try:
        challenge = violation.challenge
        user = challenge.user
        
        # Prepare notification data
        notification_data = {
            'user': user,
            'challenge': challenge,
            'violation': violation,
            'severity': violation.get_severity_display(),
            'firm': challenge.template.get_firm_name_display(),
            'timestamp': violation.timestamp
        }
        
        # Create in-app notification (using CoachingFeedback model)
        from propcoach.models import CoachingFeedback
        
        priority = 10 if violation.severity == 'critical' else 8 if violation.severity == 'major' else 6
        
        title = f"⚠️ {violation.get_severity_display().upper()} VIOLATION"
        message = (
            f"**Violation Type:** {violation.get_violation_type_display()}\n\n"
            f"**Description:** {violation.description}\n\n"
        )
        
        if violation.value_breached and violation.limit_value:
            message += f"**Value:** {violation.value_breached} (Limit: {violation.limit_value})\n\n"
        
        if violation.challenge_failed:
            message += "⚠️ **YOUR CHALLENGE HAS FAILED** ⚠️\n\n"
            message += "This critical violation has automatically failed your challenge."
        else:
            message += "**Action Required:** Review your trading rules and avoid further violations."
        
        CoachingFeedback.objects.create(
            challenge=challenge,
            user=user,
            feedback_type='risk_warning',
            title=title,
            message=message,
            priority=priority,
            is_actionable=True
        )
        
        # Send email if critical
        if violation.severity in ['critical', 'major']:
            send_violation_email(user, notification_data)
        
        logger.info(f"Violation alert sent to {user.username}: {violation.violation_type}")
        
    except Exception as e:
        logger.error(f"Failed to send violation alert: {e}", exc_info=True)


def send_violation_email(user, notification_data):
    """Send email notification for violation."""
    try:
        violation = notification_data['violation']
        challenge = notification_data['challenge']
        
        subject = f"⚠️ Rule Violation Alert - {challenge.template.get_firm_name_display()}"
        
        message = f"""
Hi {user.username},

A {violation.get_severity_display()} rule violation has been detected in your {challenge.template.template_name} challenge.

Violation Type: {violation.get_violation_type_display()}
Description: {violation.description}
Time: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{f"Challenge Status: FAILED" if violation.challenge_failed else "Please review your trading rules to avoid further violations."}

Log in to view full details:
{settings.SITE_URL}/propcoach/challenge/{challenge.id}/

Best regards,
ZenithEdge PropCoach
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
        
        logger.info(f"Violation email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send violation email: {e}", exc_info=True)


def send_challenge_complete_alert(challenge):
    """
    Send notification when challenge is completed (passed or failed).
    
    Args:
        challenge: PropChallenge instance
    """
    try:
        user = challenge.user
        template = challenge.template
        
        # Create in-app notification
        from propcoach.models import CoachingFeedback
        
        if challenge.status == 'passed':
            title = "🎉 Challenge PASSED!"
            message = (
                f"**Congratulations!** You've successfully passed the {template.template_name}!\n\n"
                f"**Final Results:**\n"
                f"• Total P/L: ${challenge.total_profit_loss:.2f}\n"
                f"• Win Rate: {challenge.win_rate:.1f}%\n"
                f"• Total Trades: {challenge.total_trades}\n"
                f"• Violations: {challenge.violation_count}\n"
                f"• Days Taken: {challenge.days_elapsed}\n\n"
                f"**Next Steps:**\n"
                f"• Review your performance metrics\n"
                f"• Consider moving to Phase 2 or a larger account\n"
                f"• Keep up the excellent discipline!"
            )
            priority = 5
            feedback_type = 'achievement'
            
        else:  # failed
            title = "Challenge Failed"
            message = (
                f"Unfortunately, your {template.template_name} challenge has failed.\n\n"
                f"**Final Results:**\n"
                f"• Total P/L: ${challenge.total_profit_loss:.2f}\n"
                f"• Win Rate: {challenge.win_rate:.1f}%\n"
                f"• Total Trades: {challenge.total_trades}\n"
                f"• Violations: {challenge.violation_count}\n"
                f"• Days Taken: {challenge.days_elapsed}\n\n"
                f"**Failure Reason:**\n"
                f"{challenge.completion_notes}\n\n"
                f"**Recommendations:**\n"
                f"• Review what went wrong\n"
                f"• Take a break and analyze your mistakes\n"
                f"• Start a fresh challenge when ready\n"
                f"• Consider reviewing PropCoach training materials"
            )
            priority = 7
            feedback_type = 'performance_alert'
        
        CoachingFeedback.objects.create(
            challenge=challenge,
            user=user,
            feedback_type=feedback_type,
            title=title,
            message=message,
            priority=priority,
            is_actionable=True
        )
        
        # Send email
        send_challenge_complete_email(user, challenge)
        
        logger.info(f"Challenge complete alert sent to {user.username}: {challenge.status}")
        
    except Exception as e:
        logger.error(f"Failed to send challenge complete alert: {e}", exc_info=True)


def send_challenge_complete_email(user, challenge):
    """Send email for challenge completion."""
    try:
        template = challenge.template
        
        if challenge.status == 'passed':
            subject = f"🎉 Congratulations! Challenge Passed - {template.get_firm_name_display()}"
            emoji = "🎉"
            status_text = "PASSED"
        else:
            subject = f"Challenge Update - {template.get_firm_name_display()}"
            emoji = "📊"
            status_text = "FAILED"
        
        message = f"""
Hi {user.username},

{emoji} Your {template.template_name} challenge has {status_text}!

FINAL RESULTS:
--------------
Profit/Loss: ${challenge.total_profit_loss:.2f}
Win Rate: {challenge.win_rate:.1f}%
Total Trades: {challenge.total_trades}
Violations: {challenge.violation_count}
Days Taken: {challenge.days_elapsed}

{f"Congratulations on your success! Keep up the excellent work." if challenge.status == 'passed' else f"Don't give up! Review your mistakes and try again when ready."}

View full details:
{settings.SITE_URL}/propcoach/challenge/{challenge.id}/

Best regards,
ZenithEdge PropCoach
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
        
        logger.info(f"Challenge complete email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send challenge complete email: {e}", exc_info=True)


def send_daily_summary(challenge):
    """
    Send end-of-day summary for active challenge.
    
    Args:
        challenge: PropChallenge instance
    """
    try:
        # This is typically called by a scheduled task
        # It creates a CoachingFeedback entry which can be viewed in the dashboard
        
        from propcoach.coaching import generate_daily_feedback
        
        result = generate_daily_feedback(challenge)
        
        if result:
            logger.info(f"Daily summary generated for {challenge.user.username}")
        
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}", exc_info=True)


def send_readiness_update(challenge, old_score: float, new_score: float):
    """
    Send notification when funding readiness score changes significantly.
    
    Args:
        challenge: PropChallenge instance
        old_score: Previous readiness score
        new_score: New readiness score
    """
    try:
        # Only notify on significant changes (>10 points)
        change = abs(new_score - old_score)
        
        if change < 10:
            return
        
        user = challenge.user
        
        # Create in-app notification
        from propcoach.models import CoachingFeedback
        
        if new_score > old_score:
            title = f"📈 Readiness Score Improved: {new_score:.0f}/100"
            message = (
                f"Great progress! Your funding readiness score has increased "
                f"from {old_score:.0f} to {new_score:.0f} (+{change:.0f}).\n\n"
                f"Keep up the good work and maintain your discipline!"
            )
            priority = 4
        else:
            title = f"📉 Readiness Score Declined: {new_score:.0f}/100"
            message = (
                f"Your funding readiness score has decreased "
                f"from {old_score:.0f} to {new_score:.0f} (-{change:.0f}).\n\n"
                f"Review your recent trades and identify areas for improvement."
            )
            priority = 6
        
        CoachingFeedback.objects.create(
            challenge=challenge,
            user=user,
            feedback_type='performance_alert',
            title=title,
            message=message,
            priority=priority,
            is_actionable=False
        )
        
        logger.info(f"Readiness update sent to {user.username}: {old_score:.0f} → {new_score:.0f}")
        
    except Exception as e:
        logger.error(f"Failed to send readiness update: {e}", exc_info=True)


def send_milestone_alert(challenge, milestone_type: str):
    """
    Send notification for achievement milestones.
    
    Args:
        challenge: PropChallenge instance
        milestone_type: Type of milestone (e.g., '50_percent', 'no_violations')
    """
    try:
        user = challenge.user
        
        milestones = {
            '50_percent': {
                'title': '🎯 Halfway to Target!',
                'message': f"You've reached 50% of your profit target! Keep going!",
                'priority': 4
            },
            '75_percent': {
                'title': '🎯 75% Complete!',
                'message': f"You're 75% of the way to your profit target! Almost there!",
                'priority': 4
            },
            '90_percent': {
                'title': '🎯 Target Almost Reached!',
                'message': f"You're at 90% of your profit target! Be conservative now.",
                'priority': 5
            },
            'no_violations_10': {
                'title': '✅ 10 Trades - Perfect Discipline!',
                'message': f"10 trades with zero violations! Excellent discipline!",
                'priority': 4
            },
            'no_violations_20': {
                'title': '✅ 20 Trades - Perfect Discipline!',
                'message': f"20 trades with zero violations! This is prop firm level!",
                'priority': 4
            },
            'high_win_rate': {
                'title': '🔥 Excellent Win Rate!',
                'message': f"Your win rate of {challenge.win_rate:.1f}% is outstanding!",
                'priority': 4
            }
        }
        
        milestone_data = milestones.get(milestone_type)
        if not milestone_data:
            return
        
        # Create in-app notification
        from propcoach.models import CoachingFeedback
        
        CoachingFeedback.objects.create(
            challenge=challenge,
            user=user,
            feedback_type='achievement',
            title=milestone_data['title'],
            message=milestone_data['message'],
            priority=milestone_data['priority'],
            is_actionable=False
        )
        
        logger.info(f"Milestone alert sent to {user.username}: {milestone_type}")
        
    except Exception as e:
        logger.error(f"Failed to send milestone alert: {e}", exc_info=True)


def get_unread_notifications(user, limit: int = 20):
    """
    Get unread notifications for a user.
    
    Args:
        user: User object
        limit: Maximum number to return
        
    Returns:
        QuerySet of unread CoachingFeedback
    """
    from propcoach.models import CoachingFeedback
    
    return CoachingFeedback.objects.filter(
        user=user,
        is_read=False
    ).order_by('-priority', '-timestamp')[:limit]


def mark_notification_read(notification_id, user):
    """
    Mark a notification as read.
    
    Args:
        notification_id: CoachingFeedback ID
        user: User object
    """
    from propcoach.models import CoachingFeedback
    
    try:
        CoachingFeedback.objects.filter(
            id=notification_id,
            user=user
        ).update(is_read=True)
        
        logger.info(f"Notification {notification_id} marked as read by {user.username}")
        
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}", exc_info=True)
