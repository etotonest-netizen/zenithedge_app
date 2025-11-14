"""
PropCoach Mode Integration with ZenBot AI Scoring

This module provides dynamic risk adjustment and signal filtering
for users in active prop firm challenges.
"""

from typing import Dict, Tuple, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def apply_prop_mode(signal_object, ai_score: int, breakdown: Dict) -> Tuple[int, Dict]:
    """
    Apply prop firm challenge mode adjustments to AI score and signal parameters.
    
    This function dynamically adjusts the AI score and provides risk recommendations
    based on the user's current prop challenge state.
    
    Args:
        signal_object: Signal model instance
        ai_score: Base AI score (0-100)
        breakdown: Score breakdown dict
        
    Returns:
        Tuple of (adjusted_score, prop_breakdown)
    """
    from propcoach.models import PropChallenge
    from django.utils import timezone
    
    prop_breakdown = {
        'prop_mode_enabled': False,
        'has_active_challenge': False,
        'adjustments_applied': []
    }
    
    try:
        # Check if user has active prop challenge
        active_challenge = PropChallenge.objects.filter(
            user=signal_object.user,
            status='active'
        ).select_related('template').first()
        
        if not active_challenge:
            prop_breakdown['message'] = 'No active prop challenge'
            return ai_score, prop_breakdown
        
        # Enable prop mode
        prop_breakdown['prop_mode_enabled'] = True
        prop_breakdown['has_active_challenge'] = True
        prop_breakdown['challenge_id'] = str(active_challenge.id)
        prop_breakdown['firm_name'] = active_challenge.template.get_firm_name_display()
        prop_breakdown['phase'] = active_challenge.template.phase
        
        # Calculate current challenge metrics
        template = active_challenge.template
        current_balance = active_challenge.current_balance
        initial_balance = active_challenge.initial_balance
        current_daily_dd = active_challenge.current_daily_drawdown
        current_total_dd = active_challenge.current_total_drawdown
        
        # Get limits
        max_daily_loss = template.get_max_daily_loss()
        max_total_loss = template.get_max_total_loss()
        profit_target = template.get_profit_target_amount()
        
        # Calculate percentages
        daily_dd_percent = (current_daily_dd / max_daily_loss * 100) if max_daily_loss > 0 else 0
        total_dd_percent = (current_total_dd / max_total_loss * 100) if max_total_loss > 0 else 0
        profit_progress = (active_challenge.total_profit_loss / profit_target * 100) if profit_target > 0 else 0
        
        # Add metrics to breakdown
        prop_breakdown['metrics'] = {
            'current_balance': float(current_balance),
            'profit_loss': float(active_challenge.total_profit_loss),
            'profit_progress_percent': round(profit_progress, 2),
            'daily_drawdown_used_percent': round(daily_dd_percent, 2),
            'total_drawdown_used_percent': round(total_dd_percent, 2),
            'violation_count': active_challenge.violation_count,
            'days_elapsed': active_challenge.days_elapsed,
            'days_remaining': active_challenge.days_remaining,
            'win_rate': active_challenge.win_rate
        }
        
        # Start with base score
        adjusted_score = ai_score
        adjustments = []
        
        # RULE 1: Daily Drawdown Protection (Critical)
        if daily_dd_percent >= 90:
            # Near daily drawdown limit - BLOCK SIGNAL
            adjusted_score = 0
            adjustments.append({
                'rule': 'Daily Drawdown Critical',
                'impact': -ai_score,
                'reason': f'Daily DD at {daily_dd_percent:.1f}% - TRADING BLOCKED',
                'severity': 'critical'
            })
            prop_breakdown['risk_status'] = '🔴 CRITICAL - Daily limit almost reached'
            
        elif daily_dd_percent >= 80:
            # High risk zone - Reduce score by 50%
            reduction = ai_score * 0.5
            adjusted_score = max(0, ai_score - reduction)
            adjustments.append({
                'rule': 'Daily Drawdown High Risk',
                'impact': -reduction,
                'reason': f'Daily DD at {daily_dd_percent:.1f}% - Risk reduced 50%',
                'severity': 'high'
            })
            prop_breakdown['risk_status'] = '🟠 HIGH RISK - Reduce position sizes'
            
        elif daily_dd_percent >= 60:
            # Elevated risk - Reduce score by 25%
            reduction = ai_score * 0.25
            adjusted_score = max(0, ai_score - reduction)
            adjustments.append({
                'rule': 'Daily Drawdown Elevated',
                'impact': -reduction,
                'reason': f'Daily DD at {daily_dd_percent:.1f}% - Risk reduced 25%',
                'severity': 'medium'
            })
            prop_breakdown['risk_status'] = '🟡 ELEVATED - Trade carefully'
        else:
            prop_breakdown['risk_status'] = '🟢 SAFE - Daily drawdown healthy'
        
        # RULE 2: Total Drawdown Protection (Critical)
        if total_dd_percent >= 90:
            # Near total drawdown limit - BLOCK SIGNAL
            adjusted_score = 0
            adjustments.append({
                'rule': 'Total Drawdown Critical',
                'impact': -adjusted_score,
                'reason': f'Total DD at {total_dd_percent:.1f}% - TRADING BLOCKED',
                'severity': 'critical'
            })
            prop_breakdown['challenge_status'] = '🔴 CRITICAL - Challenge at risk'
            
        elif total_dd_percent >= 70:
            # Dangerous zone - Reduce score by 40%
            reduction = adjusted_score * 0.4
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Total Drawdown Dangerous',
                'impact': -reduction,
                'reason': f'Total DD at {total_dd_percent:.1f}% - Protect account',
                'severity': 'high'
            })
            prop_breakdown['challenge_status'] = '🟠 DANGER - Preserve capital'
        else:
            prop_breakdown['challenge_status'] = '🟢 SAFE - Challenge on track'
        
        # RULE 3: Profit Target Protection (Conservative when near target)
        if profit_progress >= 95:
            # Almost at target - Be extremely conservative
            reduction = adjusted_score * 0.6
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Profit Target Near Complete',
                'impact': -reduction,
                'reason': f'At {profit_progress:.1f}% of target - Protect profits',
                'severity': 'medium'
            })
            prop_breakdown['profit_status'] = '🎯 PROTECT - Target almost reached'
            
        elif profit_progress >= 80:
            # Close to target - Reduce risk
            reduction = adjusted_score * 0.3
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Profit Target Close',
                'impact': -reduction,
                'reason': f'At {profit_progress:.1f}% of target - Reduce risk',
                'severity': 'low'
            })
            prop_breakdown['profit_status'] = '🎯 CLOSE - Near target'
        elif profit_progress < 0:
            # In drawdown - Be more selective
            reduction = abs(profit_progress) * 0.2  # Scale with loss size
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Account in Drawdown',
                'impact': -reduction,
                'reason': f'Down {abs(profit_progress):.1f}% - Recovery mode',
                'severity': 'medium'
            })
            prop_breakdown['profit_status'] = '📉 RECOVERY - Be selective'
        else:
            prop_breakdown['profit_status'] = '📈 BUILDING - Keep trading'
        
        # RULE 4: Violation History
        if active_challenge.violation_count >= 3:
            # Multiple violations - Very cautious
            reduction = adjusted_score * 0.5
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Multiple Violations',
                'impact': -reduction,
                'reason': f'{active_challenge.violation_count} violations - Extra caution',
                'severity': 'high'
            })
            prop_breakdown['discipline_status'] = '⚠️ POOR - Improve discipline'
            
        elif active_challenge.violation_count >= 1:
            # Some violations - Cautious
            reduction = adjusted_score * 0.2
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Violation History',
                'impact': -reduction,
                'reason': f'{active_challenge.violation_count} violations - Stay disciplined',
                'severity': 'medium'
            })
            prop_breakdown['discipline_status'] = '🟡 AVERAGE - Watch rules'
        else:
            prop_breakdown['discipline_status'] = '✅ EXCELLENT - No violations'
        
        # RULE 5: Low Confidence Signals (Prop mode requires higher confidence)
        if ai_score < 70:
            # Low confidence in prop mode - Reduce further
            reduction = 15
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Low Confidence Filter',
                'impact': -reduction,
                'reason': 'Prop mode requires high-confidence signals only',
                'severity': 'medium'
            })
        
        # RULE 6: Time Pressure (Nearing deadline but behind target)
        days_remaining = active_challenge.days_remaining
        if days_remaining <= 5 and profit_progress < 80:
            # Time running out and behind - Allow more risk
            boost = 10
            adjusted_score = min(100, adjusted_score + boost)
            adjustments.append({
                'rule': 'Time Pressure',
                'impact': boost,
                'reason': f'Only {days_remaining} days left - Need to catch up',
                'severity': 'low'
            })
            prop_breakdown['time_status'] = '⏰ URGENT - Time running out'
        elif days_remaining >= 20:
            prop_breakdown['time_status'] = '⏳ PLENTY - Take your time'
        else:
            prop_breakdown['time_status'] = '⏳ MODERATE - Stay focused'
        
        # RULE 7: Win Rate Consideration
        win_rate = active_challenge.win_rate
        if win_rate >= 60:
            # Good win rate - Slight confidence boost
            boost = 5
            adjusted_score = min(100, adjusted_score + boost)
            adjustments.append({
                'rule': 'Good Win Rate',
                'impact': boost,
                'reason': f'Win rate {win_rate:.1f}% - Trading well',
                'severity': 'low'
            })
        elif win_rate < 40 and active_challenge.total_trades >= 10:
            # Poor win rate - Extra caution
            reduction = 10
            adjusted_score = max(0, adjusted_score - reduction)
            adjustments.append({
                'rule': 'Low Win Rate',
                'impact': -reduction,
                'reason': f'Win rate {win_rate:.1f}% - Review strategy',
                'severity': 'medium'
            })
        
        # Generate recommendations
        recommendations = generate_prop_recommendations(
            active_challenge,
            daily_dd_percent,
            total_dd_percent,
            profit_progress,
            adjusted_score
        )
        
        # Finalize breakdown
        prop_breakdown['adjustments_applied'] = adjustments
        prop_breakdown['base_score'] = ai_score
        prop_breakdown['final_score'] = int(adjusted_score)
        prop_breakdown['total_adjustment'] = int(adjusted_score - ai_score)
        prop_breakdown['recommendations'] = recommendations
        
        # Overall verdict
        if adjusted_score == 0:
            prop_breakdown['verdict'] = '🔴 BLOCKED - Do not take this trade'
        elif adjusted_score < 40:
            prop_breakdown['verdict'] = '🔴 SKIP - Too risky for prop challenge'
        elif adjusted_score < 60:
            prop_breakdown['verdict'] = '🟡 CAUTION - Only if confident'
        elif adjusted_score < 80:
            prop_breakdown['verdict'] = '🟢 ACCEPTABLE - Proceed with care'
        else:
            prop_breakdown['verdict'] = '🟢 GOOD - Strong signal in prop mode'
        
        logger.info(f"Prop mode applied for user {signal_object.user.username}: {ai_score} → {adjusted_score}")
        
        return int(adjusted_score), prop_breakdown
        
    except Exception as e:
        logger.error(f"Prop mode application failed: {e}", exc_info=True)
        prop_breakdown['error'] = str(e)
        return ai_score, prop_breakdown


