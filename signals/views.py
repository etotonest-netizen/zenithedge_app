from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import json
import logging

from .models import Signal, StrategyPerformance, check_signal_against_prop, evaluate_risk_controls

logger = logging.getLogger(__name__)
webhook_logger = logging.getLogger('webhook')


def home(request):
    """Home page view"""
    return render(request, 'signals/home.html')


@csrf_exempt
@require_http_methods(["POST"])
def signal_webhook(request):
    """
    Webhook endpoint to receive trading signals from TradingView
    
    API Key can be provided in:
    - Query parameter: ?api_key=xxx
    - Header: X-API-Key: xxx
    - JSON body: "api_key": "xxx"
    
    Expected JSON payload:
    {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "side": "buy" or "sell",
        "sl": 50000.50,
        "tp": 52000.00,
        "confidence": 85.5,
        "strategy": "ZenithEdge",
        "regime": "Trend",
        "price": 51000.00,  # optional
        "timestamp": "2025-11-09T10:30:00Z",  # optional
        "api_key": "xxx"  # optional
    }
    
    Returns:
    {"status": "received", "allowed": true/false}
    """
    # Log incoming webhook request
    webhook_logger.info(f"Webhook received: IP={request.META.get('REMOTE_ADDR')}, User-Agent={request.headers.get('User-Agent', 'N/A')}")
    webhook_logger.debug(f"Raw body: {request.body.decode('utf-8', errors='ignore')[:500]}")
    
    try:
        # Get API key from various sources
        api_key = (
            request.GET.get('api_key') or
            request.headers.get('X-API-Key') or
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
        # Parse JSON payload
        try:
            data = json.loads(request.body)
            webhook_logger.info(f"Parsed JSON: {json.dumps(data, indent=2)}")
            # API key can also be in JSON body
            if not api_key and 'api_key' in data:
                api_key = data.pop('api_key')
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON format"
            }, status=400)
        
        # Authenticate user via API key
        user = None
        if api_key:
            try:
                from accounts.models import CustomUser
                user = CustomUser.objects.get(api_key=api_key, is_active=True)
                logger.info(f"Signal authenticated for user: {user.email}")
            except CustomUser.DoesNotExist:
                logger.warning(f"Invalid API key provided: {api_key[:10]}...")
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid or inactive API key"
                }, status=401)
        
        # Define required fields
        required_fields = ['symbol', 'timeframe', 'side', 'sl', 'tp', 'confidence', 'strategy', 'regime']
        
        # Validate required fields are present
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return JsonResponse({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }, status=400)
        
        # Validate field types and values
        errors = []
        
        # Validate symbol
        symbol = str(data['symbol']).strip()
        if not symbol or len(symbol) > 20:
            errors.append("symbol must be a non-empty string (max 20 characters)")
        
        # Validate timeframe
        timeframe = str(data['timeframe']).strip()
        if not timeframe or len(timeframe) > 10:
            errors.append("timeframe must be a non-empty string (max 10 characters)")
        
        # Validate side
        side = str(data['side']).strip().lower()
        if side not in ['buy', 'sell']:
            errors.append("side must be 'buy' or 'sell'")
        
        # Validate sl (stop loss)
        try:
            sl = Decimal(str(data['sl']))
            if sl <= 0:
                errors.append("sl must be greater than 0")
        except (InvalidOperation, ValueError, TypeError):
            errors.append("sl must be a valid number")
            sl = None
        
        # Validate tp (take profit)
        try:
            tp = Decimal(str(data['tp']))
            if tp <= 0:
                errors.append("tp must be greater than 0")
        except (InvalidOperation, ValueError, TypeError):
            errors.append("tp must be a valid number")
            tp = None
        
        # Validate confidence
        try:
            confidence = float(data['confidence'])
            if not (0 <= confidence <= 100):
                errors.append("confidence must be between 0 and 100")
        except (ValueError, TypeError):
            errors.append("confidence must be a valid number")
            confidence = None
        
        # Validate strategy
        strategy = str(data['strategy']).strip()
        if not strategy or len(strategy) > 50:
            errors.append("strategy must be a non-empty string (max 50 characters)")
        
        # Validate regime
        regime = str(data['regime']).strip()
        valid_regimes = ['Trend', 'Breakout', 'MeanReversion', 'Squeeze']
        if regime not in valid_regimes:
            errors.append(f"regime must be one of: {', '.join(valid_regimes)}")
        
        # Validate optional price field
        price = None
        if 'price' in data and data['price'] is not None:
            try:
                price = Decimal(str(data['price']))
                if price <= 0:
                    errors.append("price must be greater than 0")
            except (InvalidOperation, ValueError, TypeError):
                errors.append("price must be a valid number")
        
        # Get optional timestamp
        timestamp = data.get('timestamp', None)
        if timestamp:
            timestamp = str(timestamp).strip()[:100]
        
        # If there are validation errors, return them
        if errors:
            logger.warning(f"Validation errors: {errors}")
            return JsonResponse({
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }, status=400)
        
        # ========================================
        # AI VALIDATION LAYER (TRUTH FILTER)
        # ========================================
        # Import validation modules
        from zenbot.validation_engine import validate_signal
        from zenbot.contextualizer_v2 import generate_narrative
        
        # Prepare signal data for validation
        signal_data_for_validation = {
            'symbol': symbol,
            'side': side,
            'strategy': strategy,
            'confidence': confidence,
            'price': float(price) if price else 0,
            'sl': float(sl),
            'tp': float(tp),
            'regime': regime.lower(),
            'timeframe': timeframe
        }
        
        # Run AI validation
        validation_result = validate_signal(signal_data_for_validation)
        truth_index = validation_result.get('truth_index', 0)
        validation_status = validation_result.get('status', 'rejected')
        
        logger.info(f"AI Validation: Truth Index={truth_index:.1f}, Status={validation_status}")
        
        # Block signals with Truth Index < 60 (rejected)
        if validation_status == 'rejected':
            logger.warning(f"Signal REJECTED by AI validation (Truth Index: {truth_index:.1f})")
            return JsonResponse({
                "status": "rejected",
                "reason": "ai_validation_failed",
                "truth_index": float(truth_index),
                "validation_notes": validation_result.get('validation_notes', []),
                "recommendation": validation_result.get('recommendation', 'Signal does not meet quality threshold')
            }, status=200)  # 200 OK but signal rejected
        
        # Generate human-readable narrative context with KB v2.0 (get rich data)
        narrative_result = generate_narrative(
            signal_data_for_validation, 
            validation_result,
            return_metadata=True  # Get narrative + quality metrics + KB trace
        )
        # Use composed_narrative for cards (pure 2-4 sentences), full narrative for logs
        # Handle both dict and string returns (fallback compatibility)
        if isinstance(narrative_result, dict):
            context_narrative = narrative_result.get('composed_narrative', narrative_result.get('narrative', 'AI narrative generation in progress'))
            quality_metrics = narrative_result.get('quality_metrics', {})
            kb_concepts_used = narrative_result.get('kb_concepts_used', 0)
        else:
            # Fallback to v1.0 string return
            context_narrative = str(narrative_result)
            quality_metrics = {}
            kb_concepts_used = 0
        
        logger.info(
            f"Generated KB-powered narrative for {symbol} "
            f"(Concepts: {kb_concepts_used}, Uniqueness: {quality_metrics.get('linguistic_uniqueness', 0)}%)"
        )
        
        # Check risk controls first (if user authenticated)
        risk_control = None
        is_risk_blocked = False
        if user:
            risk_check_result = evaluate_risk_controls(user)
            if risk_check_result['blocked']:
                is_risk_blocked = True
                is_allowed = False
                rejection_reason = f"risk_control: {risk_check_result['reason']}"
                risk_control = risk_check_result['risk_control']
                logger.warning(f"Signal blocked by risk controls: {risk_check_result['reason']}")
        
        # Check signal against prop rules (if not already blocked by risk controls)
        prop_rule = None
        if not is_risk_blocked:
            prop_check_result = check_signal_against_prop({
                'symbol': symbol,
                'timeframe': timeframe,
                'side': side,
                'confidence': confidence,
                'strategy': strategy,
                'regime': regime
            })
            
            is_allowed = prop_check_result['allowed']
            rejection_reason = prop_check_result['reason']
            prop_rule = prop_check_result['prop_rule']
        
        # Create the signal first (to auto-detect session)
        try:
            signal = Signal(
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                sl=sl,
                tp=tp,
                confidence=confidence,
                strategy=strategy,
                regime=regime,
                price=price,
                timestamp=timestamp,
                user=user,
                is_allowed=is_allowed,
                rejection_reason=rejection_reason,
                prop_rule_checked=prop_rule,
                is_risk_blocked=is_risk_blocked,
                risk_control_checked=risk_control
            )
            # Save to trigger session auto-detection
            signal.save()
            
            # Fetch recent news for this symbol to add to quality_metrics
            news_context = None
            try:
                from zennews.models import NewsEvent
                cutoff_time = timezone.now() - timedelta(hours=12)
                recent_news = NewsEvent.objects.filter(
                    symbol__iexact=signal.symbol,
                    timestamp__gte=cutoff_time
                ).order_by('-timestamp')[:3]
                
                if recent_news.exists():
                    news_items = []
                    for news in recent_news:
                        news_items.append(f"{news.get_time_ago()}: {news.headline}")
                    news_context = " | ".join(news_items)
                    logger.info(f"Fetched {len(news_items)} news items for {signal.symbol}")
                else:
                    logger.info(f"No recent news found for {signal.symbol} in last 12 hours")
            except Exception as e:
                logger.error(f"Failed to fetch news context for {signal.symbol}: {e}")
            
            # Add news_context to quality_metrics if available
            if news_context:
                quality_metrics['news_context'] = news_context
            
            # Store AI validation results in database
            from .models import TradeValidation
            try:
                trade_validation = TradeValidation.objects.create(
                    signal=signal,
                    truth_index=truth_index,
                    status=validation_status,
                    breakdown=validation_result.get('breakdown', {}),
                    validation_notes=validation_result.get('validation_notes', []),
                    context_summary=context_narrative,
                    recommendation=validation_result.get('recommendation', ''),
                    accuracy_history={},  # Will be updated as outcomes are tracked
                    quality_metrics=quality_metrics,  # Narrative quality metrics (now includes news_context)
                    kb_concepts_used=kb_concepts_used  # Number of KB concepts used
                )
                logger.info(
                    f"Validation record created: ID={trade_validation.id} "
                    f"(Uniqueness: {quality_metrics.get('linguistic_uniqueness', 0)}%)"
                )
            except Exception as e:
                logger.error(f"Failed to save validation record: {e}")
                # Don't fail the entire request if validation storage fails
            
            # Check session rules if user is authenticated
            if user and signal.session:
                from .models import SessionRule
                try:
                    session_rule = SessionRule.objects.get(user=user, session=signal.session)
                    
                    # Check if session is blocked
                    if session_rule.is_blocked:
                        signal.is_allowed = False
                        signal.rejection_reason = f"session_block: {signal.session} session is blocked by user settings"
                        signal.save()
                        is_allowed = False
                        rejection_reason = signal.rejection_reason
                        logger.warning(f"Signal blocked by session rule: {signal} - {rejection_reason}")
                    
                except SessionRule.DoesNotExist:
                    # No session rule defined for this session, keep original allowed status
                    pass
            
            if is_allowed:
                logger.info(f"Signal received and ALLOWED: {signal}")
            else:
                logger.warning(f"Signal received but REJECTED: {signal} - Reason: {rejection_reason}")
            
            return JsonResponse({
                "status": "received",
                "signal_id": signal.id,
                "allowed": is_allowed,
                "reason": rejection_reason,
                "ai_validation": {
                    "truth_index": float(truth_index),
                    "status": validation_status,
                    "quality_label": "High Confidence" if truth_index >= 85 else "Solid" if truth_index >= 75 else "Moderate" if truth_index >= 65 else "Conditional",
                    "context_summary": context_narrative
                }
            }, status=201)
            
        except ValidationError as e:
            logger.error(f"Database validation error: {e}")
            return JsonResponse({
                "status": "error",
                "message": "Database validation failed",
                "errors": str(e)
            }, status=400)
        
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return JsonResponse({
                "status": "error",
                "message": "Failed to save signal"
            }, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error in signal_webhook: {e}")
        return JsonResponse({
            "status": "error",
            "message": "Internal server error"
        }, status=500)


class DashboardView(LoginRequiredMixin, ListView):
    """
    Dashboard view to display all trading signals with role-based filtering
    """
    model = Signal
    template_name = 'signals/dashboard.html'
    context_object_name = 'signals'
    paginate_by = 50
    ordering = ['-received_at']
    login_url = '/accounts/login/'
    
    def get_queryset(self):
        """Filter signals based on user role and query parameters"""
        queryset = super().get_queryset()
        
        # Role-based filtering
        # Admins see all signals, traders only see their own
        if not (self.request.user.is_admin or self.request.user.is_superuser):
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by status (allowed/rejected)
        status = self.request.GET.get('status')
        if status == 'allowed':
            queryset = queryset.filter(is_allowed=True)
        elif status == 'rejected':
            queryset = queryset.filter(is_allowed=False)
        
        # Filter by side (buy/sell)
        side = self.request.GET.get('side')
        if side in ['buy', 'sell']:
            queryset = queryset.filter(side=side)
        
        # Filter by regime
        regime = self.request.GET.get('regime')
        if regime in ['Trend', 'Breakout', 'MeanReversion', 'Squeeze']:
            queryset = queryset.filter(regime=regime)
        
        # Filter by symbol
        symbol = self.request.GET.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol__icontains=symbol.strip())
        
        # Filter by strategy
        strategy = self.request.GET.get('strategy')
        if strategy:
            queryset = queryset.filter(strategy=strategy.strip())
        
        # Filter by minimum AI score
        min_score = self.request.GET.get('min_score')
        if min_score:
            try:
                min_score_int = int(min_score)
                if min_score_int > 0:  # Only filter if > 0
                    queryset = queryset.filter(ai_score__ai_score__gte=min_score_int)
            except (ValueError, TypeError):
                pass  # Invalid min_score, skip filter
        
        # Filter by evaluation status (default: show only passed signals)
        view_mode = self.request.GET.get('view', 'live')
        eval_status_filters = self.request.GET.getlist('eval_status')
        
        if eval_status_filters:
            # Custom filter based on checkboxes
            from django.db.models import Q
            eval_query = Q()
            
            if 'passed' in eval_status_filters:
                eval_query |= Q(evaluation__passed=True, evaluation__is_overridden=False)
            if 'blocked' in eval_status_filters:
                eval_query |= Q(evaluation__passed=False, evaluation__is_overridden=False)
            if 'overridden' in eval_status_filters:
                eval_query |= Q(evaluation__is_overridden=True)
            
            queryset = queryset.filter(eval_query)
        elif view_mode == 'archive':
            # Show blocked signals in archive view
            queryset = queryset.filter(evaluation__passed=False)
        else:
            # Show only passed signals in live view (default)
            queryset = queryset.filter(evaluation__passed=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add statistics to context"""
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics
        all_signals = Signal.objects.all()
        context['total_signals'] = all_signals.count()
        context['allowed_signals'] = all_signals.filter(is_allowed=True).count()
        context['rejected_signals'] = all_signals.filter(is_allowed=False).count()
        
        # Evaluation statistics
        from .models import SignalEvaluation
        context['passed_signals'] = SignalEvaluation.objects.filter(passed=True).count()
        context['blocked_signals'] = SignalEvaluation.objects.filter(passed=False).count()
        
        # Current view mode
        context['view_mode'] = self.request.GET.get('view', 'live')
        
        # Add prop challenge safety status and full progress
        from signals.models import PropChallengeProgress
        try:
            prop_progress = PropChallengeProgress.objects.filter(
                user=self.request.user, 
                status='active'
            ).select_related('challenge').first()
            if prop_progress:
                context['prop_progress'] = prop_progress
        except Exception as e:
            context['prop_progress'] = None

        
        # Calculate average confidence
        avg_conf = all_signals.aggregate(avg_conf=Avg('confidence'))['avg_conf']
        context['avg_confidence'] = avg_conf if avg_conf is not None else 0
        
        # Get all unique strategies for filter dropdown
        all_strategies = Signal.objects.values_list('strategy', flat=True).distinct().order_by('strategy')
        context['all_strategies'] = list(all_strategies)
        
        # Check risk control status
        from .models import RiskControl
        try:
            risk_control = RiskControl.objects.filter(
                user=self.request.user,
                is_active=True
            ).first()
            
            if risk_control and risk_control.is_halted:
                context['risk_halted'] = True
                context['risk_halt_reason'] = risk_control.halt_reason
                context['risk_halt_time'] = risk_control.halt_triggered_at
            else:
                context['risk_halted'] = False
        except Exception:
            context['risk_halted'] = False
        
        return context


class StrategyPerformanceView(LoginRequiredMixin, ListView):
    """
    View to display strategy performance metrics with charts and filtering
    """
    model = StrategyPerformance
    template_name = 'signals/strategies.html'
    context_object_name = 'performances'
    paginate_by = 20
    
    def get_queryset(self):
        """Get performance records filtered by user role and request parameters"""
        queryset = StrategyPerformance.objects.all()
        
        # Role-based filtering
        if not self.request.user.is_admin and not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by strategy
        strategy = self.request.GET.get('strategy')
        if strategy:
            queryset = queryset.filter(strategy_name__icontains=strategy.strip())
        
        # Filter by regime
        regime = self.request.GET.get('regime')
        if regime and regime != 'all':
            queryset = queryset.filter(regime=regime)
        
        # Filter by symbol
        symbol = self.request.GET.get('symbol')
        if symbol and symbol != 'all':
            queryset = queryset.filter(symbol__icontains=symbol.strip())
        
        # Filter by timeframe
        timeframe = self.request.GET.get('timeframe')
        if timeframe and timeframe != 'all':
            queryset = queryset.filter(timeframe=timeframe)
        
        # Filter by profitability
        profitable = self.request.GET.get('profitable')
        if profitable == 'yes':
            queryset = queryset.filter(total_pnl__gt=0)
        elif profitable == 'no':
            queryset = queryset.filter(total_pnl__lte=0)
        
        # Filter by minimum trades
        min_trades = self.request.GET.get('min_trades', 5)
        try:
            min_trades = int(min_trades)
            queryset = queryset.filter(total_trades__gte=min_trades)
        except (ValueError, TypeError):
            queryset = queryset.filter(total_trades__gte=5)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-win_rate')
        valid_sorts = ['win_rate', '-win_rate', 'total_trades', '-total_trades', 
                      'avg_rr', '-avg_rr', 'profit_factor', '-profit_factor',
                      'total_pnl', '-total_pnl']
        if sort_by in valid_sorts:
            queryset = queryset.order_by(sort_by, '-total_trades')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add charts data and statistics to context"""
        context = super().get_context_data(**kwargs)
        
        # Get all performances for the user (respecting filters)
        all_performances = self.get_queryset()
        
        # Calculate overall statistics
        context['total_strategies'] = all_performances.count()
        context['profitable_strategies'] = all_performances.filter(total_pnl__gt=0).count()
        
        total_trades_sum = all_performances.aggregate(Sum('total_trades'))['total_trades__sum'] or 0
        context['total_trades_analyzed'] = total_trades_sum
        
        avg_win_rate = all_performances.aggregate(Avg('win_rate'))['win_rate__avg']
        context['avg_win_rate'] = avg_win_rate if avg_win_rate is not None else 0
        
        # Get top performer (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_performances = all_performances.filter(
            last_updated__gte=thirty_days_ago,
            total_trades__gte=5
        ).order_by('-win_rate', '-profit_factor')
        
        context['top_performer'] = recent_performances.first() if recent_performances.exists() else None
        
        # Get available filter options
        context['available_regimes'] = ['Trend', 'Breakout', 'MeanReversion', 'Squeeze']
        context['available_timeframes'] = Signal.objects.values_list('timeframe', flat=True).distinct()
        context['available_symbols'] = Signal.objects.values_list('symbol', flat=True).distinct()
        
        # Prepare chart data
        chart_performances = all_performances[:10]  # Top 10 for charts
        
        context['chart_labels'] = []
        context['chart_win_rates'] = []
        context['chart_rr_ratios'] = []
        context['chart_profit_factors'] = []
        context['chart_total_trades'] = []
        
        for perf in chart_performances:
            label = f"{perf.strategy_name}"
            if perf.regime:
                label += f" ({perf.regime})"
            if perf.symbol:
                label += f" - {perf.symbol}"
            
            context['chart_labels'].append(label)
            context['chart_win_rates'].append(float(perf.win_rate))
            context['chart_rr_ratios'].append(float(perf.avg_rr))
            context['chart_profit_factors'].append(float(perf.profit_factor))
            context['chart_total_trades'].append(perf.total_trades)
        
        # Current filters for template
        context['current_strategy'] = self.request.GET.get('strategy', '')
        context['current_regime'] = self.request.GET.get('regime', 'all')
        context['current_symbol'] = self.request.GET.get('symbol', 'all')
        context['current_timeframe'] = self.request.GET.get('timeframe', 'all')
        context['current_profitable'] = self.request.GET.get('profitable', 'all')
        context['current_min_trades'] = self.request.GET.get('min_trades', '5')
        context['current_sort'] = self.request.GET.get('sort', '-win_rate')
        
        return context


