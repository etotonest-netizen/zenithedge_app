from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q, Min, Max
from django.utils import timezone
from datetime import timedelta
from .models import InsightAudit, AuditRCA, AutopsyJob, LabelingRule
from marketdata.models import OHLCVCandle, DataSource
from signals.models import Signal


@login_required
def autopsy_dashboard(request):
    """Main AutopsyLoop analytics dashboard"""
    days = int(request.GET.get('days', 7))
    cutoff = timezone.now() - timedelta(days=days)
    
    # Overall stats
    total_audits = InsightAudit.objects.filter(created_at__gte=cutoff).count()
    total_signals = Signal.objects.count()
    total_candles = OHLCVCandle.objects.count()
    
    # Outcome breakdown
    outcomes = InsightAudit.objects.filter(
        created_at__gte=cutoff
    ).values('outcome').annotate(count=Count('id')).order_by('-count')
    
    # Success rate by strategy
    strategy_stats = InsightAudit.objects.filter(
        created_at__gte=cutoff
    ).values('insight__strategy').annotate(
        total=Count('id'),
        succeeded=Count('id', filter=Q(outcome='succeeded')),
        failed=Count('id', filter=Q(outcome='failed')),
        avg_pnl=Avg('pnl_pct'),
        avg_drawdown=Avg('max_drawdown')
    ).order_by('-total')[:10]
    
    for stat in strategy_stats:
        stat['success_rate'] = (stat['succeeded'] / stat['total'] * 100) if stat['total'] > 0 else 0
    
    # Top RCA causes
    rca_causes = AuditRCA.objects.filter(
        audit__created_at__gte=cutoff
    ).values('cause').annotate(
        count=Count('id'),
        avg_confidence=Avg('confidence')
    ).order_by('-count')[:10]
    
    # Format cause names for display (replace underscores with spaces)
    for cause in rca_causes:
        cause['cause_display'] = cause['cause'].replace('_', ' ').title()
    
    # Recent audits
    recent_audits = InsightAudit.objects.filter(
        created_at__gte=cutoff
    ).select_related('insight').order_by('-created_at')[:20]
    
    # Recent jobs
    recent_jobs = AutopsyJob.objects.order_by('-created_at')[:5]
    
    context = {
        'days': days,
        'total_audits': total_audits,
        'total_signals': total_signals,
        'total_candles': total_candles,
        'outcomes': outcomes,
        'strategy_stats': strategy_stats,
        'rca_causes': rca_causes,
        'recent_audits': recent_audits,
        'recent_jobs': recent_jobs,
    }
    
    return render(request, 'autopsy/dashboard.html', context)


@login_required
def strategy_detail(request, strategy_name):
    """Detailed analysis for a specific strategy"""
    days = int(request.GET.get('days', 30))
    cutoff = timezone.now() - timedelta(days=days)
    
    audits = InsightAudit.objects.filter(
        insight__strategy=strategy_name,
        created_at__gte=cutoff
    ).select_related('insight').order_by('-created_at')
    
    total = audits.count()
    succeeded = audits.filter(outcome='succeeded').count()
    
    context = {
        'strategy_name': strategy_name,
        'days': days,
        'audits': audits[:50],
        'total': total,
        'succeeded': succeeded,
        'success_rate': (succeeded / total * 100) if total > 0 else 0,
    }
    
    return render(request, 'autopsy/strategy_detail.html', context)


# ============================================================================
# ZENITH MARKET ANALYST - VISUAL INSIGHTS MODE VIEWS
# ============================================================================

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from autopsy.models import MarketInsight
import json
import logging

logger = logging.getLogger('autopsy')