def generate_prop_recommendations(
    challenge,
    daily_dd_percent: float,
    total_dd_percent: float,
    profit_progress: float,
    adjusted_score: int
) -> list:
    """
    Generate actionable recommendations based on challenge state.
    """
    recommendations = []
    
    # Daily drawdown recommendations
    if daily_dd_percent >= 80:
        recommendations.append({
            'priority': 'critical',
            'message': 'Stop trading for today - daily drawdown near limit',
            'action': 'Wait until tomorrow for drawdown reset'
        })
    elif daily_dd_percent >= 60:
        recommendations.append({
            'priority': 'high',
            'message': 'Use minimum position sizes (0.5% or less)',
            'action': 'Protect against daily drawdown breach'
        })
    
    # Total drawdown recommendations
    if total_dd_percent >= 70:
        recommendations.append({
            'priority': 'critical',
            'message': 'Account in danger - only take highest confidence signals (80+)',
            'action': 'Focus on capital preservation'
        })
    elif total_dd_percent >= 50:
        recommendations.append({
            'priority': 'high',
            'message': 'Reduce position sizes by 50%',
            'action': 'Rebuild with small wins'
        })
    
    # Profit recommendations
    if profit_progress >= 95:
        recommendations.append({
            'priority': 'medium',
            'message': 'Target almost reached - consider stopping new trades',
            'action': 'Let existing trades close and meet minimum trading days'
        })
    elif profit_progress < -5:
        recommendations.append({
            'priority': 'medium',
            'message': 'In drawdown - review your strategy and journal',
            'action': 'Take a break and analyze what went wrong'
        })
    
    # Violation recommendations
    if challenge.violation_count >= 2:
        recommendations.append({
            'priority': 'high',
            'message': f'{challenge.violation_count} rule violations detected',
            'action': 'Review propcoach rules and avoid further violations'
        })
    
    # Time recommendations
    if challenge.days_remaining <= 5 and profit_progress < 50:
        recommendations.append({
            'priority': 'high',
            'message': 'Time running out and far from target',
            'action': 'Consider pausing this challenge and starting fresh'
        })
    elif challenge.days_remaining >= 20 and profit_progress < 30:
        recommendations.append({
            'priority': 'low',
            'message': 'Plenty of time remaining - be patient',
            'action': 'Focus on quality over quantity'
        })
    
    # Win rate recommendations
    win_rate = challenge.win_rate
    if win_rate < 40 and challenge.total_trades >= 10:
        recommendations.append({
            'priority': 'high',
            'message': f'Low win rate ({win_rate:.1f}%) indicates strategy issues',
            'action': 'Review trade journal and adjust approach'
        })
    
    # Signal score recommendations
    if adjusted_score < 50:
        recommendations.append({
            'priority': 'medium',
            'message': 'This signal scored low in prop mode',
            'action': 'Wait for higher confidence opportunities'
        })
    
    return recommendations


