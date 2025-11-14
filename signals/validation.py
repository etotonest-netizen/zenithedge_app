"""
Signal Validation Pipeline
Processes incoming TradingView alerts through multiple validation filters.
"""
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Signal, SignalEvaluation, PropChallengeConfig, PropChallengeProgress

# Try to import NewsEvent if it exists
try:
    from .models import NewsEvent
    HAS_NEWS_EVENT = True
except ImportError:
    HAS_NEWS_EVENT = False
from bot.score_engine import TradeScorer
import logging

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a single validation check"""
    def __init__(self, passed: bool, reason: str = "", score: int = None):
        self.passed = passed
        self.reason = reason
        self.score = score


class NewsFilter:
    """
    Check if signal is within blackout window of high-impact news event.
    Uses NewsEvent model and user's prop challenge news_blackout_minutes.
    """
    
    def validate(self, signal: Signal) -> ValidationResult:
        try:
            # Get user's prop challenge config for blackout window
            try:
                prop_config = PropChallengeConfig.objects.get(
                    user=signal.user,
                    is_active=True
                )
                blackout_minutes = prop_config.news_blackout_minutes
            except PropChallengeConfig.DoesNotExist:
                # No active prop challenge, use default 30 minutes
                blackout_minutes = 30
            
            if blackout_minutes == 0:
                # News filtering disabled
                return ValidationResult(passed=True)
            
            # Check if NewsEvent model is available
            if not HAS_NEWS_EVENT:
                # NewsEvent model not implemented, skip news filtering
                return ValidationResult(passed=True)
            
            # Check for upcoming high-impact news events
            now = timezone.now()
            blackout_start = now - timedelta(minutes=blackout_minutes)
            blackout_end = now + timedelta(minutes=blackout_minutes)
            
            # Find high-impact news events in blackout window
            news_events = NewsEvent.objects.filter(
                event_time__gte=blackout_start,
                event_time__lte=blackout_end,
                impact='high'
            )
            
            # Check if any event affects this signal's currency
            symbol = signal.symbol.upper()
            for event in news_events:
                # Check if event currency matches signal symbol
                if event.currency in symbol:
                    time_diff = abs((event.event_time - now).total_seconds() / 60)
                    reason = (
                        f"High-impact {event.currency} news event '{event.event_name}' "
                        f"in {int(time_diff)} minutes (blackout: ±{blackout_minutes}min)"
                    )
                    return ValidationResult(passed=False, reason=reason)
            
            return ValidationResult(passed=True)
            
        except Exception as e:
            logger.error(f"NewsFilter error for signal {signal.id}: {e}")
            # On error, allow signal through (fail open)
            return ValidationResult(passed=True, reason=f"News check error: {str(e)}")


class PropRuleFilter:
    """
    Check if signal violates active prop challenge rules.
    Validates max daily loss, max overall loss, trading days, etc.
    """
    
    def validate(self, signal: Signal) -> ValidationResult:
        try:
            # Get active prop challenge config
            try:
                prop_config = PropChallengeConfig.objects.get(
                    user=signal.user,
                    is_active=True
                )
            except PropChallengeConfig.DoesNotExist:
                # No active prop challenge, pass through
                return ValidationResult(passed=True)
            
            # Get current progress
            try:
                progress = PropChallengeProgress.objects.get(challenge=prop_config)
            except PropChallengeProgress.DoesNotExist:
                # No progress yet, pass through
                return ValidationResult(passed=True)
            
            # Check if challenge is failed or completed
            if progress.status == 'failed':
                return ValidationResult(
                    passed=False,
                    reason=f"Prop challenge failed - no new signals allowed"
                )
            
            if progress.status == 'completed':
                # Completed challenges can receive signals
                return ValidationResult(passed=True)
            
            # Check max daily loss limit
            max_daily_loss = prop_config.account_size * (prop_config.max_daily_loss_pct / 100)
            if abs(progress.daily_pnl) >= max_daily_loss and progress.daily_pnl < 0:
                return ValidationResult(
                    passed=False,
                    reason=(
                        f"Daily loss limit reached: "
                        f"${abs(progress.daily_pnl):.2f} / ${max_daily_loss:.2f}"
                    )
                )
            
            # Check max overall loss limit
            max_overall_loss = prop_config.account_size * (prop_config.max_overall_loss_pct / 100)
            if abs(progress.total_pnl) >= max_overall_loss and progress.total_pnl < 0:
                return ValidationResult(
                    passed=False,
                    reason=(
                        f"Overall loss limit reached: "
                        f"${abs(progress.total_pnl):.2f} / ${max_overall_loss:.2f}"
                    )
                )
            
            # Check if approaching daily loss limit (warn at 80%)
            if progress.daily_pnl < 0:
                daily_loss_pct = (abs(progress.daily_pnl) / max_daily_loss) * 100
                if daily_loss_pct >= 80:
                    # Still pass, but log warning
                    logger.warning(
                        f"Signal {signal.id} user {signal.user.email}: "
                        f"Approaching daily loss limit ({daily_loss_pct:.1f}%)"
                    )
            
            return ValidationResult(passed=True)
            
        except Exception as e:
            logger.error(f"PropRuleFilter error for signal {signal.id}: {e}")
            # On error, allow signal through (fail open)
            return ValidationResult(passed=True, reason=f"Prop check error: {str(e)}")


class ZenBotScoreFilter:
    """
    Score signal using TradeScorer AI engine.
    Returns AI score (0-100) and blocks if below minimum threshold.
    """
    
    MIN_SCORE_THRESHOLD = 30  # Signals below this are blocked
    
    def validate(self, signal: Signal) -> ValidationResult:
        try:
            # Initialize TradeScorer
            scorer = TradeScorer(signal.user)
            
            # Score the signal
            score_result = scorer.score_signal(signal)
            ai_score = score_result.get('ai_score', 0)
            
            # Check if score meets minimum threshold
            if ai_score < self.MIN_SCORE_THRESHOLD:
                reason = (
                    f"AI score too low: {ai_score}/100 "
                    f"(minimum: {self.MIN_SCORE_THRESHOLD})"
                )
                return ValidationResult(passed=False, reason=reason, score=ai_score)
            
            # Pass with score
            return ValidationResult(passed=True, score=ai_score)
            
        except Exception as e:
            logger.error(f"ZenBotScoreFilter error for signal {signal.id}: {e}")
            # On error, assign default score and pass through
            return ValidationResult(passed=True, reason=f"Score check error: {str(e)}", score=50)


class StrategyMatchFilter:
    """
    Check if signal's strategy type is allowed in user's preferences.
    Could check against user's StrategyPerformance or custom whitelist.
    """
    
    ALLOWED_STRATEGIES = [
        'Trend Following',
        'Trend',
        'Range Trading',
        'Ranging',
        'Breakout',
        'Reversal',
        'Scalping',
        'Swing',
        'Position',
        'Unknown',  # Allow unknown strategies (legacy signals)
    ]
    
    def validate(self, signal: Signal) -> ValidationResult:
        try:
            # If no strategy specified, pass through
            if not signal.strategy:
                return ValidationResult(passed=True)
            
            strategy = signal.strategy.strip()
            
            # Check if strategy is in allowed list (case-insensitive)
            if any(allowed.lower() in strategy.lower() for allowed in self.ALLOWED_STRATEGIES):
                return ValidationResult(passed=True)
            
            # Strategy not recognized
            reason = f"Strategy '{strategy}' not in allowed list"
            return ValidationResult(passed=False, reason=reason)
            
        except Exception as e:
            logger.error(f"StrategyMatchFilter error for signal {signal.id}: {e}")
            # On error, allow signal through
            return ValidationResult(passed=True, reason=f"Strategy check error: {str(e)}")


class SignalValidationPipeline:
    """
    Orchestrates the validation pipeline for incoming signals.
    Runs all filters in sequence and creates SignalEvaluation record.
    """
    
    def __init__(self):
        self.filters = [
            ('news', NewsFilter()),
            ('prop', PropRuleFilter()),
            ('score', ZenBotScoreFilter()),
            ('strategy', StrategyMatchFilter()),
        ]
    
    def evaluate(self, signal: Signal) -> SignalEvaluation:
        """
        Run signal through all validation filters.
        Creates and returns SignalEvaluation record.
        """
        # Track results
        check_results = {
            'news_check': True,
            'prop_check': True,
            'score_check': True,
            'strategy_check': True,
        }
        final_score = None
        blocked_reasons = []
        evaluation_notes = []
        
        # Run each filter
        for filter_name, filter_instance in self.filters:
            try:
                result = filter_instance.validate(signal)
                
                # Store check result
                check_field = f"{filter_name}_check"
                check_results[check_field] = result.passed
                
                # Store score if provided (from ZenBotScoreFilter)
                if result.score is not None:
                    final_score = result.score
                
                # Track failure reasons
                if not result.passed:
                    blocked_reasons.append(filter_name)
                    evaluation_notes.append(f"❌ {filter_name.upper()}: {result.reason}")
                else:
                    if result.reason:
                        evaluation_notes.append(f"✓ {filter_name.upper()}: {result.reason}")
                
            except Exception as e:
                logger.error(f"Filter {filter_name} error for signal {signal.id}: {e}")
                evaluation_notes.append(f"⚠️ {filter_name.upper()}: Error - {str(e)}")
        
        # Determine overall pass/fail
        passed = all(check_results.values())
        
        # Determine blocked reason
        if passed:
            blocked_reason = 'passed'
        elif len(blocked_reasons) > 1:
            blocked_reason = 'multiple'
        elif blocked_reasons:
            blocked_reason = blocked_reasons[0]
        else:
            blocked_reason = 'manual'
        
        # Create SignalEvaluation record
        evaluation = SignalEvaluation.objects.create(
            signal=signal,
            passed=passed,
            blocked_reason=blocked_reason,
            final_ai_score=final_score,
            news_check=check_results['news_check'],
            prop_check=check_results['prop_check'],
            score_check=check_results['score_check'],
            strategy_check=check_results['strategy_check'],
            evaluation_notes="\n".join(evaluation_notes)
        )
        
        logger.info(
            f"Signal {signal.id} evaluation: "
            f"{'PASSED' if passed else 'BLOCKED'} "
            f"(score: {final_score}, reason: {blocked_reason})"
        )
        
        return evaluation
    
    @classmethod
    def process_signal(cls, signal: Signal) -> SignalEvaluation:
        """
        Convenience method to process a signal through the pipeline.
        """
        pipeline = cls()
        return pipeline.evaluate(signal)