@csrf_exempt
@require_POST
def submit_insight_webhook(request):
    """
    Webhook endpoint for Pine Script to submit bar metadata
    
    Receives JSON metadata from TradingView indicator and processes it
    through the AI insight engine to generate market intelligence.
    
    POST /autopsy/api/submit-insight/
    
    Expected JSON payload:
    {
        "symbol": "EURUSD",
        "timeframe": "1H",
        "timestamp": "2025-11-13T12:00:00Z",
        "regime": "trending",
        "structure": "bos",
        "momentum": "increasing",
        "volume_state": "spike",
        "session": "london",
        "expected_behavior": "Expansion",
        "strength": 85,
        "risk_notes": ["High volatility"]
    }
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        
        # Log webhook receipt
        logger.info(f"Received insight webhook: {data.get('symbol')} {data.get('timeframe')}")
        
        # Import analyst here to avoid circular imports
        from autopsy.insight_engine import analyst
        
        # Process bar through AI engine
        insight_data = analyst.process_bar(data)
        
        # Save to database
        insight = analyst.save_insight(insight_data)
        
        # Return success response
        return JsonResponse({
            'status': 'success',
            'insight_id': insight.id,
            'insight_index': insight.insight_index,
            'insight_text': insight.insight_text,
            'vocabulary_hash': insight.vocabulary_hash,
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def market_analyst_view(request):
    """
    Main Visual Insights Mode dashboard
    
    Displays real-time market intelligence with filtering and statistics
    """
    # Get filter parameters
    symbol = request.GET.get('symbol', '')
    timeframe = request.GET.get('timeframe', '')
    regime = request.GET.get('regime', '')
    hours = int(request.GET.get('hours', 24))
    
    # Import analyst
    from autopsy.insight_engine import analyst
    
    # Build query
    queryset = MarketInsight.objects.all()
    
    if symbol:
        queryset = queryset.filter(symbol=symbol)
    
    if timeframe:
        queryset = queryset.filter(timeframe=timeframe)
    
    if regime:
        queryset = queryset.filter(regime=regime)
    
    # Time filter
    cutoff = timezone.now() - timedelta(hours=hours)
    queryset = queryset.filter(created_at__gte=cutoff)
    
    # Get insights
    insights = queryset.order_by('-timestamp')[:50]
    
    # Get statistics
    stats = analyst.get_insight_statistics(hours=hours)
    
    # Get available symbols and timeframes for filters
    available_symbols = MarketInsight.objects.values_list('symbol', flat=True).distinct().order_by('symbol')
    available_timeframes = MarketInsight.objects.values_list('timeframe', flat=True).distinct().order_by('timeframe')
    
    context = {
        'insights': insights,
        'stats': stats,
        'symbol': symbol,
        'timeframe': timeframe,
        'regime': regime,
        'hours': hours,
        'available_symbols': available_symbols,
        'available_timeframes': available_timeframes,
        'total_insights': queryset.count(),
    }
    
    return render(request, 'autopsy/market_analyst.html', context)


@login_required
@require_http_methods(["GET"])
def get_insights_api(request):
    """
    API endpoint for real-time insight updates
    
    GET /autopsy/api/get-insights/?symbol=EURUSD&timeframe=1H&limit=20
    
    Returns JSON array of recent insights with full metadata
    """
    try:
        # Get query parameters
        symbol = request.GET.get('symbol')
        timeframe = request.GET.get('timeframe')
        regime = request.GET.get('regime')
        limit = int(request.GET.get('limit', 20))
        since_id = request.GET.get('since_id')  # For polling updates
        
        # Build query
        queryset = MarketInsight.objects.all()
        
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        
        if regime:
            queryset = queryset.filter(regime=regime)
        
        if since_id:
            # Only return insights created after this ID
            queryset = queryset.filter(id__gt=int(since_id))
        
        # Get insights
        insights = queryset.order_by('-timestamp')[:limit]
        
        # Serialize to JSON
        data = [{
            'id': i.id,
            'symbol': i.symbol,
            'timeframe': i.timeframe,
            'timestamp': i.timestamp.isoformat(),
            'regime': i.get_regime_display(),
            'regime_code': i.regime,
            'structure': i.get_structure_display(),
            'structure_code': i.structure,
            'momentum': i.get_momentum_display(),
            'volume_state': i.get_volume_state_display(),
            'session': i.get_session_display(),
            'insight_text': i.insight_text,
            'suggestion': i.suggestion,
            'insight_index': i.insight_index,
            'structure_clarity': i.structure_clarity,
            'regime_stability': i.regime_stability,
            'volume_quality': i.volume_quality,
            'momentum_alignment': i.momentum_alignment,
            'session_validity': i.session_validity,
            'risk_level': i.risk_level,
            'chart_labels': i.chart_labels,
            'news_impact': i.news_impact,
            'news_context': i.news_context,
            'expected_behavior': i.expected_behavior,
            'strength': i.strength,
            'risk_notes': i.risk_notes,
        } for i in insights]
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'insights': data
        })
        
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_chart_labels(request, symbol):
    """
    Get chart labels for a specific symbol
    
    GET /autopsy/api/chart-labels/EURUSD/?timeframe=1H&limit=100
    
    Returns micro-labels for TradingView chart overlay
    """
    try:
        timeframe = request.GET.get('timeframe', '1H')
        limit = int(request.GET.get('limit', 100))
        
        # Get recent insights for this symbol
        insights = MarketInsight.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp')[:limit]
        
        # Extract chart labels
        labels = []
        for insight in insights:
            if insight.chart_labels:
                labels.append({
                    'timestamp': insight.timestamp.isoformat(),
                    'labels': insight.chart_labels,
                    'insight_index': insight.insight_index,
                    'regime': insight.regime,
                    'structure': insight.structure,
                })
        
        return JsonResponse({
            'status': 'success',
            'symbol': symbol,
            'timeframe': timeframe,
            'count': len(labels),
            'labels': labels
        })
        
    except Exception as e:
        logger.error(f"Chart labels error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def insight_detail(request, insight_id):
    """
    Detailed view for a single market insight
    """
    insight = get_object_or_404(MarketInsight, id=insight_id)
    
    # Get related insights (same symbol/timeframe, nearby time)
    time_window_start = insight.timestamp - timedelta(hours=4)
    time_window_end = insight.timestamp + timedelta(hours=4)
    
    related_insights = MarketInsight.objects.filter(
        symbol=insight.symbol,
        timeframe=insight.timeframe,
        timestamp__gte=time_window_start,
        timestamp__lte=time_window_end
    ).exclude(id=insight.id).order_by('timestamp')[:10]
    
    # Import scorer for quality label
    from autopsy.insight_scorer import InsightScorer
    scorer = InsightScorer()
    
    quality_label = scorer.get_quality_label(insight.insight_index)
    color_code = scorer.get_color_code(insight.insight_index)
    
    context = {
        'insight': insight,
        'related_insights': related_insights,
        'quality_label': quality_label,
        'color_code': color_code,
    }
    
    return render(request, 'autopsy/insight_detail.html', context)


@login_required
@require_http_methods(["GET"])
def recent_insights_api(request):
    """
    API endpoint for notification bell - recent high-quality insights
    
    GET /autopsy/api/recent-insights/?minutes=30
    
    Returns recent insights for notification dropdown
    """
    try:
        # Get insights from last 30 minutes by default
        minutes = int(request.GET.get('minutes', 30))
        cutoff = timezone.now() - timedelta(minutes=minutes)
        
        # Get recent high-quality insights (index >= 50)
        insights = MarketInsight.objects.filter(
            created_at__gte=cutoff,
            insight_index__gte=50
        ).order_by('-created_at')[:10]
        
        # Get user's last check time from session or assume all are new
        last_check = request.session.get('last_insight_check')
        if last_check:
            last_check_time = timezone.datetime.fromisoformat(last_check)
        else:
            last_check_time = cutoff
        
        # Serialize data
        data = []
        for insight in insights:
            # Determine if unread
            is_unread = insight.created_at > last_check_time
            
            # Calculate time ago
            time_diff = timezone.now() - insight.created_at
            if time_diff.seconds < 60:
                time_ago = 'Just now'
            elif time_diff.seconds < 3600:
                time_ago = f'{time_diff.seconds // 60}m ago'
            else:
                time_ago = f'{time_diff.seconds // 3600}h ago'
            
            data.append({
                'id': insight.id,
                'symbol': insight.symbol,
                'timeframe': insight.timeframe,
                'regime': insight.get_regime_display(),
                'structure': insight.get_structure_display(),
                'insight_index': insight.insight_index,
                'insight_text': insight.insight_text[:100] + '...' if len(insight.insight_text) > 100 else insight.insight_text,
                'time_ago': time_ago,
                'read': not is_unread,
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'insights': data
        })
        
    except Exception as e:
        logger.error(f"Recent insights API error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
