"""
Gamification - Badges, achievements, and rewards
"""
from decimal import Decimal
from django.utils import timezone
from .models import SkillBadge, BadgeAward, ApprenticeProfile, SimulationRun


def check_and_award_badges(profile: ApprenticeProfile, latest_run: SimulationRun = None):
    """
    Check if apprentice earned any new badges and award them.
    
    Args:
        profile: ApprenticeProfile to check
        latest_run: Optional most recent simulation run that triggered check
    """
    badges_to_check = SkillBadge.objects.filter(is_active=True)
    
    for badge in badges_to_check:
        # Skip if already earned
        if profile.badges.filter(id=badge.id).exists():
            continue
        
        # Check requirements
        if check_badge_requirements(profile, badge, latest_run):
            # Award badge
            award = BadgeAward.objects.create(
                apprentice=profile,
                badge=badge,
                awarded_for=f"Earned on {timezone.now().strftime('%Y-%m-%d')}"
            )
            
            # Could trigger notification here
            print(f"🏆 Badge Awarded: {badge.name} to {profile.user.email}")


def check_badge_requirements(profile: ApprenticeProfile, badge: SkillBadge, 
                             latest_run: SimulationRun = None) -> bool:
    """
    Check if apprentice meets badge requirements.
    
    Returns:
        True if requirements met
    """
    criteria = badge.requirement_criteria
    
    if not criteria:
        return False
    
    # Performance badges
    if badge.category == 'performance':
        if 'min_expectancy' in criteria:
            if float(profile.overall_expectancy) < criteria['min_expectancy']:
                return False
        
        if 'min_win_rate' in criteria:
            if float(profile.win_rate) < criteria['min_win_rate']:
                return False
        
        if 'min_scenarios_passed' in criteria:
            if profile.total_scenarios_passed < criteria['min_scenarios_passed']:
                return False
    
    # Discipline badges
    elif badge.category == 'discipline':
        if 'min_discipline_score' in criteria:
            if float(profile.discipline_score) < criteria['min_discipline_score']:
                return False
        
        if 'max_revenge_trades' in criteria:
            if profile.revenge_trade_count > criteria['max_revenge_trades']:
                return False
        
        if 'min_journal_quality' in criteria:
            if float(profile.journaling_quality_score) < criteria['min_journal_quality']:
                return False
    
    # Consistency badges
    elif badge.category == 'consistency':
        if 'min_consecutive_wins' in criteria:
            recent_runs = SimulationRun.objects.filter(
                apprentice=profile,
                status='completed'
            ).order_by('-completed_at')[:criteria['min_consecutive_wins']]
            
            if recent_runs.count() < criteria['min_consecutive_wins']:
                return False
            
            if not all(run.passed for run in recent_runs):
                return False
        
        if 'min_risk_consistency' in criteria:
            if float(profile.risk_consistency_score) < criteria['min_risk_consistency']:
                return False
    
    # Milestone badges
    elif badge.category == 'milestone':
        if 'lessons_completed' in criteria:
            if profile.lessons_completed < criteria['lessons_completed']:
                return False
        
        if 'total_scenarios' in criteria:
            if profile.total_scenarios_attempted < criteria['total_scenarios']:
                return False
    
    # Mastery badges (strategy-specific)
    elif badge.category == 'mastery':
        strategy = criteria.get('strategy')
        if strategy:
            strategy_prof = profile.strategy_proficiency.get(strategy, 0)
            min_prof = criteria.get('min_proficiency', 80)
            
            if strategy_prof < min_prof:
                return False
    
    return True


