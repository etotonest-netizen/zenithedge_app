"""
Grading System - Evaluates simulation performance
"""
from decimal import Decimal
from typing import Dict
from .nlp_analysis import journal_analyzer


def grade_simulation(sim_run) -> Dict:
    """
    Comprehensive grading of simulation run.
    
    Returns:
        Dict with individual component scores
    """
    # Get grading criteria from scenario
    criteria = sim_run.scenario.grading_criteria
    
    # Grade each component
    technical_score = grade_technical_analysis(sim_run, criteria)
    risk_mgmt_score = grade_risk_management(sim_run, criteria)
    execution_score = grade_execution(sim_run, criteria)
    journaling_score = grade_journaling(sim_run, criteria)
    discipline_score = grade_discipline(sim_run, criteria)
    
    return {
        'technical_score': technical_score,
        'risk_mgmt_score': risk_mgmt_score,
        'execution_score': execution_score,
        'journaling_score': journaling_score,
        'discipline_score': discipline_score,
    }


def grade_technical_analysis(sim_run, criteria: Dict) -> Decimal:
    """Grade technical correctness of trades (0-100)."""
    trades = sim_run.trades.all()
    
    if not trades.exists():
        return Decimal('0')
    
    scores = []
    
    for trade in trades:
        # Check ZenBot score if available
        if trade.zenbot_score:
            scores.append(float(trade.zenbot_score))
        else:
            # Fallback: check against optimal solution
            optimal = sim_run.scenario
            
            # Direction match
            direction_correct = trade.direction == optimal.optimal_direction
            
            # Entry price proximity
            if optimal.optimal_entry_price:
                entry_diff_pct = abs(
                    (trade.entry_price - optimal.optimal_entry_price) / optimal.optimal_entry_price * 100
                )
                # Within 1% is good
                entry_score = max(0, 100 - (entry_diff_pct * 20))
            else:
                entry_score = 50  # Neutral if no optimal
            
            # Combine
            trade_score = (70 if direction_correct else 30) * 0.6 + entry_score * 0.4
            scores.append(trade_score)
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return Decimal(str(round(avg_score, 2)))


def grade_risk_management(sim_run, criteria: Dict) -> Decimal:
    """Grade risk management discipline (0-100)."""
    trades = sim_run.trades.all()
    
    if not trades.exists():
        return Decimal('0')
    
    violations = []
    good_practices = []
    
    max_risk_pct = criteria.get('max_acceptable_risk_per_trade', 2.5)
    min_rr = criteria.get('min_reward_risk_ratio', 1.5)
    
    for trade in trades:
        # Check risk percentage
        if trade.risk_percentage > max_risk_pct:
            violations.append(f"Risk {trade.risk_percentage:.1f}% exceeds {max_risk_pct}%")
        else:
            good_practices.append("Appropriate risk sizing")
        
        # Check reward:risk ratio
        if trade.reward_risk_ratio < min_rr:
            violations.append(f"R:R {trade.reward_risk_ratio:.1f} below {min_rr}")
        else:
            good_practices.append("Good R:R ratio")
        
        # Check stop loss usage
        if not trade.stop_loss:
            violations.append("Missing stop loss")
        else:
            good_practices.append("Stop loss set")
    
    # Calculate score
    total_checks = len(violations) + len(good_practices)
    if total_checks == 0:
        return Decimal('50')
    
    score = (len(good_practices) / total_checks) * 100
    
    return Decimal(str(round(score, 2)))


def grade_execution(sim_run, criteria: Dict) -> Decimal:
    """Grade trade execution quality (0-100)."""
    trades = sim_run.trades.all()
    
    if not trades.exists():
        return Decimal('0')
    
    scores = []
    
    for trade in trades:
        # Check if trade was closed properly
        if trade.status == 'closed':
            # Check if stopped out or target hit
            if trade.exit_price:
                if trade.direction == 'long':
                    hit_stop = trade.exit_price <= trade.stop_loss
                    hit_target = trade.take_profit and trade.exit_price >= trade.take_profit
                else:
                    hit_stop = trade.exit_price >= trade.stop_loss
                    hit_target = trade.take_profit and trade.exit_price <= trade.take_profit
                
                if hit_stop or hit_target:
                    scores.append(100)  # Clean exit
                else:
                    scores.append(70)  # Manual exit (acceptable)
            else:
                scores.append(50)  # Incomplete data
        else:
            scores.append(30)  # Didn't close trade properly
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return Decimal(str(round(avg_score, 2)))


def grade_journaling(sim_run, criteria: Dict) -> Decimal:
    """Grade journal quality (0-100)."""
    journal_entries = sim_run.journal_entries
    
    if not journal_entries:
        return Decimal('0')
    
    # Analyze all entries
    entry_texts = [entry['text'] for entry in journal_entries]
    batch_analysis = journal_analyzer.analyze_batch(entry_texts)
    
    return Decimal(str(round(batch_analysis['avg_quality_score'], 2)))


def grade_discipline(sim_run, criteria: Dict) -> Decimal:
    """Grade overall discipline (0-100)."""
    trades = sim_run.trades.all()
    
    if not trades.exists():
        return Decimal('50')
    
    discipline_score = 100
    
    # Check for revenge trading patterns
    consecutive_losses = 0
    max_consecutive_losses = 0
    
    for trade in trades:
        if trade.was_winner == False:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0
    
    if max_consecutive_losses > criteria.get('max_consecutive_losses_allowed', 3):
        discipline_score -= 20
    
    # Check for oversized positions after losses
    prev_trade = None
    for trade in trades:
        if prev_trade and prev_trade.was_winner == False:
            # Check if increased position size after loss
            if trade.position_size > prev_trade.position_size * 1.5:
                discipline_score -= 15  # Likely revenge trading
        prev_trade = trade
    
    # Check max drawdown adherence
    if sim_run.max_drawdown > sim_run.initial_balance * Decimal('0.10'):  # 10% max
        discipline_score -= 10
    
    # Bonus for consistent risk
    risk_percentages = [float(t.risk_percentage) for t in trades if t.risk_percentage]
    if risk_percentages:
        import statistics
        risk_stdev = statistics.stdev(risk_percentages) if len(risk_percentages) > 1 else 0
        if risk_stdev < 0.5:  # Very consistent
            discipline_score += 10
    
    # Clip to 0-100
    discipline_score = max(0, min(100, discipline_score))
    
    return Decimal(str(round(discipline_score, 2)))