def get_prop_challenge_summary(user) -> Optional[Dict]:
    """
    Get a summary of user's active prop challenge.
    
    Args:
        user: User object
        
    Returns:
        Dict with challenge summary or None if no active challenge
    """
    from propcoach.models import PropChallenge
    
    try:
        active_challenge = PropChallenge.objects.filter(
            user=user,
            status='active'
        ).select_related('template').first()
        
        if not active_challenge:
            return None
        
        template = active_challenge.template
        
        return {
            'challenge_id': str(active_challenge.id),
            'firm_name': template.get_firm_name_display(),
            'phase': template.get_phase_display(),
            'account_size': float(template.account_size),
            'current_balance': float(active_challenge.current_balance),
            'profit_loss': float(active_challenge.total_profit_loss),
            'profit_target': float(template.get_profit_target_amount()),
            'profit_progress_percent': active_challenge.profit_progress_percent,
            'daily_drawdown_percent': (
                active_challenge.current_daily_drawdown / 
                template.get_max_daily_loss() * 100
                if template.get_max_daily_loss() > 0 else 0
            ),
            'total_drawdown_percent': (
                active_challenge.current_total_drawdown / 
                template.get_max_total_loss() * 100
                if template.get_max_total_loss() > 0 else 0
            ),
            'violation_count': active_challenge.violation_count,
            'days_elapsed': active_challenge.days_elapsed,
            'days_remaining': active_challenge.days_remaining,
            'total_trades': active_challenge.total_trades,
            'win_rate': active_challenge.win_rate,
            'funding_readiness_score': float(active_challenge.funding_readiness_score),
            'is_passing': active_challenge.is_passing,
        }
        
    except Exception as e:
        logger.error(f"Failed to get prop challenge summary: {e}", exc_info=True)
        return None


