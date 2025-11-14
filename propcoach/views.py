from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal
from datetime import timedelta
import json

from .models import (
    PropChallenge, FirmTemplate, TradeRecord, 
    PropRuleViolation, CoachingFeedback, PropTrainingSession
)
from .coaching import generate_daily_feedback
from .prop_mode import get_prop_challenge_summary


@login_required
def dashboard(request):
    """Main PropCoach dashboard view."""
    # Get user's active challenge
    active_challenge = PropChallenge.objects.filter(
        user=request.user,
        status='active'
    ).select_related('template').first()
    
    # Get completed challenges
    completed_challenges = PropChallenge.objects.filter(
        user=request.user,
        status__in=['passed', 'failed']
    ).select_related('template').order_by('-completion_date')[:5]
    
    # Get recent coaching feedback
    recent_feedback = CoachingFeedback.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]
    
    # Get unread feedback count
    unread_count = CoachingFeedback.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Get overall statistics
    all_challenges = PropChallenge.objects.filter(user=request.user)
    stats = {
        'total_challenges': all_challenges.count(),
        'passed_challenges': all_challenges.filter(status='passed').count(),
        'failed_challenges': all_challenges.filter(status='failed').count(),
        'active_challenges': all_challenges.filter(status='active').count(),
    }
    
    if stats['total_challenges'] > 0:
        stats['pass_rate'] = (stats['passed_challenges'] / stats['total_challenges']) * 100
    else:
        stats['pass_rate'] = 0
    
    # Calculate thresholds for active challenge (for gauges)
    drawdown_thresholds = {}
    if active_challenge:
        max_daily = abs(active_challenge.template.get_max_daily_loss())
        max_total = abs(active_challenge.template.get_max_total_loss())
        drawdown_thresholds = {
            'daily_80': float(max_daily * Decimal('0.8')),
            'daily_60': float(max_daily * Decimal('0.6')),
            'total_80': float(max_total * Decimal('0.8')),
            'total_60': float(max_total * Decimal('0.6')),
        }
    
    context = {
        'active_challenge': active_challenge,
        'completed_challenges': completed_challenges,
        'recent_feedback': recent_feedback,
        'unread_count': unread_count,
        'stats': stats,
        'drawdown_thresholds': drawdown_thresholds,
    }
    
    return render(request, 'propcoach/dashboard.html', context)


@login_required
def challenge_detail(request, challenge_id):
    """Detailed view of a specific challenge."""
    challenge = get_object_or_404(
        PropChallenge.objects.select_related('template'),
        id=challenge_id,
        user=request.user
    )
    
    # Get trades
    trades = TradeRecord.objects.filter(
        challenge=challenge
    ).order_by('-entry_time')
    
    # Get violations
    violations = PropRuleViolation.objects.filter(
        challenge=challenge
    ).order_by('-timestamp')
    
    # Get coaching feedback
    coaching = CoachingFeedback.objects.filter(
        challenge=challenge
    ).order_by('-timestamp')
    
    # Calculate equity curve data
    equity_data = []
    running_balance = challenge.initial_balance
    
    for trade in trades.filter(status='closed').order_by('entry_time'):
        running_balance += trade.profit_loss
        equity_data.append({
            'date': trade.exit_time.isoformat() if trade.exit_time else '',
            'balance': float(running_balance),
            'pnl': float(trade.profit_loss)
        })
    
    # Get template limits
    template = challenge.template
    max_daily = abs(template.get_max_daily_loss())
    max_total = abs(template.get_max_total_loss())
    
    limits = {
        'max_daily_loss': float(max_daily),
        'max_total_loss': float(max_total),
        'profit_target': float(template.get_profit_target_amount()),
    }
    
    # Calculate thresholds for gauges (convert to Decimal to avoid TypeError)
    thresholds = {
        'daily_80': float(max_daily * Decimal('0.8')),
        'daily_60': float(max_daily * Decimal('0.6')),
        'total_80': float(max_total * Decimal('0.8')),
        'total_60': float(max_total * Decimal('0.6')),
    }
    
    context = {
        'challenge': challenge,
        'trades': trades,
        'violations': violations,
        'coaching': coaching,
        'equity_data': json.dumps(equity_data),
        'limits': limits,
        'thresholds': thresholds,
    }
    
    return render(request, 'propcoach/challenge_detail.html', context)


