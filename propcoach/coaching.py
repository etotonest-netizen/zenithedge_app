"""
AI Coaching Engine for PropCoach

Generates personalized coaching feedback by combining:
- Performance metrics from PropChallenge
- Psychology data from Cognition module
- Violation history
- Trading patterns
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def generate_daily_feedback(challenge) -> Optional[Dict]:
    """
    Generate comprehensive daily feedback for a prop challenge.
    
    Args:
        challenge: PropChallenge instance
        
    Returns:
        Dict with coaching feedback data or None on error
    """
    from propcoach.models import CoachingFeedback, TradeRecord, PropRuleViolation
    from cognition.models import TraderPsychology
    
    try:
        user = challenge.user
        template = challenge.template
        
        # Get today's trades
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = TradeRecord.objects.filter(
            challenge=challenge,
            entry_time__gte=today_start
        )
        
        # Get recent psychology data (last 24 hours)
        recent_psych = TraderPsychology.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-timestamp').first()
        
        # Get recent violations (last 24 hours)
        recent_violations = PropRuleViolation.objects.filter(
            challenge=challenge,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )
        
        # Analyze performance
        performance_analysis = analyze_performance(challenge, today_trades)
        
        # Analyze psychology
        psychology_analysis = analyze_psychology(recent_psych, challenge) if recent_psych else None
        
        # Analyze violations
        violation_analysis = analyze_violations(recent_violations, challenge)
        
        # Generate insights
        insights = generate_insights(
            challenge,
            performance_analysis,
            psychology_analysis,
            violation_analysis
        )
        
        # Create coaching feedback entries
        feedback_entries = []
        for insight in insights:
            feedback = CoachingFeedback.objects.create(
                challenge=challenge,
                user=user,
                feedback_type=insight['type'],
                title=insight['title'],
                message=insight['message'],
                metrics_data=insight.get('metrics', {}),
                emotional_tone=insight.get('emotional_tone', ''),
                detected_biases=insight.get('biases', []),
                discipline_score=insight.get('discipline_score'),
                recommendations=insight.get('recommendations', []),
                priority=insight.get('priority', 5),
                is_actionable=insight.get('is_actionable', False)
            )
            feedback_entries.append(feedback)
        
        return {
            'feedback_count': len(feedback_entries),
            'insights': insights,
            'performance': performance_analysis,
            'psychology': psychology_analysis,
            'violations': violation_analysis
        }
        
    except Exception as e:
        logger.error(f"Failed to generate daily feedback: {e}", exc_info=True)
        return None


def analyze_performance(challenge, today_trades) -> Dict:
    """Analyze trading performance metrics."""
    template = challenge.template
    
    analysis = {
        'trades_today': today_trades.count(),
        'current_balance': float(challenge.current_balance),
        'profit_loss': float(challenge.total_profit_loss),
        'profit_target': float(template.get_profit_target_amount()),
        'profit_progress_percent': challenge.profit_progress_percent,
        'win_rate': challenge.win_rate,
        'total_trades': challenge.total_trades,
        'daily_drawdown_percent': (
            challenge.current_daily_drawdown / template.get_max_daily_loss() * 100
            if template.get_max_daily_loss() > 0 else 0
        ),
        'total_drawdown_percent': (
            challenge.current_total_drawdown / template.get_max_total_loss() * 100
            if template.get_max_total_loss() > 0 else 0
        ),
        'days_remaining': challenge.days_remaining,
        'funding_readiness': float(challenge.funding_readiness_score)
    }
    
    # Calculate today's P/L
    today_pnl = sum(trade.profit_loss for trade in today_trades.filter(status='closed'))
    analysis['today_pnl'] = float(today_pnl)
    
    # Calculate today's win rate
    today_closed = today_trades.filter(status='closed')
    if today_closed.count() > 0:
        today_wins = today_closed.filter(profit_loss__gt=0).count()
        analysis['today_win_rate'] = (today_wins / today_closed.count()) * 100
    else:
        analysis['today_win_rate'] = 0
    
    # Performance trends
    if challenge.win_rate >= 60:
        analysis['performance_level'] = 'excellent'
    elif challenge.win_rate >= 50:
        analysis['performance_level'] = 'good'
    elif challenge.win_rate >= 40:
        analysis['performance_level'] = 'average'
    else:
        analysis['performance_level'] = 'poor'
    
    return analysis


def analyze_psychology(psych_entry, challenge) -> Dict:
    """Analyze psychological state from cognition data."""
    analysis = {
        'sentiment': round(psych_entry.sentiment_score, 3),
        'discipline': round(psych_entry.discipline_score, 2),
        'emotional_tone': psych_entry.emotional_tone,
        'biases': psych_entry.detected_biases,
        'confidence': round(psych_entry.confidence_level, 2)
    }
    
    # Calculate psychological risk level
    bias_count = len(psych_entry.detected_biases)
    
    if psych_entry.discipline_score >= 80 and bias_count == 0:
        analysis['psych_status'] = 'excellent'
        analysis['risk_level'] = 'low'
    elif psych_entry.discipline_score >= 60 and bias_count <= 1:
        analysis['psych_status'] = 'good'
        analysis['risk_level'] = 'low'
    elif psych_entry.discipline_score >= 40 or bias_count <= 2:
        analysis['psych_status'] = 'average'
        analysis['risk_level'] = 'medium'
    else:
        analysis['psych_status'] = 'poor'
        analysis['risk_level'] = 'high'
    
    # Emotional warnings
    dangerous_emotions = ['greedy', 'fearful', 'overconfident', 'vengeful', 'impulsive']
    if psych_entry.emotional_tone in dangerous_emotions:
        analysis['emotional_warning'] = True
    else:
        analysis['emotional_warning'] = False
    
    return analysis


def analyze_violations(violations, challenge) -> Dict:
    """Analyze rule violations."""
    analysis = {
        'violation_count': violations.count(),
        'total_violations': challenge.violation_count,
        'violation_types': {},
        'critical_violations': 0,
        'major_violations': 0,
        'minor_violations': 0
    }
    
    for violation in violations:
        # Count by type
        vtype = violation.violation_type
        analysis['violation_types'][vtype] = analysis['violation_types'].get(vtype, 0) + 1
        
        # Count by severity
        if violation.severity == 'critical':
            analysis['critical_violations'] += 1
        elif violation.severity == 'major':
            analysis['major_violations'] += 1
        elif violation.severity == 'minor':
            analysis['minor_violations'] += 1
    
    # Violation risk assessment
    if analysis['critical_violations'] > 0:
        analysis['violation_status'] = 'critical'
    elif analysis['major_violations'] >= 2:
        analysis['violation_status'] = 'high_risk'
    elif analysis['minor_violations'] >= 3:
        analysis['violation_status'] = 'moderate_risk'
    else:
        analysis['violation_status'] = 'low_risk'
    
    return analysis


def generate_insights(challenge, performance, psychology, violations) -> List[Dict]:
    """
    Generate actionable coaching insights.
    
    Returns list of insight dicts with coaching messages.
    """
    insights = []
    
    # INSIGHT 1: Daily Summary
    insights.append(generate_daily_summary(challenge, performance, psychology, violations))
    
    # INSIGHT 2: Performance Alerts (if needed)
    perf_alert = generate_performance_alert(challenge, performance)
    if perf_alert:
        insights.append(perf_alert)
    
    # INSIGHT 3: Behavioral Insights (from psychology)
    if psychology:
        behavior_insight = generate_behavioral_insight(psychology, performance)
        if behavior_insight:
            insights.append(behavior_insight)
    
    # INSIGHT 4: Risk Warnings (from violations and drawdown)
    risk_warning = generate_risk_warning(challenge, violations, performance)
    if risk_warning:
        insights.append(risk_warning)
    
    # INSIGHT 5: Achievements (if applicable)
    achievement = generate_achievement(challenge, performance)
    if achievement:
        insights.append(achievement)
    
    # INSIGHT 6: Strategy Suggestions
    strategy_suggestion = generate_strategy_suggestion(challenge, performance, psychology)
    if strategy_suggestion:
        insights.append(strategy_suggestion)
    
    return insights


def generate_daily_summary(challenge, performance, psychology, violations) -> Dict:
    """Generate daily summary insight."""
    template = challenge.template
    
    # Build summary message
    message = f"**Daily Summary - {timezone.now().strftime('%B %d, %Y')}**\n\n"
    
    # Performance summary
    message += f"**Performance:**\n"
    message += f"• Trades Today: {performance['trades_today']}\n"
    if performance['trades_today'] > 0:
        message += f"• Today's P/L: ${performance['today_pnl']:.2f}\n"
        message += f"• Today's Win Rate: {performance['today_win_rate']:.1f}%\n"
    message += f"• Challenge Progress: {performance['profit_progress_percent']:.1f}% of target\n"
    message += f"• Overall Win Rate: {performance['win_rate']:.1f}%\n"
    message += f"• Days Remaining: {performance['days_remaining']}\n\n"
    
    # Risk summary
    message += f"**Risk Status:**\n"
    message += f"• Daily Drawdown: {performance['daily_drawdown_percent']:.1f}% used\n"
    message += f"• Total Drawdown: {performance['total_drawdown_percent']:.1f}% used\n"
    
    if violations['violation_count'] > 0:
        message += f"• ⚠️ {violations['violation_count']} violations today\n"
    else:
        message += f"• ✅ No violations today\n"
    
    # Psychology summary
    if psychology:
        message += f"\n**Mental State:**\n"
        message += f"• Emotional Tone: {psychology['emotional_tone'].title()}\n"
        message += f"• Discipline Score: {psychology['discipline']}/100\n"
        if len(psychology['biases']) > 0:
            message += f"• ⚠️ Detected Biases: {', '.join(psychology['biases'])}\n"
    
    # Funding readiness
    message += f"\n**Funding Readiness: {performance['funding_readiness']:.0f}/100**\n"
    
    return {
        'type': 'daily_summary',
        'title': 'Daily Challenge Summary',
        'message': message,
        'metrics': performance,
        'emotional_tone': psychology['emotional_tone'] if psychology else '',
        'biases': psychology['biases'] if psychology else [],
        'discipline_score': Decimal(str(psychology['discipline'])) if psychology else None,
        'recommendations': [],
        'priority': 5,
        'is_actionable': False
    }


def generate_performance_alert(challenge, performance) -> Optional[Dict]:
    """Generate performance alert if needed."""
    alerts = []
    
    # Low win rate alert
    if performance['total_trades'] >= 10 and performance['win_rate'] < 40:
        alerts.append({
            'type': 'performance_alert',
            'title': '⚠️ Low Win Rate Alert',
            'message': (
                f"Your win rate is {performance['win_rate']:.1f}%, which is below the "
                f"recommended 50% for prop challenges.\n\n"
                f"**Recommendations:**\n"
                f"• Review your trade journal to identify patterns\n"
                f"• Consider reducing position sizes\n"
                f"• Only take high-confidence signals (AI score 70+)\n"
                f"• Take a break and reassess your strategy"
            ),
            'recommendations': [
                'Review trade journal',
                'Reduce position sizes',
                'Filter for high-confidence signals',
                'Take a trading break'
            ],
            'priority': 8,
            'is_actionable': True
        })
    
    # Behind target with low time
    if performance['days_remaining'] <= 7 and performance['profit_progress_percent'] < 50:
        alerts.append({
            'type': 'performance_alert',
            'title': '⏰ Time Running Out',
            'message': (
                f"Only {performance['days_remaining']} days left and you're at "
                f"{performance['profit_progress_percent']:.1f}% of target.\n\n"
                f"**Options:**\n"
                f"• Continue trading with slightly higher risk\n"
                f"• Consider restarting a fresh challenge\n"
                f"• Focus on quality over quantity"
            ),
            'recommendations': [
                'Evaluate if target is reachable',
                'Consider fresh challenge',
                'Maintain discipline despite pressure'
            ],
            'priority': 9,
            'is_actionable': True
        })
    
    # Near target
    if performance['profit_progress_percent'] >= 90:
        alerts.append({
            'type': 'performance_alert',
            'title': '🎯 Target Almost Reached!',
            'message': (
                f"Excellent progress! You're at {performance['profit_progress_percent']:.1f}% "
                f"of your profit target.\n\n"
                f"**Next Steps:**\n"
                f"• Reduce position sizes to protect gains\n"
                f"• Ensure minimum trading days requirement is met\n"
                f"• Avoid taking unnecessary risks"
            ),
            'recommendations': [
                'Reduce risk significantly',
                'Verify minimum trading days',
                'Protect your gains'
            ],
            'priority': 7,
            'is_actionable': True
        })
    
    return alerts[0] if alerts else None


def generate_behavioral_insight(psychology, performance) -> Optional[Dict]:
    """Generate behavioral insight from psychology data."""
    # Check for emotional warnings
    if psychology['emotional_warning']:
        message = (
            f"**Emotional State Warning**\n\n"
            f"Your emotional tone is '{psychology['emotional_tone']}', which can "
            f"lead to impulsive decisions.\n\n"
        )
        
        if psychology['emotional_tone'] == 'greedy':
            message += (
                "**Greed Warning:**\n"
                "• Don't overtrade trying to reach target quickly\n"
                "• Stick to your position sizing rules\n"
                "• Remember: slow and steady wins the race"
            )
        elif psychology['emotional_tone'] == 'fearful':
            message += (
                "**Fear Warning:**\n"
                "• Don't let losses paralyze you\n"
                "• Trust your tested strategy\n"
                "• Consider smaller position sizes to build confidence"
            )
        elif psychology['emotional_tone'] == 'overconfident':
            message += (
                "**Overconfidence Warning:**\n"
                "• Recent wins can cloud judgment\n"
                "• Don't increase risk beyond your rules\n"
                "• Every trade still requires full analysis"
            )
        
        return {
            'type': 'behavioral_insight',
            'title': f'Psychology Alert: {psychology["emotional_tone"].title()}',
            'message': message,
            'emotional_tone': psychology['emotional_tone'],
            'biases': psychology['biases'],
            'discipline_score': Decimal(str(psychology['discipline'])),
            'recommendations': [
                'Take a 30-minute break',
                'Review your trading plan',
                'Journal your current emotions'
            ],
            'priority': 8,
            'is_actionable': True
        }
    
    # Check for multiple biases
    if len(psychology['biases']) >= 2:
        return {
            'type': 'behavioral_insight',
            'title': '🧠 Multiple Cognitive Biases Detected',
            'message': (
                f"**Detected Biases:** {', '.join(psychology['biases'])}\n\n"
                f"These biases can affect your trading decisions. "
                f"Awareness is the first step to overcoming them.\n\n"
                f"**Recommended Actions:**\n"
                f"• Write down your reasoning before each trade\n"
                f"• Use a pre-trade checklist\n"
                f"• Take breaks between trades"
            ),
            'emotional_tone': psychology['emotional_tone'],
            'biases': psychology['biases'],
            'discipline_score': Decimal(str(psychology['discipline'])),
            'recommendations': [
                'Use pre-trade checklist',
                'Journal trade reasoning',
                'Take breaks between trades'
            ],
            'priority': 7,
            'is_actionable': True
        }
    
    return None


def generate_risk_warning(challenge, violations, performance) -> Optional[Dict]:
    """Generate risk warning if needed."""
    warnings = []
    
    # Critical violation warning
    if violations['critical_violations'] > 0:
        warnings.append({
            'type': 'risk_warning',
            'title': '🚨 Critical Rule Violation',
            'message': (
                f"You have {violations['critical_violations']} critical violations!\n\n"
                f"Critical violations can immediately fail your challenge. "
                f"Review the PropCoach rules immediately.\n\n"
                f"**Violation Types:**\n" +
                '\n'.join([f"• {vtype}: {count}x" for vtype, count in violations['violation_types'].items()])
            ),
            'recommendations': [
                'Review all PropCoach rules',
                'Pause trading for 24 hours',
                'Analyze what went wrong'
            ],
            'priority': 10,
            'is_actionable': True
        })
    
    # High drawdown warning
    if performance['daily_drawdown_percent'] >= 70:
        warnings.append({
            'type': 'risk_warning',
            'title': '🔴 High Daily Drawdown',
            'message': (
                f"Your daily drawdown is at {performance['daily_drawdown_percent']:.1f}%!\n\n"
                f"**IMMEDIATE ACTIONS:**\n"
                f"• Stop trading for today\n"
                f"• Daily drawdown resets tomorrow\n"
                f"• Review what caused the losses"
            ),
            'recommendations': [
                'STOP TRADING TODAY',
                'Wait for drawdown reset',
                'Analyze losing trades'
            ],
            'priority': 10,
            'is_actionable': True
        })
    
    if performance['total_drawdown_percent'] >= 70:
        warnings.append({
            'type': 'risk_warning',
            'title': '🔴 Dangerous Total Drawdown',
            'message': (
                f"Your total drawdown is at {performance['total_drawdown_percent']:.1f}%!\n\n"
                f"Your challenge is at serious risk. Consider:\n"
                f"• Taking a 48-hour break\n"
                f"• Using minimum position sizes (0.5% max)\n"
                f"• Only taking 80+ AI score signals\n"
                f"• Or restarting with a fresh challenge"
            ),
            'recommendations': [
                'Take 48-hour break',
                'Use 0.5% max position size',
                'Filter for 80+ AI scores',
                'Consider restarting challenge'
            ],
            'priority': 10,
            'is_actionable': True
        })
    
    return warnings[0] if warnings else None


def generate_achievement(challenge, performance) -> Optional[Dict]:
    """Generate achievement notification if applicable."""
    achievements = []
    
    # First profitable day
    if performance['trades_today'] > 0 and performance['today_pnl'] > 0:
        if challenge.winning_trades == performance['trades_today']:  # All today's trades are first wins
            achievements.append({
                'type': 'achievement',
                'title': '🎉 First Profitable Day!',
                'message': (
                    f"Congratulations! You made ${performance['today_pnl']:.2f} today.\n\n"
                    f"Keep up the good work and maintain your discipline!"
                ),
                'priority': 3
            })
    
    # 50% profit target reached
    if 48 <= performance['profit_progress_percent'] < 52:
        achievements.append({
            'type': 'achievement',
            'title': '🎯 Halfway to Target!',
            'message': (
                f"You've reached {performance['profit_progress_percent']:.1f}% of your profit target!\n\n"
                f"Stay focused and maintain your risk management."
            ),
            'priority': 4
        })
    
    # No violations milestone
    if challenge.total_trades >= 20 and challenge.violation_count == 0:
        achievements.append({
            'type': 'achievement',
            'title': '✅ Perfect Discipline!',
            'message': (
                f"Amazing! {challenge.total_trades} trades with ZERO violations.\n\n"
                f"This is exactly the discipline prop firms look for!"
            ),
            'priority': 4
        })
    
    # High win rate
    if challenge.total_trades >= 20 and performance['win_rate'] >= 65:
        achievements.append({
            'type': 'achievement',
            'title': '🔥 Excellent Win Rate!',
            'message': (
                f"Your win rate of {performance['win_rate']:.1f}% is outstanding!\n\n"
                f"You're trading at a professional level."
            ),
            'priority': 4
        })
    
    return achievements[0] if achievements else None


def generate_strategy_suggestion(challenge, performance, psychology) -> Optional[Dict]:
    """Generate strategy suggestion based on patterns."""
    suggestions = []
    
    # Suggest break after losses
    if performance['trades_today'] >= 3:
        recent_trades = TradeRecord.objects.filter(
            challenge=challenge
        ).order_by('-entry_time')[:3]
        
        losses = sum(1 for t in recent_trades if t.profit_loss < 0)
        if losses >= 2:
            suggestions.append({
                'type': 'strategy_suggestion',
                'title': '💡 Take a Break',
                'message': (
                    f"You've had {losses} losses in your last 3 trades.\n\n"
                    f"**Suggestion:**\n"
                    f"• Take a 1-2 hour break\n"
                    f"• Clear your mind\n"
                    f"• Return with fresh perspective\n"
                    f"• Review what went wrong"
                ),
                'recommendations': [
                    'Take 1-2 hour break',
                    'Analyze recent losses',
                    'Refresh your mind'
                ],
                'priority': 6,
                'is_actionable': True
            })
    
    # Suggest position size adjustment
    if psychology and psychology['discipline'] < 60:
        suggestions.append({
            'type': 'strategy_suggestion',
            'title': '💡 Reduce Position Sizes',
            'message': (
                f"Your discipline score is {psychology['discipline']}/100.\n\n"
                f"Lower discipline often leads to mistakes. Consider:\n"
                f"• Reducing position sizes by 50%\n"
                f"• Trading less frequently\n"
                f"• Building confidence with smaller wins"
            ),
            'recommendations': [
                'Reduce position sizes 50%',
                'Trade less frequently',
                'Focus on high-probability setups'
            ],
            'priority': 6,
            'is_actionable': True
        })
    
    return suggestions[0] if suggestions else None


from propcoach.models import TradeRecord
