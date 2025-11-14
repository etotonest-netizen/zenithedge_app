"""
Admin Dashboard Views
Centralized control panel for system administration
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from accounts.models import CustomUser
from signals.models import Signal, StrategyPerformance, SessionRule, RiskControl, TradeJournalEntry
from bot.models import BotConversation
try:
    from analytics.models import BacktestResult
except ImportError:
    BacktestResult = None
try:
    from propcoach.models import PropChallenge, FirmTemplate
except ImportError:
    PropChallenge = None
    FirmTemplate = None
try:
    from zenithmentor.models import ApprenticeProfile, Scenario, SimulationRun, SkillBadge
except ImportError:
    ApprenticeProfile = None
    Scenario = None
    SimulationRun = None
    SkillBadge = None
try:
    from zennews.models import NewsArticle, MarketSentiment
except ImportError:
    NewsArticle = None
    MarketSentiment = None
try:
    from support.models import SupportTicket
except ImportError:
    SupportTicket = None


@staff_member_required
def admin_dashboard(request):
    """Main admin control panel."""
    
    # Time ranges
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # ===== USER STATISTICS =====
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(last_login__gte=week_start).count()
    new_users_today = CustomUser.objects.filter(date_joined__gte=today_start).count()
    new_users_week = CustomUser.objects.filter(date_joined__gte=week_start).count()
    staff_users = CustomUser.objects.filter(is_staff=True).count()
    verified_users = CustomUser.objects.filter(is_active=True, email_verified=True).count() if hasattr(CustomUser, 'email_verified') else 0
    
    # ===== SIGNAL STATISTICS =====
    total_signals = Signal.objects.count()
    # Signals marked allowed and not blocked by risk controls
    active_signals = Signal.objects.filter(is_allowed=True, is_risk_blocked=False).count()
    # Use received_at (webhook receipt) as signal timestamp
    signals_today = Signal.objects.filter(received_at__gte=today_start).count()
    # Pending = not allowed yet
    signals_pending = Signal.objects.filter(is_allowed=False).count()
    # Executed/settled signals are those with an outcome
    signals_executed = Signal.objects.filter(outcome__in=['win', 'loss']).count()
    
    # Signal performance
    winning_signals = Signal.objects.filter(outcome='win').count()
    losing_signals = Signal.objects.filter(outcome='loss').count()
    # Total P&L derived from strategy performance summary (if available)
    try:
        total_pnl = StrategyPerformance.objects.aggregate(total=Sum('total_pnl'))['total'] or Decimal('0.00')
    except Exception:
        total_pnl = Decimal('0.00')
    
    win_rate = (winning_signals / (winning_signals + losing_signals) * 100) if (winning_signals + losing_signals) > 0 else 0
    
    # ===== STRATEGY STATISTICS =====
    total_strategies = StrategyPerformance.objects.count()
    active_strategies = StrategyPerformance.objects.filter(total_trades__gt=0).count()
    strategy_performance = StrategyPerformance.objects.values('strategy_name').annotate(
        win_rate=Avg('win_rate'),
        total_trades=Sum('total_trades'),
        total_pnl=Sum('total_pnl')
    ).order_by('-win_rate')[:5]
    
    # ===== SESSION STATISTICS =====
    total_sessions = SessionRule.objects.count()
    # Active sessions = non-blocked sessions
    active_sessions = SessionRule.objects.filter(is_blocked=False).count()
    sessions_today = SessionRule.objects.filter(created_at__gte=today_start).count() if hasattr(SessionRule, 'created_at') else 0
    
    # ===== RISK CONTROL =====
    # Use received_at instead of created_at for Signal model
    risk_blocks_today = Signal.objects.filter(
        is_risk_blocked=True,
        received_at__gte=today_start
    ).count()
    
    active_risk_controls = RiskControl.objects.filter(is_active=True).count()
    
    # ===== ZENITHMENTOR STATISTICS =====
    total_apprentices = ApprenticeProfile.objects.count() if ApprenticeProfile else 0
    total_scenarios = Scenario.objects.count() if Scenario else 0
    total_simulations = SimulationRun.objects.count() if SimulationRun else 0
    completed_simulations = SimulationRun.objects.filter(status='completed').count() if SimulationRun else 0
    active_simulations = SimulationRun.objects.filter(status='in_progress').count() if SimulationRun else 0
    total_badges_awarded = SkillBadge.objects.annotate(
        award_count=Count('badgeaward')
    ).aggregate(total=Sum('award_count'))['total'] or 0 if SkillBadge else 0
    
    # ===== PROPCOACH STATISTICS =====
    total_challenges = PropChallenge.objects.count() if PropChallenge else 0
    active_challenges = PropChallenge.objects.filter(status='active').count() if PropChallenge else 0
    passed_challenges = PropChallenge.objects.filter(status='passed').count() if PropChallenge else 0
    prop_firms = FirmTemplate.objects.count() if FirmTemplate else 0
    
    # ===== BOT STATISTICS =====
    total_conversations = BotConversation.objects.count()
    conversations_today = BotConversation.objects.filter(created_at__gte=today_start).count()
    
    # ===== NEWS STATISTICS =====
    total_news = NewsArticle.objects.count() if NewsArticle else 0
    news_today = NewsArticle.objects.filter(published_at__gte=today_start).count() if NewsArticle else 0
    sentiment_records = MarketSentiment.objects.count() if MarketSentiment else 0
    
    # ===== SUPPORT STATISTICS =====
    total_tickets = SupportTicket.objects.count() if SupportTicket else 0
    open_tickets = SupportTicket.objects.filter(status='open').count() if SupportTicket else 0
    pending_tickets = SupportTicket.objects.filter(status='pending').count() if SupportTicket else 0
    resolved_tickets = SupportTicket.objects.filter(status='resolved').count() if SupportTicket else 0
    
    # ===== JOURNAL STATISTICS =====
    total_journal_entries = TradeJournalEntry.objects.count()
    journal_entries_week = TradeJournalEntry.objects.filter(created_at__gte=week_start).count()
    
    # ===== RECENT ACTIVITY =====
    # Order recent signals by receipt time
    recent_signals = Signal.objects.select_related('user').order_by('-received_at')[:10]
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    recent_tickets = SupportTicket.objects.select_related('user').order_by('-created_at')[:5] if SupportTicket else []
    
    # ===== SYSTEM HEALTH =====
    system_health = {
        'database': 'healthy',  # Could add actual DB health check
        'redis': 'N/A',  # If using Redis
        'storage': 'healthy',
        'api_status': 'operational'
    }
    
    context = {
        # User stats
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'staff_users': staff_users,
        'verified_users': verified_users,
        
        # Signal stats
        'total_signals': total_signals,
        'active_signals': active_signals,
        'signals_today': signals_today,
        'signals_pending': signals_pending,
        'signals_executed': signals_executed,
        'winning_signals': winning_signals,
        'losing_signals': losing_signals,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        
        # Strategy stats
        'total_strategies': total_strategies,
        'active_strategies': active_strategies,
        'strategy_performance': strategy_performance,
        
        # Session stats
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'sessions_today': sessions_today,
        
        # Risk control
        'risk_blocks_today': risk_blocks_today,
        'active_risk_controls': active_risk_controls,
        
        # ZenithMentor
        'total_apprentices': total_apprentices,
        'total_scenarios': total_scenarios,
        'total_simulations': total_simulations,
        'completed_simulations': completed_simulations,
        'active_simulations': active_simulations,
        'total_badges_awarded': total_badges_awarded,
        
        # PropCoach
        'total_challenges': total_challenges,
        'active_challenges': active_challenges,
        'passed_challenges': passed_challenges,
        'prop_firms': prop_firms,
        
        # Bot
        'total_conversations': total_conversations,
        'conversations_today': conversations_today,
        
        # News
        'total_news': total_news,
        'news_today': news_today,
        'sentiment_records': sentiment_records,
        
        # Support
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'pending_tickets': pending_tickets,
        'resolved_tickets': resolved_tickets,
        
        # Journal
        'total_journal_entries': total_journal_entries,
        'journal_entries_week': journal_entries_week,
        
        # Recent activity
        'recent_signals': recent_signals,
        'recent_users': recent_users,
        'recent_tickets': recent_tickets,
        
        # System health
        'system_health': system_health,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@staff_member_required
def user_management(request):
    """User management interface."""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter options
    filter_type = request.GET.get('filter', 'all')
    search = request.GET.get('search', '')
    
    if filter_type == 'staff':
        users = users.filter(is_staff=True)
    elif filter_type == 'active':
        users = users.filter(is_active=True)
    elif filter_type == 'inactive':
        users = users.filter(is_active=False)
    
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    context = {
        'users': users[:100],  # Paginate in production
        'filter_type': filter_type,
        'search': search,
        'total_count': users.count(),
    }
    
    return render(request, 'admin_dashboard/user_management.html', context)


@staff_member_required
def system_settings(request):
    """System settings and configuration."""
    
    if request.method == 'POST':
        # Handle settings update
        # This would typically update a Settings model
        pass
    
    context = {
        'settings': {
            'site_name': 'ZenithEdge Trading Hub',
            'maintenance_mode': False,
            'registration_enabled': True,
            'email_notifications': True,
            'max_signals_per_day': 50,
            'risk_control_enabled': True,
        }
    }
    
    return render(request, 'admin_dashboard/settings.html', context)


@staff_member_required
def system_analytics(request):
    """Comprehensive system analytics."""
    
    # Time range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # User growth
    user_growth = CustomUser.objects.filter(
        date_joined__gte=start_date
    ).extra(
        select={'day': 'date(date_joined)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Signal volume
    signal_volume = Signal.objects.filter(
        received_at__gte=start_date
    ).extra(
        select={'day': 'date(received_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Performance metrics
    performance_data = Signal.objects.filter(
        received_at__gte=start_date,
        outcome__in=['win', 'loss']
    ).extra(
        select={'day': 'date(received_at)'}
    ).values('day').annotate(
        wins=Count('id', filter=Q(outcome='win')),
        losses=Count('id', filter=Q(outcome='loss')),
        total_pnl=Sum('price')
    ).order_by('day')
    
    context = {
        'days': days,
        'user_growth': list(user_growth),
        'signal_volume': list(signal_volume),
        'performance_data': list(performance_data),
    }
    
    return render(request, 'admin_dashboard/analytics.html', context)


# ============================================
# USER MANAGEMENT VIEWS
# ============================================

@staff_member_required
def add_user(request):
    """Add new user."""
    from django.contrib.auth.forms import UserCreationForm
    from django import forms
    
    class CustomUserCreationForm(forms.ModelForm):
        password1 = forms.CharField(
            label='Password', 
            widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
        )
        password2 = forms.CharField(
            label='Password confirmation', 
            widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
        )
        
        class Meta:
            model = CustomUser
            fields = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
            widgets = {
                'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@example.com'}),
                'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
                'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
                'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }
        
        def clean_password2(self):
            password1 = self.cleaned_data.get("password1")
            password2 = self.cleaned_data.get("password2")
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError("Passwords don't match")
            return password2
        
        def save(self, commit=True):
            user = super().save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            if commit:
                user.save()
            return user
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard:user_management')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'action': 'Add'})


@staff_member_required
def edit_user(request, user_id):
    """Edit existing user."""
    from django import forms
    from django.shortcuts import get_object_or_404
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    class CustomUserEditForm(forms.ModelForm):
        class Meta:
            model = CustomUser
            fields = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_verified')
            widgets = {
                'email': forms.EmailInput(attrs={'class': 'form-control'}),
                'first_name': forms.TextInput(attrs={'class': 'form-control'}),
                'last_name': forms.TextInput(attrs={'class': 'form-control'}),
                'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }
    
    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard:user_management')
    else:
        form = CustomUserEditForm(instance=user)
    
    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'action': 'Edit', 'user_obj': user})


@staff_member_required
def delete_user(request, user_id):
    """Delete user."""
    from django.shortcuts import get_object_or_404
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.delete()
        return redirect('admin_dashboard:user_management')
    
    return render(request, 'admin_dashboard/user_confirm_delete.html', {'user_obj': user})


# ============================================
# MODULE MANAGEMENT VIEWS
# ============================================

@staff_member_required
def signals_management(request):
    """Manage signals."""
    # Start with base queryset
    signals = Signal.objects.select_related('user').order_by('-received_at')
    
    # Filter options - apply BEFORE slicing
    filter_status = request.GET.get('status', 'all')
    if filter_status == 'allowed':
        signals = signals.filter(is_allowed=True)
    elif filter_status == 'blocked':
        signals = signals.filter(is_allowed=False)
    elif filter_status == 'risk_blocked':
        signals = signals.filter(is_risk_blocked=True)
    
    # Now slice after filtering
    signals = signals[:100]
    
    context = {
        'signals': signals,
        'filter_status': filter_status,
        'total_count': Signal.objects.count(),
        'allowed_count': Signal.objects.filter(is_allowed=True).count(),
        'blocked_count': Signal.objects.filter(is_allowed=False).count(),
    }
    
    return render(request, 'admin_dashboard/signals.html', context)


@staff_member_required
def strategies_management(request):
    """Manage strategies."""
    strategies = StrategyPerformance.objects.select_related('user').order_by('-win_rate', '-total_trades')
    
    context = {
        'strategies': strategies,
        'total_count': strategies.count(),
    }
    
    return render(request, 'admin_dashboard/strategies.html', context)


@staff_member_required
def sessions_management(request):
    """Manage session rules."""
    sessions = SessionRule.objects.select_related('user').order_by('-created_at')
    
    context = {
        'sessions': sessions,
        'total_count': sessions.count(),
        'active_count': sessions.filter(is_blocked=False).count(),
        'blocked_count': sessions.filter(is_blocked=True).count(),
    }
    
    return render(request, 'admin_dashboard/sessions.html', context)


@staff_member_required
def risk_control_management(request):
    """Manage risk controls."""
    risk_controls = RiskControl.objects.select_related('user').order_by('-updated_at')
    
    context = {
        'risk_controls': risk_controls,
        'total_count': risk_controls.count(),
        'active_count': risk_controls.filter(is_active=True).count(),
        'halted_count': risk_controls.filter(is_halted=True).count(),
    }
    
    return render(request, 'admin_dashboard/risk_controls.html', context)


@staff_member_required
def prop_rules_management(request):
    """Manage prop rules."""
    from signals.models import PropRules
    prop_rules = PropRules.objects.order_by('-created_at')
    
    context = {
        'prop_rules': prop_rules,
        'total_count': prop_rules.count(),
        'active_count': prop_rules.filter(is_active=True).count(),
    }
    
    return render(request, 'admin_dashboard/prop_rules.html', context)


@staff_member_required
def trade_journal_management(request):
    """Manage trade journal entries."""
    entries = TradeJournalEntry.objects.select_related('user', 'signal').order_by('-created_at')[:100]
    
    context = {
        'entries': entries,
        'total_count': TradeJournalEntry.objects.count(),
    }
    
    return render(request, 'admin_dashboard/trade_journal.html', context)


@staff_member_required
def zenithmentor_management(request):
    """Manage ZenithMentor apprentice profiles."""
    from zenithmentor.models import ApprenticeProfile
    
    all_profiles = ApprenticeProfile.objects.select_related('user').order_by('-created_at')
    
    context = {
        'profiles': all_profiles[:100],
        'total_count': ApprenticeProfile.objects.count(),
        'active_count': all_profiles.filter(is_active=True).count() if hasattr(ApprenticeProfile, 'is_active') else 0,
    }
    
    return render(request, 'admin_dashboard/zenithmentor.html', context)


@staff_member_required
def propcoach_management(request):
    """Manage PropCoach challenges."""
    from propcoach.models import PropChallenge
    
    # Get base queryset
    all_challenges = PropChallenge.objects.select_related('user', 'template').order_by('-start_date')
    
    context = {
        'challenges': all_challenges[:100],
        'total_count': PropChallenge.objects.count(),
        'active_count': all_challenges.filter(status='active').count(),
        'passed_count': all_challenges.filter(status='passed').count(),
        'failed_count': all_challenges.filter(status='failed').count(),
    }
    
    return render(request, 'admin_dashboard/propcoach.html', context)


@staff_member_required
def zenbot_management(request):
    """Manage ZenBot conversations."""
    from bot.models import BotConversation
    
    conversations = BotConversation.objects.select_related('user').order_by('-created_at')[:100]
    
    context = {
        'conversations': conversations,
        'total_count': BotConversation.objects.count(),
    }
    
    return render(request, 'admin_dashboard/zenbot.html', context)


@staff_member_required
def zennews_management(request):
    """Manage ZenNews events."""
    from zennews.models import NewsEvent
    
    all_news = NewsEvent.objects.order_by('-timestamp')
    
    context = {
        'news_events': all_news[:100],
        'total_count': NewsEvent.objects.count(),
        'high_impact_count': all_news.filter(impact_level='high').count(),
    }
    
    return render(request, 'admin_dashboard/zennews.html', context)


@staff_member_required
def support_management(request):
    """Manage support threads."""
    from support.models import SupportThread
    
    all_threads = SupportThread.objects.select_related('user').order_by('-created_at')
    
    context = {
        'threads': all_threads[:100],
        'total_count': SupportThread.objects.count(),
        'open_count': all_threads.filter(status='open').count() if hasattr(SupportThread, 'status') else 0,
    }
    
    return render(request, 'admin_dashboard/support.html', context)