@login_required
def start_challenge(request):
    """Start a new prop challenge."""
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        template = get_object_or_404(FirmTemplate, id=template_id, is_active=True)
        
        # Check if user already has an active challenge
        existing_active = PropChallenge.objects.filter(
            user=request.user,
            status='active'
        ).exists()
        
        if existing_active:
            return JsonResponse({
                'success': False,
                'error': 'You already have an active challenge. Complete or abandon it first.'
            })
        
        # Create new challenge
        challenge = PropChallenge.objects.create(
            user=request.user,
            template=template,
            initial_balance=template.account_size,
            current_balance=template.account_size,
            peak_balance=template.account_size,
            status='active',
            start_date=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'challenge_id': str(challenge.id),
            'redirect_url': f'/propcoach/challenge/{challenge.id}/'
        })
    
    # GET request - show template selection
    templates = FirmTemplate.objects.filter(is_active=True).order_by('firm_name', 'phase')
    
    # Group templates by firm
    firms = {}
    for template in templates:
        firm_name = template.get_firm_name_display()
        if firm_name not in firms:
            firms[firm_name] = []
        firms[firm_name].append(template)
    
    context = {
        'firms': firms,
    }
    
    return render(request, 'propcoach/start_challenge.html', context)


@login_required
def trade_log(request, challenge_id):
    """Detailed trade log for a challenge."""
    challenge = get_object_or_404(
        PropChallenge,
        id=challenge_id,
        user=request.user
    )
    
    trades = TradeRecord.objects.filter(
        challenge=challenge
    ).order_by('-entry_time')
    
    # Calculate statistics
    closed_trades = trades.filter(status='closed')
    winning_trades = closed_trades.filter(profit_loss__gt=0)
    losing_trades = closed_trades.filter(profit_loss__lt=0)
    
    stats = {
        'total_trades': closed_trades.count(),
        'winning_trades': winning_trades.count(),
        'losing_trades': losing_trades.count(),
        'win_rate': (winning_trades.count() / closed_trades.count() * 100) if closed_trades.count() > 0 else 0,
        'total_pnl': closed_trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0,
        'avg_win': winning_trades.aggregate(Avg('profit_loss'))['profit_loss__avg'] or 0,
        'avg_loss': losing_trades.aggregate(Avg('profit_loss'))['profit_loss__avg'] or 0,
        'largest_win': winning_trades.aggregate(Max('profit_loss'))['profit_loss__max'] or 0,
        'largest_loss': losing_trades.aggregate(Min('profit_loss'))['profit_loss__min'] or 0,
    }
    
    if stats['avg_loss'] != 0:
        stats['profit_factor'] = abs(stats['avg_win'] / stats['avg_loss'])
    else:
        stats['profit_factor'] = 0
    
    context = {
        'challenge': challenge,
        'trades': trades,
        'stats': stats,
    }
    
    return render(request, 'propcoach/trade_log.html', context)


@login_required
def coaching_panel(request, challenge_id):
    """View coaching feedback for a challenge."""
    challenge = get_object_or_404(
        PropChallenge,
        id=challenge_id,
        user=request.user
    )
    
    feedback = CoachingFeedback.objects.filter(
        challenge=challenge
    ).order_by('-timestamp')
    
    # Mark as read
    if request.method == 'POST':
        feedback_id = request.POST.get('feedback_id')
        if feedback_id:
            CoachingFeedback.objects.filter(
                id=feedback_id,
                user=request.user
            ).update(is_read=True)
            return JsonResponse({'success': True})
    
    # Generate new feedback if requested
    if request.GET.get('generate'):
        result = generate_daily_feedback(challenge)
        if result:
            return redirect('propcoach:coaching_panel', challenge_id=challenge_id)
    
    context = {
        'challenge': challenge,
        'feedback': feedback,
    }
    
    return render(request, 'propcoach/coaching_panel.html', context)


@login_required
def leaderboard(request):
    """Community leaderboard view."""
    # Get top performers (by pass rate)
    top_users = User.objects.annotate(
        total_challenges=Count('propcoach_challenges'),
        passed_challenges=Count('propcoach_challenges', filter=Q(propcoach_challenges__status='passed')),
    ).filter(total_challenges__gte=3).order_by('-passed_challenges')[:20]
    
    # Calculate pass rates
    leaderboard_data = []
    for user in top_users:
        if user.total_challenges > 0:
            pass_rate = (user.passed_challenges / user.total_challenges) * 100
            leaderboard_data.append({
                'username': user.username,
                'total_challenges': user.total_challenges,
                'passed_challenges': user.passed_challenges,
                'pass_rate': pass_rate,
            })
    
    context = {
        'leaderboard': leaderboard_data,
    }
    
    return render(request, 'propcoach/leaderboard.html', context)


@login_required
def api_challenge_status(request, challenge_id):
    """API endpoint for real-time challenge status."""
    challenge = get_object_or_404(
        PropChallenge,
        id=challenge_id,
        user=request.user
    )
    
    summary = get_prop_challenge_summary(request.user)
    
    return JsonResponse(summary if summary else {'error': 'No active challenge'})


from django.contrib.auth import get_user_model
from django.db.models import Max, Min

User = get_user_model()
