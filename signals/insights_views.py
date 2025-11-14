"""
Market Insights Dashboard Views

Django views for the AI Decision Intelligence Console UI.
Replaces signal-focused dashboards with intelligence-focused dashboards.

All views use MarketInsight model and intelligence terminology.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from signals.models import MarketInsight


@login_required
def insights_dashboard(request):
    """
    Main dashboard for AI Decision Intelligence Console.
    
    Displays market insights as Insight Snapshot cards (NO TRADING LANGUAGE).
    """
    # Get filter parameters
    symbol = request.GET.get('symbol', '').strip().upper()
    bias = request.GET.get('bias', '').lower()
    market_phase = request.GET.get('market_phase', '').lower()
    min_insight_index = request.GET.get('min_insight_index', '')
    high_quality_only = request.GET.get('high_quality_only', False)
    
    # Build queryset
    insights_qs = MarketInsight.objects.filter(user=request.user).order_by('-received_at')
    
    # Apply filters
    if symbol:
        insights_qs = insights_qs.filter(symbol__icontains=symbol)
    
    if bias and bias in ['bearish', 'neutral', 'bullish']:
        insights_qs = insights_qs.filter(bias=bias)
    
    if market_phase and market_phase in ['accumulation', 'expansion', 'manipulation', 'distribution']:
        insights_qs = insights_qs.filter(market_phase=market_phase)
    
    if min_insight_index:
        try:
            min_index = float(min_insight_index)
            insights_qs = insights_qs.filter(insight_index__gte=min_index)
        except ValueError:
            pass
    
    if high_quality_only:
        insights_qs = insights_qs.filter(is_high_quality=True)
    
    # Paginate
    paginator = Paginator(insights_qs, 20)  # 20 insights per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'insights': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filter_applied': any([symbol, bias, market_phase, min_insight_index, high_quality_only]),
    }
    
    return render(request, 'signals/insights_dashboard.html', context)
