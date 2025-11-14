"""
Market Insights API Views

REST API endpoints for the AI Decision Intelligence Console.
Replaces signal-focused endpoints with intelligence-focused endpoints.

All endpoints use MarketInsight model and intelligence terminology.
NO TRADING INSTRUCTIONS - only market analysis and context.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from signals.models import MarketInsight
from signals.insight_converter import create_insight_from_webhook
from zenbot.validation_engine import SignalValidator

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@login_required
def insights_list_api(request):
    """
    List market insights for authenticated user.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - symbol: Filter by symbol (e.g., GBPJPY)
    - bias: Filter by bias (bearish, neutral, bullish)
    - market_phase: Filter by phase (accumulation, expansion, manipulation, distribution)
    - min_insight_index: Minimum insight index (0-100)
    - high_quality_only: If 'true', only show high quality insights (default: false)
    
    Returns:
        JSON: {
            'insights': [...],
            'pagination': {...},
            'filters': {...}
        }
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        symbol = request.GET.get('symbol', '').strip().upper()
        bias = request.GET.get('bias', '').lower()
        market_phase = request.GET.get('market_phase', '').lower()
        min_insight_index = float(request.GET.get('min_insight_index', 0))
        high_quality_only = request.GET.get('high_quality_only', 'false').lower() == 'true'
        
        # Build queryset
        insights_qs = MarketInsight.objects.filter(user=request.user).order_by('-received_at')
        
        # Apply filters
        if symbol:
            insights_qs = insights_qs.filter(symbol__icontains=symbol)
        
        if bias and bias in ['bearish', 'neutral', 'bullish']:
            insights_qs = insights_qs.filter(bias=bias)
        
        if market_phase and market_phase in ['accumulation', 'expansion', 'manipulation', 'distribution']:
            insights_qs = insights_qs.filter(market_phase=market_phase)
        
        if min_insight_index > 0:
            insights_qs = insights_qs.filter(insight_index__gte=min_insight_index)
        
        if high_quality_only:
            insights_qs = insights_qs.filter(is_high_quality=True)
        
        # Paginate
        paginator = Paginator(insights_qs, page_size)
        insights_page = paginator.get_page(page)
        
        # Serialize insights (NO TRADING LANGUAGE)
        insights_data = [insight.to_dict() for insight in insights_page]
        
        return JsonResponse({
            'success': True,
            'insights': insights_data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'page_size': page_size,
                'has_next': insights_page.has_next(),
                'has_previous': insights_page.has_previous(),
            },
            'filters': {
                'symbol': symbol,
                'bias': bias,
                'market_phase': market_phase,
                'min_insight_index': min_insight_index,
                'high_quality_only': high_quality_only,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in insights_list_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def insight_detail_api(request, insight_id):
    """
    Get detailed information for a specific market insight.
    
    Returns:
        JSON: Full insight data including narrative, bias, metrics
    """
    try:
        insight = MarketInsight.objects.get(id=insight_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'insight': insight.to_dict()
        })
        
    except MarketInsight.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Insight not found or access denied'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error in insight_detail_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt  # Use webhook authentication instead
def webhook_insights_create(request):
    """
    Create market insight from TradingView webhook (NEW FLOW).
    
    This replaces signal_webhook() - creates MarketInsight directly
    instead of creating Signal first.
    
    Expected Payload:
    {
        "symbol": "GBPJPY",
        "timeframe": "4H",
        "regime": "Breakout",
        "session": "London",
        "confidence": 85,
        "strategy": "smc",
        "price": 185.45,
        "timestamp": "2024-11-11 10:30:00",
        
        // Optional legacy fields (for transition period)
        "side": "buy",
        "sl": 184.50,
        "tp": 187.00
    }
    
    Returns:
        JSON: Created insight data
    """
    try:
        import json
        webhook_data = json.loads(request.body)
        
        # Validate webhook (add your authentication here)
        # webhook_uuid = request.GET.get('uuid')
        # if not validate_webhook_uuid(webhook_uuid):
        #     return JsonResponse({'success': False, 'error': 'Invalid webhook'}, status=403)
        
        # Run validation engine
        validator = SignalValidator()
        validation_result = validator.validate_signal(webhook_data)
        
        # Create MarketInsight (bypasses Signal model)
        insight = create_insight_from_webhook(webhook_data, validation_result)
        
        # Assign user if authenticated, otherwise leave null
        if request.user.is_authenticated:
            insight.user = request.user
        
        insight.save()
        
        logger.info(f"Created insight #{insight.id} for {insight.symbol} - {insight.bias} bias")
        
        return JsonResponse({
            'success': True,
            'message': 'Market insight created',
            'insight_id': insight.id,
            'insight': insight.to_dict()
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error creating insight from webhook: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def insights_summary_api(request):
    """
    Get summary statistics for user's market insights.
    
    Returns:
        JSON: {
            'total_insights': int,
            'high_quality_count': int,
            'bias_distribution': {...},
            'market_phase_distribution': {...},
            'avg_insight_index': float,
            'recent_insights': [...]
        }
    """
    try:
        insights_qs = MarketInsight.objects.filter(user=request.user)
        
        total = insights_qs.count()
        high_quality = insights_qs.filter(is_high_quality=True).count()
        
        # Bias distribution
        bias_counts = {
            'bearish': insights_qs.filter(bias='bearish').count(),
            'neutral': insights_qs.filter(bias='neutral').count(),
            'bullish': insights_qs.filter(bias='bullish').count(),
        }
        
        # Market phase distribution
        phase_counts = {
            'accumulation': insights_qs.filter(market_phase='accumulation').count(),
            'expansion': insights_qs.filter(market_phase='expansion').count(),
            'manipulation': insights_qs.filter(market_phase='manipulation').count(),
            'distribution': insights_qs.filter(market_phase='distribution').count(),
        }
        
        # Average insight index
        avg_insight_index = 0
        if total > 0:
            total_index = sum(i.insight_index for i in insights_qs)
            avg_insight_index = total_index / total
        
        # Recent insights (last 5)
        recent = insights_qs.order_by('-received_at')[:5]
        recent_data = [insight.to_dict() for insight in recent]
        
        return JsonResponse({
            'success': True,
            'summary': {
                'total_insights': total,
                'high_quality_count': high_quality,
                'high_quality_percentage': (high_quality / total * 100) if total > 0 else 0,
                'bias_distribution': bias_counts,
                'market_phase_distribution': phase_counts,
                'avg_insight_index': round(avg_insight_index, 2),
                'recent_insights': recent_data,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in insights_summary_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