def initialize_default_badges():
    """
    Create default badge set. Run via management command.
    """
    default_badges = [
        # Discipline badges
        {
            'name': 'First Steps',
            'description': 'Completed your first simulation with discipline',
            'category': 'discipline',
            'requirement_criteria': {
                'min_scenarios_passed': 1,
                'min_discipline_score': 70,
            },
            'icon_name': 'award-fill',
            'color': 'silver',
        },
        {
            'name': 'Risk Manager',
            'description': 'Maintained excellent risk management for 20 trades',
            'category': 'discipline',
            'requirement_criteria': {
                'min_discipline_score': 80,
                'min_scenarios_passed': 20,
            },
            'icon_name': 'shield-fill-check',
            'color': 'blue',
        },
        {
            'name': 'Journal Master',
            'description': 'Consistently high-quality trade journaling',
            'category': 'discipline',
            'requirement_criteria': {
                'min_journal_quality': 80,
                'min_scenarios_passed': 15,
            },
            'icon_name': 'journal-text',
            'color': 'purple',
        },
        
        # Performance badges
        {
            'name': 'Profitable Trader',
            'description': 'Achieved positive expectancy over 30 simulations',
            'category': 'performance',
            'requirement_criteria': {
                'min_expectancy': 0.2,
                'min_scenarios_passed': 30,
            },
            'icon_name': 'graph-up-arrow',
            'color': 'green',
        },
        {
            'name': 'High Win Rate',
            'description': 'Maintained 60%+ win rate over 25 simulations',
            'category': 'performance',
            'requirement_criteria': {
                'min_win_rate': 60,
                'min_scenarios_passed': 25,
            },
            'icon_name': 'trophy-fill',
            'color': 'gold',
        },
        {
            'name': 'Century',
            'description': 'Passed 100 simulations',
            'category': 'milestone',
            'requirement_criteria': {
                'min_scenarios_passed': 100,
            },
            'icon_name': 'star-fill',
            'color': 'gold',
        },
        
        # Consistency badges
        {
            'name': 'Consistent Performer',
            'description': 'Passed 10 simulations in a row',
            'category': 'consistency',
            'requirement_criteria': {
                'min_consecutive_wins': 10,
            },
            'icon_name': 'arrow-repeat',
            'color': 'teal',
        },
        {
            'name': 'Risk Discipline',
            'description': 'Ultra-consistent risk sizing across trades',
            'category': 'consistency',
            'requirement_criteria': {
                'min_risk_consistency': 90,
                'min_scenarios_passed': 20,
            },
            'icon_name': 'gear-fill',
            'color': 'blue',
        },
        
        # Mastery badges
        {
            'name': 'Trend Master',
            'description': 'Mastered trend trading strategies',
            'category': 'mastery',
            'requirement_criteria': {
                'strategy': 'trend',
                'min_proficiency': 80,
            },
            'icon_name': 'arrow-up-right',
            'color': 'green',
        },
        {
            'name': 'SMC Expert',
            'description': 'Mastered Smart Money Concepts',
            'category': 'mastery',
            'requirement_criteria': {
                'strategy': 'smc',
                'min_proficiency': 85,
            },
            'icon_name': 'lightning-fill',
            'color': 'orange',
        },
        {
            'name': 'Breakout Specialist',
            'description': 'Mastered breakout trading',
            'category': 'mastery',
            'requirement_criteria': {
                'strategy': 'breakout',
                'min_proficiency': 80,
            },
            'icon_name': 'box-arrow-up-right',
            'color': 'red',
        },
        
        # Ultimate badges
        {
            'name': 'ZenithMentor Certified',
            'description': 'Completed full certification program',
            'category': 'milestone',
            'requirement_criteria': {
                'lessons_completed': 40,
                'min_scenarios_passed': 100,
                'min_expectancy': 0.2,
                'min_discipline_score': 75,
            },
            'icon_name': 'patch-check-fill',
            'color': 'gold',
        },
    ]
    
    for badge_data in default_badges:
        badge, created = SkillBadge.objects.get_or_create(
            name=badge_data['name'],
            defaults=badge_data
        )
        if created:
            print(f"Created badge: {badge.name}")


def calculate_leaderboard_score(profile: ApprenticeProfile) -> float:
    """
    Calculate composite leaderboard score.
    
    Combines multiple metrics into single ranking score.
    """
    score = 0.0
    
    # Expectancy (40%)
    score += float(profile.overall_expectancy) * 100 * 0.4
    
    # Win rate (20%)
    score += float(profile.win_rate) * 0.2
    
    # Discipline (20%)
    score += float(profile.discipline_score) * 0.2
    
    # Scenarios passed (10%)
    score += min(100, profile.total_scenarios_passed) * 0.1
    
    # Badge count bonus (10%)
    badge_count = profile.badges.count()
    score += min(100, badge_count * 10) * 0.1
    
    return round(score, 2)


def get_leaderboard(limit: int = 10) -> list:
    """
    Get top apprentices by leaderboard score.
    
    Returns:
        List of dicts with profile data and scores
    """
    profiles = ApprenticeProfile.objects.all()
    
    leaderboard = []
    for profile in profiles:
        score = calculate_leaderboard_score(profile)
        leaderboard.append({
            'profile': profile,
            'score': score,
            'rank': 0,  # Will be set after sorting
        })
    
    # Sort by score
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    # Assign ranks
    for idx, entry in enumerate(leaderboard[:limit]):
        entry['rank'] = idx + 1
    
    return leaderboard[:limit]