class JournalListView(LoginRequiredMixin, ListView):
    """View to display list of trade journal entries"""
    model = None  # Will be imported below
    template_name = 'signals/journal_list.html'
    context_object_name = 'entries'
    paginate_by = 20
    
    def get_queryset(self):
        from .models import TradeJournalEntry
        
        # Base queryset filtered by user
        qs = TradeJournalEntry.objects.filter(user=self.request.user)
        
        # Apply filters from query parameters
        outcome = self.request.GET.get('outcome')
        if outcome:
            qs = qs.filter(outcome=outcome)
        
        decision = self.request.GET.get('decision')
        if decision:
            qs = qs.filter(decision=decision)
        
        symbol = self.request.GET.get('symbol')
        if symbol:
            qs = qs.filter(signal__symbol__icontains=symbol)
        
        strategy = self.request.GET.get('strategy')
        if strategy:
            qs = qs.filter(signal__strategy__icontains=strategy)
        
        session = self.request.GET.get('session')
        if session:
            qs = qs.filter(signal__session=session)
        
        return qs.select_related('signal', 'user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        from .models import TradeJournalEntry, summarize_journal
        
        context = super().get_context_data(**kwargs)
        
        # Add filter values to context
        context['filter_outcome'] = self.request.GET.get('outcome', '')
        context['filter_decision'] = self.request.GET.get('decision', '')
        context['filter_symbol'] = self.request.GET.get('symbol', '')
        context['filter_strategy'] = self.request.GET.get('strategy', '')
        context['filter_session'] = self.request.GET.get('session', '')
        
        # Add choice lists for filters
        context['outcome_choices'] = TradeJournalEntry.OUTCOME_CHOICES
        context['decision_choices'] = TradeJournalEntry.DECISION_CHOICES
        context['session_choices'] = [
            ('Asia', 'Asia Session'),
            ('London', 'London Session'),
            ('New York', 'New York Session'),
        ]
        
        # Add journal summary statistics
        context['summary'] = summarize_journal(self.request.user)
        
        return context


class JournalDetailView(LoginRequiredMixin, TemplateView):
    """View to display a single journal entry with detailed analysis"""
    template_name = 'signals/journal_detail.html'
    
    def get_context_data(self, **kwargs):
        from .models import TradeJournalEntry
        
        context = super().get_context_data(**kwargs)
        entry_id = kwargs.get('pk')
        
        try:
            entry = TradeJournalEntry.objects.select_related('signal', 'user').get(
                id=entry_id,
                user=self.request.user
            )
            context['entry'] = entry
        except TradeJournalEntry.DoesNotExist:
            context['error'] = 'Journal entry not found or access denied'
        
        return context


@login_required
def journal_summary_api(request):
    """API endpoint to get journal summary statistics"""
    from .models import summarize_journal
    
    summary = summarize_journal(request.user)
    return JsonResponse(summary)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def journal_ai_review(request):
    """
    AI-powered journal review endpoint (optional - requires OpenAI API key).
    Analyzes journal entries and provides insights.
    """
    try:
        # Parse request body
        data = json.loads(request.body.decode('utf-8'))
        entry_ids = data.get('entry_ids', [])
        
        from .models import TradeJournalEntry, summarize_journal
        
        # Get entries
        if entry_ids:
            entries = TradeJournalEntry.objects.filter(
                user=request.user,
                id__in=entry_ids
            ).select_related('signal')
        else:
            # Get last 20 entries if no specific IDs provided
            entries = TradeJournalEntry.objects.filter(
                user=request.user
            ).select_related('signal').order_by('-created_at')[:20]
        
        if not entries.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'No journal entries found'
            }, status=404)
        
        # Get summary statistics
        summary = summarize_journal(request.user)
        
        # Prepare analysis text
        analysis_parts = []
        analysis_parts.append(f"Journal Summary for {request.user.email}")
        analysis_parts.append(f"Total Entries: {summary.get('total_entries', 0)}")
        analysis_parts.append(f"Win Rate: {summary.get('win_rate', 0)}%")
        analysis_parts.append(f"Average Pips: {summary.get('avg_pips', 0)}")
        analysis_parts.append(f"Average R:R: {summary.get('avg_rr', 0)}")
        
        if summary.get('best_strategy', {}).get('name'):
            analysis_parts.append(f"Best Strategy: {summary['best_strategy']['name']} ({summary['best_strategy']['win_rate']}% WR)")
        
        if summary.get('best_session', {}).get('name'):
            analysis_parts.append(f"Best Session: {summary['best_session']['name']} ({summary['best_session']['win_rate']}% WR)")
        
        if summary.get('best_regime', {}).get('name'):
            analysis_parts.append(f"Best Regime: {summary['best_regime']['name']} ({summary['best_regime']['win_rate']}% WR)")
        
        analysis_parts.append("\nKey Observations:")
        
        # Add insights based on data
        if summary.get('win_rate', 0) < 50:
            analysis_parts.append("- Your win rate is below 50%. Consider reviewing your entry criteria and risk management.")
        elif summary.get('win_rate', 0) > 60:
            analysis_parts.append("- Excellent win rate! You're demonstrating strong trade selection.")
        
        if summary.get('avg_rr', 0) < 1.5:
            analysis_parts.append("- Your average R:R is below 1.5. Aim for higher reward relative to risk.")
        elif summary.get('avg_rr', 0) > 2.0:
            analysis_parts.append("- Strong risk-reward management! Keep maintaining this discipline.")
        
        if summary.get('skipped_trades', 0) > summary.get('took_trades', 0):
            analysis_parts.append("- You're skipping more trades than you take. This shows discipline, but ensure you're not missing good opportunities.")
        
        # Check for consistency across sessions
        session_breakdown = summary.get('session_breakdown', {})
        if len(session_breakdown) > 1:
            analysis_parts.append(f"- You're trading across {len(session_breakdown)} different sessions. Focus on your most profitable session.")
        
        # Recent entries analysis
        analysis_parts.append("\nRecent Entries:")
        for entry in entries[:5]:
            signal_info = f" ({entry.signal.symbol} {entry.signal.side})" if entry.signal else ""
            pips_info = f" {entry.pips} pips" if entry.pips else ""
            analysis_parts.append(f"- {entry.get_decision_display()}: {entry.get_outcome_display()}{signal_info}{pips_info}")
        
        analysis_text = "\n".join(analysis_parts)
        
        # Note: This is a basic analysis. For AI-powered insights using OpenAI:
        # 1. Set OPENAI_API_KEY in environment
        # 2. Install openai package: pip install openai
        # 3. Uncomment the code below:
        
        # import os
        # import openai
        # openai.api_key = os.environ.get('OPENAI_API_KEY')
        # 
        # if openai.api_key:
        #     try:
        #         response = openai.ChatCompletion.create(
        #             model="gpt-4",
        #             messages=[
        #                 {"role": "system", "content": "You are a professional trading coach analyzing a trader's journal."},
        #                 {"role": "user", "content": f"Analyze this trading journal and provide actionable insights:\n\n{analysis_text}"}
        #             ]
        #         )
        #         ai_insights = response.choices[0].message.content
        #         analysis_text += f"\n\nAI Insights:\n{ai_insights}"
        #     except Exception as e:
        #         logger.error(f"OpenAI API error: {e}")
        
        return JsonResponse({
            'status': 'success',
            'analysis': analysis_text,
            'summary': summary,
            'entries_analyzed': entries.count()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Journal AI review error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


class TradeReplayView(TemplateView):
    """View to replay a trade with candle-by-candle visualization"""
    template_name = 'signals/trade_replay.html'
    
    def get_context_data(self, **kwargs):
        from .models import Signal, fetch_chart_snapshot
        
        context = super().get_context_data(**kwargs)
        signal_id = kwargs.get('pk')
        
        try:
            signal = Signal.objects.get(id=signal_id)
            
            # Generate replay data if not exists
            if not signal.replay_data:
                fetch_chart_snapshot(signal, bars_before=50, bars_after=30)
                signal.refresh_from_db()
            
            context['signal'] = signal
            context['replay_data'] = signal.replay_data
            context['entry_bar_index'] = signal.entry_bar_index
            context['exit_bar_index'] = signal.exit_bar_index
            context['exit_reason'] = signal.exit_reason
            
        except Signal.DoesNotExist:
            context['error'] = 'Signal not found or access denied'
        
        return context


@login_required
def generate_replay_data(request, signal_id):
    """API endpoint to generate/regenerate replay data for a signal"""
    from .models import Signal, fetch_chart_snapshot
    
    try:
        signal = Signal.objects.get(id=signal_id, user=request.user)
        
        # Generate replay data
        result = fetch_chart_snapshot(signal, bars_before=50, bars_after=30)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Replay data generated successfully',
            'entry_bar_index': result['entry_bar_index'],
            'exit_bar_index': result['exit_bar_index'],
            'exit_reason': result['exit_reason'],
            'total_bars': len(result['bars'])
        })
        
    except Signal.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Signal not found or access denied'
        }, status=404)
    except Exception as e:
        logger.error(f"Error generating replay data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# ==================== PROP CHALLENGE VIEWS ====================

class ChallengeSetupView(LoginRequiredMixin, TemplateView):
    """View to setup prop firm challenge configuration"""
    template_name = 'signals/challenge_setup.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        from .models import PropChallengeConfig, PropChallengeProgress
        
        context = super().get_context_data(**kwargs)
        
        # Get user's active challenge if exists
        try:
            challenge = PropChallengeConfig.objects.get(user=self.request.user, is_active=True)
            context['challenge'] = challenge
            context['has_active_challenge'] = True
            
            # Get progress
            try:
                progress = challenge.progress
                context['progress'] = progress
            except PropChallengeProgress.DoesNotExist:
                pass
                
        except PropChallengeConfig.DoesNotExist:
            context['has_active_challenge'] = False
        
        # Get firm presets for JavaScript
        context['firm_presets'] = {
            'ftmo': PropChallengeConfig.get_firm_presets('ftmo'),
            'funding_pips': PropChallengeConfig.get_firm_presets('funding_pips'),
            'myforexfunds': PropChallengeConfig.get_firm_presets('myforexfunds'),
            'the5ers': PropChallengeConfig.get_firm_presets('the5ers'),
            'topstep': PropChallengeConfig.get_firm_presets('topstep'),
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .models import PropChallengeConfig, PropChallengeProgress
        import json
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create':
                # Deactivate any existing challenges
                PropChallengeConfig.objects.filter(user=request.user, is_active=True).update(is_active=False)
                
                # Create new challenge
                challenge = PropChallengeConfig.objects.create(
                    user=request.user,
                    firm_name=data.get('firm_name', 'ftmo'),
                    account_size=int(data.get('account_size', 10000)),
                    max_daily_loss_pct=float(data.get('max_daily_loss_pct', 5.0)),
                    max_overall_loss_pct=float(data.get('max_overall_loss_pct', 10.0)),
                    min_trading_days=int(data.get('min_trading_days', 5)),
                    profit_target_pct=float(data.get('profit_target_pct', 10.0)),
                    news_blackout_minutes=int(data.get('news_blackout_minutes', 2)),
                    leverage=int(data.get('leverage', 100)),
                    is_active=True
                )
                
                # Create progress tracker
                PropChallengeProgress.objects.create(
                    challenge=challenge,
                    peak_balance=challenge.account_size,
                    status='active'
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'{challenge.get_firm_name_display()} challenge created successfully!',
                    'challenge_id': challenge.id
                })
            
            elif action == 'deactivate':
                PropChallengeConfig.objects.filter(user=request.user, is_active=True).update(is_active=False)
                return JsonResponse({'status': 'success', 'message': 'Challenge deactivated'})
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class ChallengeOverviewView(LoginRequiredMixin, TemplateView):
    """View to display prop challenge progress and status"""
    template_name = 'signals/challenge_overview.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        from .models import PropChallengeConfig, PropChallengeProgress
        
        context = super().get_context_data(**kwargs)
        
        try:
            challenge = PropChallengeConfig.objects.get(user=self.request.user, is_active=True)
            progress = challenge.progress
            
            context['challenge'] = challenge
            context['progress'] = progress
            context['has_challenge'] = True
            
            # Calculate metrics
            context['current_balance'] = progress.get_current_balance()
            context['daily_loss_remaining'] = progress.get_daily_loss_remaining()
            context['overall_loss_remaining'] = progress.get_overall_loss_remaining()
            context['profit_progress_pct'] = progress.get_profit_progress_pct()
            context['days_remaining'] = progress.get_days_remaining()
            context['status_indicator'] = progress.get_status_indicator()
            
            # Checklist items
            context['checklist'] = {
                'daily_loss_ok': progress.check_daily_loss_limit(),
                'overall_loss_ok': progress.check_overall_loss_limit(),
                'profit_target_met': float(progress.total_pnl) >= challenge.get_profit_target_amount(),
                'min_days_met': progress.trading_days >= challenge.min_trading_days,
                'no_violations': progress.daily_loss_violations == 0 and progress.overall_loss_violations == 0,
            }
            
            # Win rate
            if progress.total_trades > 0:
                context['win_rate'] = (progress.winning_trades / progress.total_trades) * 100
            else:
                context['win_rate'] = 0
            
        except (PropChallengeConfig.DoesNotExist, PropChallengeProgress.DoesNotExist):
            context['has_challenge'] = False
        
        return context



# =============================================================================
# Webhook Setup Wizard View
# =============================================================================

class WebhookSetupView(LoginRequiredMixin, TemplateView):
    """
    Webhook wizard to help users connect TradingView alerts.
    Generates unique UUID-based webhook URLs and provides setup instructions.
    """
    template_name = 'signals/webhook_setup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .models import WebhookConfig, Signal
        
        # Get or create webhook config for user
        webhook_config, created = WebhookConfig.objects.get_or_create(
            user=self.request.user
        )
        
        # Generate webhook URL if not set
        if not webhook_config.webhook_url or created:
            # Get base URL from request
            scheme = 'https' if self.request.is_secure() else 'http'
            host = self.request.get_host()
            base_url = f"{scheme}://{host}"
            webhook_config.generate_webhook_url(base_url)
            webhook_config.save()
        
        context['webhook_config'] = webhook_config
        context['webhook_url'] = webhook_config.webhook_url
        context['webhook_uuid'] = str(webhook_config.webhook_uuid)
        
        # Calculate stats
        total_signals = Signal.objects.filter(user=self.request.user).count()
        context['total_signals'] = total_signals
        context['webhook_signals'] = webhook_config.signal_count
        context['last_signal'] = webhook_config.last_signal_at
        
        # TradingView JSON template
        context['tv_json_template'] = '''{
  "user_uuid": "%s",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Trend"
}''' % str(webhook_config.webhook_uuid)
        
        # Alternative templates for different regimes
        context['tv_json_templates'] = {
            'trend': '''{
  "user_uuid": "%s",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Trend"
}''' % str(webhook_config.webhook_uuid),
            'breakout': '''{
  "user_uuid": "%s",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Breakout"
}''' % str(webhook_config.webhook_uuid),
            'meanreversion': '''{
  "user_uuid": "%s",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "MeanReversion"
}''' % str(webhook_config.webhook_uuid),
            'squeeze': '''{
  "user_uuid": "%s",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "price": {{close}},
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Squeeze"
}''' % str(webhook_config.webhook_uuid)
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle webhook regeneration"""
        from .models import WebhookConfig
        import json
        
        action = request.POST.get('action')
        
        if action == 'regenerate':
            try:
                webhook_config = WebhookConfig.objects.get(user=request.user)
                webhook_config.regenerate_uuid()
                
                # Get base URL from request
                scheme = 'https' if request.is_secure() else 'http'
                host = request.get_host()
                base_url = f"{scheme}://{host}"
                webhook_config.generate_webhook_url(base_url)
                webhook_config.save()
                
                return JsonResponse({
                    'status': 'success',
                    'webhook_url': webhook_config.webhook_url,
                    'webhook_uuid': str(webhook_config.webhook_uuid)
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
        
        elif action == 'toggle_active':
            try:
                webhook_config = WebhookConfig.objects.get(user=request.user)
                webhook_config.is_active = not webhook_config.is_active
                webhook_config.save()
                
                return JsonResponse({
                    'status': 'success',
                    'is_active': webhook_config.is_active
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)


# =============================================================================
# UUID-Based Webhook Endpoint
# =============================================================================

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def uuid_webhook(request, webhook_uuid):
    """
    UUID-based webhook endpoint for TradingView signals.
    URL format: /api/v1/signal/<uuid>/
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        from .models import WebhookConfig, Signal
        
        # Find webhook config by UUID
        try:
            webhook_config = WebhookConfig.objects.get(webhook_uuid=webhook_uuid)
        except WebhookConfig.DoesNotExist:
            return JsonResponse({'error': 'Invalid webhook UUID'}, status=404)
        
        # Check if webhook is active
        if not webhook_config.is_active:
            return JsonResponse({'error': 'Webhook is disabled'}, status=403)
        
        # Parse JSON payload
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Extract signal data from payload
        user_uuid = payload.get('user_uuid')
        if str(webhook_config.webhook_uuid) != user_uuid:
            return JsonResponse({'error': 'UUID mismatch'}, status=400)
        
        # Map TradingView data to Signal fields
        signal_data = {
            'user': webhook_config.user,
            'symbol': payload.get('symbol', 'UNKNOWN'),
            'timeframe': payload.get('timeframe', '1H'),
            'side': payload.get('side', 'buy').lower(),
            'price': float(payload.get('price', 0)),
            'sl': float(payload.get('sl', 0)),
            'tp': float(payload.get('tp', 0)),
            'confidence': float(payload.get('confidence', 50)),
            'strategy': payload.get('strategy', 'Unknown'),
            'regime': payload.get('regime', 'Unknown'),
            'session': payload.get('session', 'Unknown'),
            'is_allowed': True
        }
        
        # Create signal
        signal = Signal.objects.create(**signal_data)
        
        # Run through validation pipeline
        from .validation import SignalValidationPipeline
        evaluation = SignalValidationPipeline.process_signal(signal)
        
        # Increment webhook counter
        webhook_config.increment_signal_count()
        
        # Return response with evaluation info
        response_data = {
            'status': 'success',
            'signal_id': signal.id,
            'message': 'Signal received and processed',
            'evaluation': {
                'passed': evaluation.passed,
                'blocked_reason': evaluation.blocked_reason,
                'ai_score': evaluation.final_ai_score,
                'checks': {
                    'news': evaluation.news_check,
                    'prop': evaluation.prop_check,
                    'score': evaluation.score_check,
                    'strategy': evaluation.strategy_check,
                }
            }
        }
        
        return JsonResponse(response_data, status=201)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"UUID webhook error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def override_signal(request, signal_id):
    """
    Admin-only view to manually override a blocked signal.
    Creates audit log and updates evaluation status.
    """
    # Check admin permissions
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin):
        return JsonResponse({'error': 'Admin permission required'}, status=403)
    
    try:
        from .models import Signal, SignalEvaluation
        
        # Get signal and evaluation
        signal = Signal.objects.get(id=signal_id)
        try:
            evaluation = signal.evaluation
        except SignalEvaluation.DoesNotExist:
            return JsonResponse({'error': 'No evaluation found for this signal'}, status=404)
        
        # Check if already overridden
        if evaluation.is_overridden:
            return JsonResponse({'error': 'Signal already overridden'}, status=400)
        
        # Check if signal is blocked (shouldn't override passed signals)
        if evaluation.passed and not evaluation.is_overridden:
            return JsonResponse({'error': 'Cannot override passed signal'}, status=400)
        
        # Get override reason from request
        try:
            data = json.loads(request.body)
            override_reason = data.get('reason', 'Admin override - no reason provided')
        except json.JSONDecodeError:
            override_reason = 'Admin override - no reason provided'
        
        # Create override log and update evaluation
        evaluation.create_override_log(request.user, override_reason)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Signal override successful',
            'signal_id': signal.id,
            'overridden_by': request.user.email,
            'overridden_at': evaluation.overridden_at.isoformat()
        })
        
    except Signal.DoesNotExist:
        return JsonResponse({'error': 'Signal not found'}, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Override signal error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


class ValidationTrackRecordView(LoginRequiredMixin, TemplateView):
    """
    System Track Record page showing AI validation performance metrics.
    
    Displays:
    - Monthly accuracy trends
    - Validation success rates
    - Strategy-specific performance
    - Truth Index distributions
    - Public-facing reputation analytics
    """
    template_name = 'signals/validation_track_record.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .models import TradeValidation, ValidationScore, Signal
        from django.db.models import Avg, Count, Q
        from datetime import datetime, timedelta
        from decimal import Decimal
        
        # Get time period from query params (default: last 6 months)
        months_back = int(self.request.GET.get('months', 6))
        start_date = timezone.now() - timedelta(days=months_back * 30)
        
        # Overall Statistics
        total_validations = TradeValidation.objects.filter(
            validated_at__gte=start_date
        ).count()
        
        approved_count = TradeValidation.objects.filter(
            validated_at__gte=start_date,
            status='approved'
        ).count()
        
        conditional_count = TradeValidation.objects.filter(
            validated_at__gte=start_date,
            status='conditional'
        ).count()
        
        rejected_count = TradeValidation.objects.filter(
            validated_at__gte=start_date,
            status='rejected'
        ).count()
        
        avg_truth_index = TradeValidation.objects.filter(
            validated_at__gte=start_date
        ).aggregate(Avg('truth_index'))['truth_index__avg'] or 0
        
        # Approval rate
        approval_rate = (approved_count / total_validations * 100) if total_validations > 0 else 0
        
        # Monthly trends (last 6 months)
        monthly_stats = []
        for i in range(months_back):
            month_start = timezone.now() - timedelta(days=(months_back - i) * 30)
            month_end = month_start + timedelta(days=30)
            
            month_validations = TradeValidation.objects.filter(
                validated_at__gte=month_start,
                validated_at__lt=month_end
            )
            
            month_approved = month_validations.filter(status='approved').count()
            month_total = month_validations.count()
            month_avg_truth = month_validations.aggregate(Avg('truth_index'))['truth_index__avg'] or 0
            
            monthly_stats.append({
                'month': month_start.strftime('%b %Y'),
                'total': month_total,
                'approved': month_approved,
                'approval_rate': (month_approved / month_total * 100) if month_total > 0 else 0,
                'avg_truth_index': float(month_avg_truth)
            })
        
        # Strategy-specific performance
        strategy_stats = []
        strategies = Signal.objects.values('strategy').annotate(
            count=Count('id')
        ).filter(count__gt=5).order_by('-count')
        
        for strat in strategies:
            strategy_name = strat['strategy']
            
            # Get validations for this strategy
            strategy_validations = TradeValidation.objects.filter(
                signal__strategy=strategy_name,
                validated_at__gte=start_date
            )
            
            strat_total = strategy_validations.count()
            if strat_total == 0:
                continue
            
            strat_approved = strategy_validations.filter(status='approved').count()
            strat_avg_truth = strategy_validations.aggregate(Avg('truth_index'))['truth_index__avg'] or 0
            
            strategy_stats.append({
                'name': strategy_name,
                'total': strat_total,
                'approved': strat_approved,
                'approval_rate': (strat_approved / strat_total * 100),
                'avg_truth_index': float(strat_avg_truth)
            })
        
        # Sort by approval rate
        strategy_stats.sort(key=lambda x: x['approval_rate'], reverse=True)
        
        # Truth Index distribution
        truth_distribution = {
            'excellent': TradeValidation.objects.filter(
                validated_at__gte=start_date,
                truth_index__gte=85
            ).count(),
            'good': TradeValidation.objects.filter(
                validated_at__gte=start_date,
                truth_index__gte=75,
                truth_index__lt=85
            ).count(),
            'moderate': TradeValidation.objects.filter(
                validated_at__gte=start_date,
                truth_index__gte=65,
                truth_index__lt=75
            ).count(),
            'conditional': TradeValidation.objects.filter(
                validated_at__gte=start_date,
                truth_index__gte=60,
                truth_index__lt=65
            ).count(),
            'rejected': TradeValidation.objects.filter(
                validated_at__gte=start_date,
                truth_index__lt=60
            ).count(),
        }
        
        # Breakdown scores averages
        all_validations = TradeValidation.objects.filter(
            validated_at__gte=start_date
        )
        
        breakdown_averages = {
            'technical_integrity': 0,
            'volatility_filter': 0,
            'regime_alignment': 0,
            'sentiment_coherence': 0,
            'historical_reliability': 0,
            'psychological_safety': 0
        }
        
        if all_validations.exists():
            for validation in all_validations:
                if validation.breakdown:
                    for key in breakdown_averages.keys():
                        if key in validation.breakdown:
                            breakdown_averages[key] += float(validation.breakdown[key])
            
            # Calculate averages
            count = all_validations.count()
            for key in breakdown_averages.keys():
                breakdown_averages[key] = (breakdown_averages[key] / count) * 100 if count > 0 else 0
        
        # System health grade
        if approval_rate >= 70 and avg_truth_index >= 75:
            system_grade = 'A'
            system_health = 'Excellent'
        elif approval_rate >= 60 and avg_truth_index >= 70:
            system_grade = 'B'
            system_health = 'Good'
        elif approval_rate >= 50 and avg_truth_index >= 65:
            system_grade = 'C'
            system_health = 'Fair'
        else:
            system_grade = 'D'
            system_health = 'Needs Improvement'
        
        context.update({
            'total_validations': total_validations,
            'approved_count': approved_count,
            'conditional_count': conditional_count,
            'rejected_count': rejected_count,
            'approval_rate': approval_rate,
            'avg_truth_index': float(avg_truth_index),
            'monthly_stats': monthly_stats,
            'strategy_stats': strategy_stats,
            'truth_distribution': truth_distribution,
            'breakdown_averages': breakdown_averages,
            'system_grade': system_grade,
            'system_health': system_health,
            'months_back': months_back,
        })
        
        return context


class InsightDetailView(LoginRequiredMixin, TemplateView):
    """
    Detailed view of a single opportunity/signal insight.
    Opens in a new tab/window with complete insight information.
    """
    template_name = 'signals/insight_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signal_id = kwargs.get('pk')
        
        try:
            # Get the signal - allow access if user owns it OR if no user assigned
            # This makes all signals accessible to logged-in users for now
            signal = Signal.objects.select_related('validation').get(id=signal_id)
            context['signal'] = signal
        except Signal.DoesNotExist:
            context['signal'] = None
            context['error'] = 'Opportunity not found or access denied'
            logger.error(f"Signal {signal_id} not found")
        
        return context
