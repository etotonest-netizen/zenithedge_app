"""
ZenithMentor Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Avg, Count, Q, Sum
from decimal import Decimal
import json

from .models import (
    ApprenticeProfile, Lesson, LessonStep, Scenario,
    SimulationRun, TradeEntry, SkillBadge, AssessmentResult, CoachingSession
)
from .adaptive_coach import adaptive_coach
from .nlp_analysis import journal_analyzer, rationale_validator
from bot.ai_score import predict_score  # ZenBot integration


@login_required
def dashboard(request):
    """Main ZenithMentor dashboard."""
    # Get or create apprentice profile
    profile, created = ApprenticeProfile.objects.get_or_create(user=request.user)
    
    if created:
        # Initialize new apprentice
        profile.skill_level = 'novice'
        profile.current_difficulty = 1
        profile.save()
    
    # Get current lesson and progress
    current_lesson = profile.current_lesson
    if not current_lesson:
        # Assign first lesson
        current_lesson = Lesson.objects.filter(is_published=True, week=0).first()
        if current_lesson:
            profile.current_lesson = current_lesson
            profile.save()
    
    # Get recent simulation runs
    recent_runs = SimulationRun.objects.filter(
        apprentice=profile
    ).order_by('-started_at')[:5]
    
    # Get badges
    badges = profile.badges.all()[:10]
    
    # Get coaching messages
    recent_coaching = CoachingSession.objects.filter(
        apprentice=profile
    ).order_by('-created_at')[:3]
    
    # Performance metrics
    stats = {
        'total_scenarios': profile.total_scenarios_attempted,
        'passed_scenarios': profile.total_scenarios_passed,
        'pass_rate': (profile.total_scenarios_passed / profile.total_scenarios_attempted * 100) 
                     if profile.total_scenarios_attempted > 0 else 0,
        'win_rate': float(profile.win_rate),
        'expectancy': float(profile.overall_expectancy),
        'discipline_score': float(profile.discipline_score),
        'pass_probability': float(profile.pass_probability),
    }
    
    # Certification status
    cert_requirements = {
        'lessons_required': 40,
        'lessons_completed': profile.lessons_completed,
        'scenarios_required': 100,
        'scenarios_completed': profile.total_scenarios_passed,
        'min_expectancy': 0.2,
        'current_expectancy': float(profile.overall_expectancy),
        'min_discipline': 70,
        'current_discipline': float(profile.discipline_score),
    }
    
    context = {
        'profile': profile,
        'current_lesson': current_lesson,
        'recent_runs': recent_runs,
        'badges': badges,
        'recent_coaching': recent_coaching,
        'stats': stats,
        'cert_requirements': cert_requirements,
    }
    
    return render(request, 'zenithmentor/dashboard.html', context)


@login_required
def curriculum(request):
    """Display full curriculum."""
    lessons = Lesson.objects.filter(is_published=True).order_by('week', 'order')
    
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    # Group by week
    curriculum_by_week = {}
    for lesson in lessons:
        week = lesson.week
        if week not in curriculum_by_week:
            curriculum_by_week[week] = []
        
        # Check if accessible
        can_access = True
        if lesson.prerequisites.exists():
            # Check if all prerequisites completed
            for prereq in lesson.prerequisites.all():
                prereq_assessments = AssessmentResult.objects.filter(
                    apprentice=profile,
                    lesson=prereq,
                    passed=True
                )
                if not prereq_assessments.exists():
                    can_access = False
                    break
        
        curriculum_by_week[week].append({
            'lesson': lesson,
            'can_access': can_access,
        })
    
    context = {
        'curriculum_by_week': curriculum_by_week,
        'profile': profile,
    }
    
    return render(request, 'zenithmentor/curriculum.html', context)


@login_required
def lesson_detail(request, lesson_id):
    """Display lesson content and steps."""
    lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    # Check access
    can_access = True
    if lesson.prerequisites.exists():
        for prereq in lesson.prerequisites.all():
            prereq_assessments = AssessmentResult.objects.filter(
                apprentice=profile,
                lesson=prereq,
                passed=True
            )
            if not prereq_assessments.exists():
                can_access = False
                break
    
    if not can_access:
        return render(request, 'zenithmentor/lesson_locked.html', {'lesson': lesson})
    
    # Get steps
    steps = lesson.steps.all()
    
    # Get user's progress on this lesson
    completed_steps = []  # Track via session or DB
    
    context = {
        'lesson': lesson,
        'steps': steps,
        'profile': profile,
        'completed_steps': completed_steps,
    }
    
    return render(request, 'zenithmentor/lesson_detail.html', context)


@login_required
def scenario_list(request):
    """Browse available scenarios."""
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    # Filter scenarios by difficulty
    difficulty_filter = request.GET.get('difficulty', profile.current_difficulty)
    regime_filter = request.GET.get('regime', '')
    strategy_filter = request.GET.get('strategy', '')
    
    scenarios = Scenario.objects.filter(is_active=True)
    
    if difficulty_filter:
        scenarios = scenarios.filter(difficulty=difficulty_filter)
    
    if regime_filter:
        scenarios = scenarios.filter(regime=regime_filter)
    
    if strategy_filter:
        scenarios = scenarios.filter(strategy_focus__icontains=strategy_filter)
    
    scenarios = scenarios.order_by('difficulty', 'name')
    
    context = {
        'scenarios': scenarios,
        'profile': profile,
        'current_difficulty': profile.current_difficulty,
    }
    
    return render(request, 'zenithmentor/scenario_list.html', context)


@login_required
@require_http_methods(["POST"])
def launch_simulation(request):
    """Start a new simulation run."""
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    # Handle both JSON and form data
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        scenario_id = data.get('scenario_id')
    else:
        scenario_id = request.POST.get('scenario_id')
    
    scenario = get_object_or_404(Scenario, id=scenario_id, is_active=True)
    
    # Create simulation run
    sim_run = SimulationRun.objects.create(
        apprentice=profile,
        scenario=scenario,
        status='in_progress',
        initial_balance=10000,
        final_balance=10000,
    )
    
    # Increment scenario usage
    scenario.increment_usage()
    
    # Update apprentice metrics
    profile.total_scenarios_attempted += 1
    profile.save()
    
    # Return JSON for AJAX requests, redirect for form submissions
    if request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'simulation_id': str(sim_run.id),
            'scenario': {
                'name': scenario.name,
                'candle_data': scenario.candle_data,
                'has_news': scenario.has_synthetic_news,
                'news_events': scenario.synthetic_news_events,
            }
        })
    else:
        # Redirect to simulation replay page
        return redirect('zenithmentor:simulation_replay', simulation_id=sim_run.id)


@login_required
def simulation_replay(request, simulation_id):
    """Replay/resume a simulation."""
    sim_run = get_object_or_404(SimulationRun, id=simulation_id)
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    if sim_run.apprentice != profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get scenario data
    scenario = sim_run.scenario
    
    # Get existing trades
    trades = sim_run.trades.all().order_by('entry_candle_index')
    
    context = {
        'simulation': sim_run,  # Use 'simulation' to match template
        'sim_run': sim_run,  # Keep for backward compatibility
        'scenario': scenario,
        'candle_data': json.dumps(scenario.candle_data),
        'trades': trades,
        'current_balance': float(sim_run.final_balance),
        'profile': profile,
    }
    
    return render(request, 'zenithmentor/simulation_replay.html', context)


@login_required
@require_http_methods(["POST"])
def submit_trade(request):
    """Submit a trade during simulation."""
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    data = json.loads(request.body)
    simulation_id = data.get('simulation_id')
    
    sim_run = get_object_or_404(SimulationRun, id=simulation_id)
    
    if sim_run.apprentice != profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Extract trade data
    direction = data.get('direction')
    entry_price = Decimal(str(data.get('entry_price')))
    stop_loss = Decimal(str(data.get('stop_loss')))
    take_profit = Decimal(str(data.get('take_profit'))) if data.get('take_profit') else None
    position_size = Decimal(str(data.get('position_size', 1000)))
    rationale = data.get('rationale', '')
    candle_index = data.get('candle_index')
    
    # Validate rationale
    rationale_check = rationale_validator.validate_rationale(rationale)
    
    if not rationale_check['is_valid'] and profile.coaching_mode == 'assisted':
        return JsonResponse({
            'success': False,
            'error': 'incomplete_rationale',
            'feedback': rationale_check['feedback'],
            'missing_elements': rationale_check['missing_elements'],
        })
    
    # Check if coach should intervene
    trade_data = {
        'risk_percentage': float(data.get('risk_percentage', 2)),
        'account_balance': float(sim_run.final_balance),
    }
    
    should_block, block_reason = adaptive_coach.should_intervene(profile, trade_data)
    
    if should_block:
        return JsonResponse({
            'success': False,
            'error': 'coach_intervention',
            'message': block_reason,
        })
    
    # Create trade entry
    trade = TradeEntry.objects.create(
        simulation_run=sim_run,
        direction=direction,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size,
        entry_candle_index=candle_index,
        entry_timestamp=timezone.now(),
        rationale=rationale,
        status='open',
    )
    
    # Calculate risk
    trade.calculate_risk(sim_run.final_balance)
    
    # Get ZenBot score (if available)
    try:
        # Prepare signal data for ZenBot (using a mock signal object)
        from signals.models import Signal
        from django.utils import timezone as tz
        
        # Create temporary signal for scoring
        temp_signal = Signal(
            user=request.user,
            symbol=sim_run.scenario.symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            timestamp=tz.now(),
        )
        
        zenbot_score, breakdown = predict_score(temp_signal, apply_cognition=False, apply_prop_mode=False)
        trade.zenbot_score = Decimal(str(zenbot_score))
        trade.coach_verdict = f"ZenBot Score: {zenbot_score}/100"
        trade.save()
        
    except Exception as e:
        # ZenBot not available or error
        trade.coach_verdict = "ZenBot analysis unavailable"
        trade.save()
    
    # Update simulation counts
    sim_run.trades_count += 1
    sim_run.save()
    
    return JsonResponse({
        'success': True,
        'trade_id': str(trade.id),
        'zenbot_score': float(trade.zenbot_score) if trade.zenbot_score else None,
        'coach_verdict': trade.coach_verdict,
        'rationale_feedback': rationale_check,
    })


@login_required
@require_http_methods(["POST"])
def close_trade(request):
    """Close an open trade."""
    data = json.loads(request.body)
    trade_id = data.get('trade_id')
    exit_price = Decimal(str(data.get('exit_price')))
    candle_index = data.get('candle_index')
    
    trade = get_object_or_404(TradeEntry, id=trade_id)
    sim_run = trade.simulation_run
    
    # Verify ownership
    if sim_run.apprentice.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Calculate P&L
    if trade.direction == 'long':
        price_diff = exit_price - trade.entry_price
    else:
        price_diff = trade.entry_price - exit_price
    
    trade.pnl = price_diff * trade.position_size
    trade.pnl_percentage = (price_diff / trade.entry_price) * 100
    trade.was_winner = trade.pnl > 0
    
    trade.exit_price = exit_price
    trade.exit_candle_index = candle_index
    trade.exit_timestamp = timezone.now()
    trade.status = 'closed'
    trade.save()
    
    # Update simulation balance
    sim_run.final_balance += trade.pnl
    sim_run.final_pnl += trade.pnl
    
    if trade.was_winner:
        sim_run.winning_trades += 1
    else:
        sim_run.losing_trades += 1
    
    # Update max drawdown
    if trade.pnl < 0:
        current_dd = sim_run.initial_balance - sim_run.final_balance
        if current_dd > sim_run.max_drawdown:
            sim_run.max_drawdown = current_dd
    
    sim_run.save()
    
    return JsonResponse({
        'success': True,
        'pnl': float(trade.pnl),
        'new_balance': float(sim_run.final_balance),
        'was_winner': trade.was_winner,
    })


@login_required
@require_http_methods(["POST"])
def add_journal_entry(request):
    """Add journal note during simulation."""
    data = json.loads(request.body)
    simulation_id = data.get('simulation_id')
    entry_text = data.get('entry', '')
    
    sim_run = get_object_or_404(SimulationRun, id=simulation_id)
    
    # Verify ownership
    if sim_run.apprentice.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Analyze journal entry
    analysis = journal_analyzer.analyze_journal_entry(entry_text)
    
    # Add to simulation log
    sim_run.journal_entries.append({
        'timestamp': timezone.now().isoformat(),
        'text': entry_text,
        'analysis': analysis,
    })
    sim_run.save()
    
    # Check for psychological warnings
    if analysis['warnings']:
        # Create coaching session
        CoachingSession.objects.create(
            apprentice=sim_run.apprentice,
            simulation_run=sim_run,
            topic="Psychological Alert",
            message="\n".join(analysis['warnings']),
            triggered_by="journal_analysis",
            datapoints=analysis,
        )
    
    return JsonResponse({
        'success': True,
        'analysis': analysis,
    })


@login_required
@require_http_methods(["POST"])
def complete_simulation(request):
    """Mark simulation as complete and grade it."""
    data = json.loads(request.body)
    simulation_id = data.get('simulation_id')
    
    sim_run = get_object_or_404(SimulationRun, id=simulation_id)
    profile = sim_run.apprentice
    
    # Verify ownership
    if profile.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Grade the simulation
    from .grading import grade_simulation
    grading_result = grade_simulation(sim_run)
    
    # Update simulation
    sim_run.status = 'completed'
    sim_run.completed_at = timezone.now()
    sim_run.technical_score = grading_result['technical_score']
    sim_run.risk_mgmt_score = grading_result['risk_mgmt_score']
    sim_run.execution_score = grading_result['execution_score']
    sim_run.journaling_score = grading_result['journaling_score']
    sim_run.discipline_score = grading_result['discipline_score']
    sim_run.calculate_overall_score()
    
    # Generate personalized feedback
    feedback_data = adaptive_coach.generate_personalized_feedback(sim_run)
    sim_run.coach_feedback = feedback_data['feedback']
    sim_run.strengths = feedback_data['strengths']
    sim_run.weaknesses = feedback_data['weaknesses']
    sim_run.suggestions = feedback_data['suggestions']
    sim_run.save()
    
    # Update apprentice profile
    if sim_run.passed:
        profile.total_scenarios_passed += 1
    
    profile.update_metrics()
    adaptive_coach.update_apprentice_profile(profile)
    
    # Check for badge awards
    from .gamification import check_and_award_badges
    check_and_award_badges(profile, sim_run)
    
    return JsonResponse({
        'success': True,
        'passed': sim_run.passed,
        'overall_score': float(sim_run.overall_score),
        'feedback': sim_run.coach_feedback,
        'strengths': sim_run.strengths,
        'weaknesses': sim_run.weaknesses,
        'suggestions': sim_run.suggestions,
        'new_pass_probability': float(profile.pass_probability),
    })


@login_required
def simulation_results(request, simulation_id):
    """View detailed simulation results."""
    sim_run = get_object_or_404(SimulationRun, id=simulation_id)
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    if sim_run.apprentice != profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    trades = sim_run.trades.all().order_by('entry_candle_index')
    
    # Prepare equity curve data
    equity_curve = [float(sim_run.initial_balance)]
    balance = sim_run.initial_balance
    
    for trade in trades:
        balance += trade.pnl
        equity_curve.append(float(balance))
    
    context = {
        'sim_run': sim_run,
        'trades': trades,
        'equity_curve': json.dumps(equity_curve),
        'profile': profile,
    }
    
    return render(request, 'zenithmentor/simulation_results.html', context)


@login_required
def progress_report(request):
    """View detailed progress and analytics."""
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    # Get all simulation runs
    all_runs = SimulationRun.objects.filter(
        apprentice=profile,
        status='completed'
    ).order_by('completed_at')
    
    # Performance over time
    performance_data = []
    for run in all_runs:
        performance_data.append({
            'date': run.completed_at.isoformat(),
            'score': float(run.overall_score),
            'pnl': float(run.final_pnl),
            'passed': run.passed,
        })
    
    # Strategy breakdown
    strategy_stats = {}
    for run in all_runs:
        strategy = run.scenario.strategy_focus
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {'total': 0, 'passed': 0, 'avg_score': []}
        
        strategy_stats[strategy]['total'] += 1
        if run.passed:
            strategy_stats[strategy]['passed'] += 1
        strategy_stats[strategy]['avg_score'].append(float(run.overall_score))
    
    # Calculate averages
    for strategy, stats in strategy_stats.items():
        stats['pass_rate'] = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['avg_score'] = sum(stats['avg_score']) / len(stats['avg_score']) if stats['avg_score'] else 0
    
    context = {
        'profile': profile,
        'performance_data': json.dumps(performance_data),
        'strategy_stats': strategy_stats,
        'total_runs': all_runs.count(),
    }
    
    return render(request, 'zenithmentor/progress_report.html', context)


@login_required
def badges(request):
    """View earned badges and available badges."""
    profile = ApprenticeProfile.objects.get(user=request.user)
    
    earned_badges = profile.badges.all()
    all_badges = SkillBadge.objects.filter(is_active=True)
    
    available_badges = all_badges.exclude(id__in=earned_badges.values_list('id', flat=True))
    
    context = {
        'profile': profile,
        'earned_badges': earned_badges,
        'available_badges': available_badges,
    }
    
    return render(request, 'zenithmentor/badges.html', context)