def check_trade_allowed(user, symbol: str, proposed_risk_percent: float = 1.0) -> Tuple[bool, str]:
    """
    Check if a trade is allowed under current prop challenge constraints.
    
    Args:
        user: User object
        symbol: Trading symbol
        proposed_risk_percent: Proposed risk as % of account
        
    Returns:
        Tuple of (is_allowed, reason_message)
    """
    from propcoach.models import PropChallenge
    
    try:
        active_challenge = PropChallenge.objects.filter(
            user=user,
            status='active'
        ).select_related('template').first()
        
        if not active_challenge:
            return True, "No active prop challenge"
        
        template = active_challenge.template
        
        # Check 1: Daily drawdown
        max_daily_loss = template.get_max_daily_loss()
        remaining_daily = max_daily_loss - active_challenge.current_daily_drawdown
        daily_dd_percent = (active_challenge.current_daily_drawdown / max_daily_loss * 100) if max_daily_loss > 0 else 0
        
        if daily_dd_percent >= 95:
            return False, "Daily drawdown limit reached - trading blocked for today"
        
        # Check 2: Total drawdown
        max_total_loss = template.get_max_total_loss()
        remaining_total = max_total_loss - active_challenge.current_total_drawdown
        total_dd_percent = (active_challenge.current_total_drawdown / max_total_loss * 100) if max_total_loss > 0 else 0
        
        if total_dd_percent >= 95:
            return False, "Total drawdown limit reached - challenge failed"
        
        # Check 3: Position size
        if proposed_risk_percent > float(template.max_position_size_percent):
            return False, f"Position size {proposed_risk_percent}% exceeds limit of {template.max_position_size_percent}%"
        
        # Check 4: Can afford the risk
        proposed_risk_amount = active_challenge.current_balance * Decimal(str(proposed_risk_percent)) / 100
        if proposed_risk_amount > remaining_daily:
            return False, f"Proposed risk ${proposed_risk_amount:.2f} exceeds remaining daily allowance ${remaining_daily:.2f}"
        
        # All checks passed
        return True, "Trade allowed"
        
    except Exception as e:
        logger.error(f"Trade check failed: {e}", exc_info=True)
        return True, f"Trade check error: {str(e)}"
