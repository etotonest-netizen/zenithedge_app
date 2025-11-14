"""
PropCoach Signals
Automatic rule checking and violation detection
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from .models import TradeRecord, PropChallenge, PropRuleViolation


@receiver(post_save, sender=TradeRecord)
def check_trade_violations(sender, instance, created, **kwargs):
    """
    Automatically check for rule violations when a trade is closed
    """
    if instance.status != 'closed':
        return
    
    challenge = instance.challenge
    template = challenge.template
    violations_found = []
    
    # 1. Check minimum trade duration
    if template.min_trade_duration_minutes > 0:
        if instance.hold_duration_minutes < template.min_trade_duration_minutes:
            violation = PropRuleViolation.objects.create(
                challenge=challenge,
                trade=instance,
                violation_type='min_trade_time',
                severity='minor',
                description=f'Trade held for only {instance.hold_duration_minutes} minutes, minimum is {template.min_trade_duration_minutes}',
                value_breached=Decimal(str(instance.hold_duration_minutes)),
                limit_value=Decimal(str(template.min_trade_duration_minutes)),
                auto_detected=True
            )
            violations_found.append(violation)
            instance.has_violations = True
            instance.violation_notes += f"Min duration violated; "
    
    # 2. Check position size
    if instance.position_size_percent > template.max_position_size_percent:
        violation = PropRuleViolation.objects.create(
            challenge=challenge,
            trade=instance,
            violation_type='max_position_size',
            severity='major',
            description=f'Position size {instance.position_size_percent}% exceeds maximum {template.max_position_size_percent}%',
            value_breached=instance.position_size_percent,
            limit_value=template.max_position_size_percent,
            auto_detected=True
        )
        violations_found.append(violation)
        instance.has_violations = True
        instance.violation_notes += f"Position size exceeded; "
    
    # 3. Check leverage
    if instance.leverage_used > template.max_leverage:
        violation = PropRuleViolation.objects.create(
            challenge=challenge,
            trade=instance,
            violation_type='max_leverage',
            severity='major',
            description=f'Leverage {instance.leverage_used}x exceeds maximum {template.max_leverage}x',
            value_breached=instance.leverage_used,
            limit_value=template.max_leverage,
            auto_detected=True
        )
        violations_found.append(violation)
        instance.has_violations = True
        instance.violation_notes += f"Leverage exceeded; "
    
    # 4. Check weekend holding (simplified - checks if exit is Monday and entry was Friday)
    if not template.allow_weekend_holding:
        entry_day = instance.entry_time.weekday()  # Monday = 0, Sunday = 6
        exit_day = instance.exit_time.weekday() if instance.exit_time else entry_day
        
        # If entered on Friday (4) and exited on Monday (0), violation
        if entry_day == 4 and exit_day == 0:
            violation = PropRuleViolation.objects.create(
                challenge=challenge,
                trade=instance,
                violation_type='weekend_hold',
                severity='major',
                description='Trade held over weekend - not allowed by firm rules',
                auto_detected=True
            )
            violations_found.append(violation)
            instance.has_violations = True
            instance.violation_notes += f"Weekend holding; "
    
    # Update challenge violation count and send alerts
    if violations_found:
        challenge.violation_count += len(violations_found)
        challenge.save()
        instance.save()
        
        # Send alert for each violation
        from propcoach.notifications import send_violation_alert
        for violation in violations_found:
            send_violation_alert(violation)
    
    # Check critical violations (drawdown)
    check_challenge_violations(challenge)


def check_challenge_violations(challenge):
    """
    Check challenge-level violations (drawdown, time limits)
    """
    template = challenge.template
    critical_violations = []
    
    # Check daily drawdown
    max_daily_loss = template.get_max_daily_loss()
    if challenge.current_daily_drawdown > max_daily_loss:
        violation = PropRuleViolation.objects.create(
            challenge=challenge,
            violation_type='daily_drawdown',
            severity='critical',
            description=f'Daily drawdown ${challenge.current_daily_drawdown} exceeds limit ${max_daily_loss}',
            value_breached=challenge.current_daily_drawdown,
            limit_value=max_daily_loss,
            auto_detected=True,
            challenge_failed=True
        )
        critical_violations.append(violation)
        
        # Fail the challenge
        challenge.status = 'failed'
        challenge.completion_date = timezone.now()
        challenge.completion_notes = f"Challenge failed due to daily drawdown violation: ${challenge.current_daily_drawdown}"
        challenge.save()
        
        # Send critical violation alert and completion notification
        from propcoach.notifications import send_violation_alert, send_challenge_complete_alert
        send_violation_alert(violation)
        send_challenge_complete_alert(challenge)
    
    # Check total drawdown
    max_total_loss = template.get_max_total_loss()
    if challenge.current_total_drawdown > max_total_loss:
        violation = PropRuleViolation.objects.create(
            challenge=challenge,
            violation_type='total_drawdown',
            severity='critical',
            description=f'Total drawdown ${challenge.current_total_drawdown} exceeds limit ${max_total_loss}',
            value_breached=challenge.current_total_drawdown,
            limit_value=max_total_loss,
            auto_detected=True,
            challenge_failed=True
        )
        critical_violations.append(violation)
        
        # Fail the challenge
        challenge.status = 'failed'
        challenge.completion_date = timezone.now()
        challenge.completion_notes = f"Challenge failed due to total drawdown violation: ${challenge.current_total_drawdown}"
        challenge.save()
        
        # Send critical violation alert and completion notification
        from propcoach.notifications import send_violation_alert, send_challenge_complete_alert
        send_violation_alert(violation)
        send_challenge_complete_alert(challenge)
    
    # Check if profit target met
    if challenge.total_profit_loss >= challenge.profit_target:
        if challenge.trading_days_count >= template.min_trading_days:
            if challenge.violation_count == 0:
                # Challenge passed!
                challenge.status = 'passed'
                challenge.completion_date = timezone.now()
                challenge.completion_notes = f"Challenge passed! Profit: ${challenge.total_profit_loss}"
                challenge.save()
                
                # Send completion notification
                from propcoach.notifications import send_challenge_complete_alert
                send_challenge_complete_alert(challenge)
    
    return critical_violations
