"""
Analytics Integration for PropCoach

Combines backtest results with prop challenge data to:
- Identify which strategies pass challenges
- Simulate multi-challenge outcomes
- Predict success probability
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
import logging

logger = logging.getLogger(__name__)


def correlate_with_backtests(user) -> Dict:
    """
    Correlate backtest strategy performance with prop challenge success.
    
    Identifies which strategies are most successful in passing challenges.
    
    Args:
        user: User object
        
    Returns:
        Dict with correlation data
    """
    from propcoach.models import PropChallenge, TradeRecord
    from analytics.models import BacktestResult
    
    try:
        # Get completed challenges
        completed_challenges = PropChallenge.objects.filter(
            user=user,
            status__in=['passed', 'failed']
        )
        
        if not completed_challenges.exists():
            return {
                'status': 'no_data',
                'message': 'No completed challenges to analyze'
            }
        
        # Analyze strategies used in challenges
        strategy_performance = {}
        
        for challenge in completed_challenges:
            trades = TradeRecord.objects.filter(challenge=challenge)
            
            for trade in trades:
                strategy = trade.strategy_used or 'Unknown'
                
                if strategy not in strategy_performance:
                    strategy_performance[strategy] = {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'total_pnl': 0,
                        'challenges_passed': 0,
                        'challenges_failed': 0,
                        'avg_confidence': 0,
                        'confidence_sum': 0
                    }
                
                perf = strategy_performance[strategy]
                perf['total_trades'] += 1
                
                if trade.profit_loss > 0:
                    perf['winning_trades'] += 1
                
                perf['total_pnl'] += float(trade.profit_loss)
                perf['confidence_sum'] += trade.confidence_score or 50
                
                # Track challenge outcome
                if challenge.status == 'passed':
                    perf['challenges_passed'] += 1
                elif challenge.status == 'failed':
                    perf['challenges_failed'] += 1
        
        # Calculate metrics
        for strategy, perf in strategy_performance.items():
            if perf['total_trades'] > 0:
                perf['win_rate'] = (perf['winning_trades'] / perf['total_trades']) * 100
                perf['avg_confidence'] = perf['confidence_sum'] / perf['total_trades']
                perf['avg_pnl_per_trade'] = perf['total_pnl'] / perf['total_trades']
            
            total_challenges = perf['challenges_passed'] + perf['challenges_failed']
            if total_challenges > 0:
                perf['challenge_pass_rate'] = (perf['challenges_passed'] / total_challenges) * 100
            else:
                perf['challenge_pass_rate'] = 0
        
        # Get backtest results for comparison
        backtests = BacktestResult.objects.filter(user=user)
        backtest_data = {}
        
        for backtest in backtests:
            strategy = backtest.strategy or 'Unknown'
            backtest_data[strategy] = {
                'total_return': float(backtest.total_return),
                'win_rate': float(backtest.win_rate),
                'max_drawdown': float(backtest.max_drawdown),
                'profit_factor': float(backtest.profit_factor),
                'sharpe_ratio': float(backtest.sharpe_ratio),
            }
        
        # Correlate backtest with challenge performance
        correlation = []
        
        for strategy, perf in strategy_performance.items():
            backtest = backtest_data.get(strategy, {})
            
            correlation.append({
                'strategy': strategy,
                'challenge_data': {
                    'trades': perf['total_trades'],
                    'win_rate': round(perf['win_rate'], 2),
                    'avg_pnl': round(perf['avg_pnl_per_trade'], 2),
                    'pass_rate': round(perf['challenge_pass_rate'], 2),
                    'avg_confidence': round(perf['avg_confidence'], 1)
                },
                'backtest_data': backtest,
                'correlation_score': calculate_correlation_score(perf, backtest)
            })
        
        # Sort by pass rate
        correlation.sort(key=lambda x: x['challenge_data']['pass_rate'], reverse=True)
        
        return {
            'status': 'success',
            'total_completed_challenges': completed_challenges.count(),
            'strategies_analyzed': len(strategy_performance),
            'correlation': correlation,
            'best_strategy': correlation[0]['strategy'] if correlation else None,
            'worst_strategy': correlation[-1]['strategy'] if correlation else None
        }
        
    except Exception as e:
        logger.error(f"Backtest correlation failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


def calculate_correlation_score(challenge_perf: Dict, backtest_data: Dict) -> float:
    """Calculate correlation score between backtest and challenge performance."""
    if not backtest_data:
        return 0.0
    
    score = 0.0
    
    # Win rate correlation (30%)
    if 'win_rate' in backtest_data:
        wr_diff = abs(challenge_perf['win_rate'] - backtest_data['win_rate'])
        score += max(0, 30 - wr_diff)
    
    # Challenge pass rate (40%)
    score += challenge_perf['challenge_pass_rate'] * 0.4
    
    # Trading activity (30%)
    if challenge_perf['total_trades'] >= 20:
        score += 30
    elif challenge_perf['total_trades'] >= 10:
        score += 20
    else:
        score += 10
    
    return round(score, 2)


def simulate_multi_challenge(user, strategy: Optional[str] = None, n_simulations: int = 10) -> Dict:
    """
    Run Monte Carlo simulation to predict multi-challenge outcomes.
    
    Args:
        user: User object
        strategy: Optional strategy name to focus on
        n_simulations: Number of simulations to run
        
    Returns:
        Dict with simulation results
    """
    from propcoach.models import PropChallenge, TradeRecord
    import random
    
    try:
        # Get historical challenge data
        historical_challenges = PropChallenge.objects.filter(
            user=user,
            status__in=['passed', 'failed']
        )
        
        if historical_challenges.count() < 3:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 3 completed challenges for simulation'
            }
        
        # Extract historical metrics
        historical_metrics = []
        
        for challenge in historical_challenges:
            trades = TradeRecord.objects.filter(challenge=challenge)
            
            if strategy:
                trades = trades.filter(strategy_used=strategy)
            
            if trades.exists():
                historical_metrics.append({
                    'win_rate': challenge.win_rate / 100.0,
                    'avg_trade_return': float(trades.aggregate(Avg('profit_loss_percent'))['profit_loss_percent__avg'] or 0),
                    'max_drawdown': float(challenge.max_total_drawdown_reached),
                    'passed': challenge.status == 'passed',
                    'violations': challenge.violation_count
                })
        
        if len(historical_metrics) < 3:
            return {
                'status': 'insufficient_data',
                'message': f'Not enough historical data for {strategy or "all strategies"}'
            }
        
        # Run simulations
        simulation_results = []
        
        for i in range(n_simulations):
            # Sample from historical metrics with random variation
            base_metrics = random.choice(historical_metrics)
            
            # Add randomness
            win_rate = max(0.1, min(0.9, base_metrics['win_rate'] + random.gauss(0, 0.1)))
            avg_return = base_metrics['avg_trade_return'] * (1 + random.gauss(0, 0.3))
            max_dd = abs(base_metrics['max_drawdown'] * (1 + random.gauss(0, 0.2)))
            violations = max(0, int(base_metrics['violations'] + random.gauss(0, 1)))
            
            # Simulate challenge outcome
            simulated_trades = random.randint(15, 40)
            wins = int(simulated_trades * win_rate)
            losses = simulated_trades - wins
            
            # Calculate profit
            total_return = (wins * avg_return * 1.5) + (losses * avg_return * 0.8)
            
            # Determine pass/fail
            passed = (
                total_return >= 8.0 and  # At least 8% profit
                max_dd <= 10.0 and  # Within drawdown limit
                violations == 0 and  # No violations
                simulated_trades >= 20  # Minimum trades
            )
            
            simulation_results.append({
                'simulation_id': i + 1,
                'trades': simulated_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate * 100,
                'total_return': total_return,
                'max_drawdown': max_dd,
                'violations': violations,
                'passed': passed
            })
        
        # Aggregate results
        passed_count = sum(1 for r in simulation_results if r['passed'])
        pass_probability = (passed_count / n_simulations) * 100
        
        avg_return = sum(r['total_return'] for r in simulation_results) / n_simulations
        avg_dd = sum(r['max_drawdown'] for r in simulation_results) / n_simulations
        avg_wr = sum(r['win_rate'] for r in simulation_results) / n_simulations
        
        return {
            'status': 'success',
            'simulations_run': n_simulations,
            'strategy': strategy or 'All strategies',
            'pass_probability': round(pass_probability, 2),
            'passed_simulations': passed_count,
            'failed_simulations': n_simulations - passed_count,
            'expected_performance': {
                'avg_return': round(avg_return, 2),
                'avg_drawdown': round(avg_dd, 2),
                'avg_win_rate': round(avg_wr, 2)
            },
            'confidence_level': calculate_confidence_level(historical_metrics),
            'simulations': simulation_results[:5]  # Return first 5 for display
        }
        
    except Exception as e:
        logger.error(f"Multi-challenge simulation failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


def calculate_confidence_level(historical_metrics: List[Dict]) -> str:
    """Calculate confidence level for simulation based on historical data quality."""
    if len(historical_metrics) >= 10:
        return 'High (10+ challenges)'
    elif len(historical_metrics) >= 5:
        return 'Medium (5-9 challenges)'
    else:
        return 'Low (3-4 challenges)'


def identify_failure_patterns(user) -> Dict:
    """
    Identify common patterns that lead to challenge failure.
    
    Args:
        user: User object
        
    Returns:
        Dict with failure pattern analysis
    """
    from propcoach.models import PropChallenge, PropRuleViolation, TradeRecord
    
    try:
        failed_challenges = PropChallenge.objects.filter(
            user=user,
            status='failed'
        )
        
        if not failed_challenges.exists():
            return {
                'status': 'success',
                'message': 'No failed challenges - excellent work!',
                'patterns': []
            }
        
        patterns = {
            'drawdown_breaches': 0,
            'time_violations': 0,
            'leverage_violations': 0,
            'position_size_violations': 0,
            'consistency_violations': 0,
            'emotional_trading': 0,
            'overtrading': 0,
            'poor_risk_reward': 0,
        }
        
        detailed_patterns = []
        
        for challenge in failed_challenges:
            # Get violations
            violations = PropRuleViolation.objects.filter(challenge=challenge)
            
            for violation in violations:
                if violation.violation_type in ['daily_drawdown', 'total_drawdown']:
                    patterns['drawdown_breaches'] += 1
                elif violation.violation_type == 'min_trade_time':
                    patterns['time_violations'] += 1
                elif violation.violation_type == 'max_leverage':
                    patterns['leverage_violations'] += 1
                elif violation.violation_type == 'max_position_size':
                    patterns['position_size_violations'] += 1
                elif violation.violation_type == 'consistency':
                    patterns['consistency_violations'] += 1
            
            # Analyze trades
            trades = TradeRecord.objects.filter(challenge=challenge)
            
            if trades.count() > 50:
                patterns['overtrading'] += 1
                detailed_patterns.append({
                    'pattern': 'Overtrading',
                    'description': f'Challenge {challenge.id}: {trades.count()} trades',
                    'recommendation': 'Focus on quality over quantity'
                })
            
            # Check risk/reward
            poor_rr_count = trades.filter(risk_reward_ratio__lt=1.5).count()
            if poor_rr_count > trades.count() * 0.5:
                patterns['poor_risk_reward'] += 1
                detailed_patterns.append({
                    'pattern': 'Poor Risk/Reward',
                    'description': f'{poor_rr_count} trades with R:R < 1.5',
                    'recommendation': 'Aim for minimum 2:1 risk/reward ratio'
                })
        
        # Sort patterns by frequency
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        
        # Generate recommendations
        recommendations = []
        
        if patterns['drawdown_breaches'] > 0:
            recommendations.append({
                'issue': 'Drawdown breaches',
                'frequency': patterns['drawdown_breaches'],
                'recommendation': 'Reduce position sizes by 50% and use wider stops'
            })
        
        if patterns['overtrading'] > 0:
            recommendations.append({
                'issue': 'Overtrading',
                'frequency': patterns['overtrading'],
                'recommendation': 'Limit yourself to 2-3 high-quality trades per day'
            })
        
        if patterns['poor_risk_reward'] > 0:
            recommendations.append({
                'issue': 'Poor risk/reward ratios',
                'frequency': patterns['poor_risk_reward'],
                'recommendation': 'Only take trades with minimum 2:1 R:R ratio'
            })
        
        if patterns['leverage_violations'] > 0:
            recommendations.append({
                'issue': 'Excessive leverage',
                'frequency': patterns['leverage_violations'],
                'recommendation': 'Keep leverage below 50:1 for prop challenges'
            })
        
        return {
            'status': 'success',
            'total_failed_challenges': failed_challenges.count(),
            'patterns': sorted_patterns,
            'detailed_patterns': detailed_patterns,
            'recommendations': recommendations,
            'most_common_failure': sorted_patterns[0][0] if sorted_patterns else None
        }
        
    except Exception as e:
        logger.error(f"Failure pattern analysis failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


def get_challenge_insights(user) -> Dict:
    """
    Get comprehensive insights across all user's challenges.
    
    Args:
        user: User object
        
    Returns:
        Dict with insights
    """
    from propcoach.models import PropChallenge, TradeRecord
    
    try:
        all_challenges = PropChallenge.objects.filter(user=user)
        
        if not all_challenges.exists():
            return {
                'status': 'no_data',
                'message': 'No challenges found'
            }
        
        # Overall statistics
        total = all_challenges.count()
        passed = all_challenges.filter(status='passed').count()
        failed = all_challenges.filter(status='failed').count()
        active = all_challenges.filter(status='active').count()
        
        insights = {
            'total_challenges': total,
            'passed': passed,
            'failed': failed,
            'active': active,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
        }
        
        # Get all trades
        all_trades = TradeRecord.objects.filter(challenge__user=user)
        
        if all_trades.exists():
            insights['total_trades'] = all_trades.count()
            insights['total_volume'] = float(all_trades.aggregate(Sum('lot_size'))['lot_size__sum'] or 0)
            insights['total_pnl'] = float(all_trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0)
            
            winning_trades = all_trades.filter(profit_loss__gt=0)
            insights['overall_win_rate'] = (winning_trades.count() / all_trades.count() * 100) if all_trades.count() > 0 else 0
        
        # Best and worst challenges
        completed = all_challenges.filter(status__in=['passed', 'failed'])
        
        if completed.exists():
            best = completed.order_by('-total_profit_loss').first()
            worst = completed.order_by('total_profit_loss').first()
            
            insights['best_challenge'] = {
                'firm': best.template.get_firm_name_display(),
                'pnl': float(best.total_profit_loss),
                'win_rate': best.win_rate,
                'status': best.status
            }
            
            insights['worst_challenge'] = {
                'firm': worst.template.get_firm_name_display(),
                'pnl': float(worst.total_profit_loss),
                'win_rate': worst.win_rate,
                'status': worst.status
            }
        
        # Favorite firms
        firm_stats = {}
        for challenge in all_challenges:
            firm = challenge.template.get_firm_name_display()
            if firm not in firm_stats:
                firm_stats[firm] = {'attempts': 0, 'passed': 0}
            
            firm_stats[firm]['attempts'] += 1
            if challenge.status == 'passed':
                firm_stats[firm]['passed'] += 1
        
        insights['firm_statistics'] = firm_stats
        
        return {
            'status': 'success',
            **insights
        }
        
    except Exception as e:
        logger.error(f"Challenge insights failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }
