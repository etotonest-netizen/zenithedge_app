"""
ZenNews Views
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count
from .models import NewsEvent, NewsAlert
import json


def news_dashboard(request):
    """
    Main news dashboard view
    """
    # Get recent news (last 24 hours) - base queryset without slicing
    recent_news_qs = NewsEvent.objects.filter(
        timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
    ).order_by('-timestamp')
    
    # Get statistics from unsliced queryset
    stats = {
        'total_today': recent_news_qs.count(),
        'high_impact': recent_news_qs.filter(impact_level='high').count(),
        'avg_sentiment': recent_news_qs.aggregate(avg=Avg('sentiment'))['avg'] or 0,
    }
    
    # Now slice for display (after statistics are calculated)
    recent_news = recent_news_qs[:50]
    
    # Get unread alerts
    unread_alerts = NewsAlert.objects.filter(is_read=False).order_by('-created_at')[:10]
    
    context = {
        'news_events': recent_news,
        'alerts': unread_alerts,
        'stats': stats,
    }
    
    return render(request, 'zennews/dashboard.html', context)


def news_api(request):
    """
    API endpoint for fetching news data
    """
    symbol = request.GET.get('symbol', '')
    hours = int(request.GET.get('hours', 24))
    
    # Build query
    query = NewsEvent.objects.filter(
        timestamp__gte=timezone.now() - timezone.timedelta(hours=hours)
    )
    
    if symbol:
        query = query.filter(symbol=symbol)
    
    query = query.order_by('-timestamp')[:100]
    
    # Serialize data
    news_data = []
    for news in query:
        news_data.append({
            'id': str(news.id),
            'symbol': news.symbol,
            'headline': news.headline,
            'sentiment': news.sentiment,
            'sentiment_label': news.get_sentiment_label(),
            'impact_level': news.impact_level,
            'topic': news.topic,
            'source': news.source,
            'source_url': news.source_url,
            'timestamp': news.timestamp.isoformat(),
        })
    
    return JsonResponse({'news': news_data})


def sentiment_chart_data(request):
    """
    API endpoint for sentiment chart data
    """
    symbol = request.GET.get('symbol', 'EURUSD')
    hours = int(request.GET.get('hours', 24))
    
    # Get news for the symbol
    news_events = NewsEvent.objects.filter(
        symbol=symbol,
        timestamp__gte=timezone.now() - timezone.timedelta(hours=hours)
    ).order_by('timestamp')
    
    # Prepare chart data
    labels = []
    sentiments = []
    
    for news in news_events:
        labels.append(news.timestamp.strftime('%Y-%m-%d %H:%M'))
        sentiments.append(float(news.sentiment))
    
    return JsonResponse({
        'labels': labels,
        'sentiments': sentiments,
        'symbol': symbol,
    })


def mark_alert_read(request, alert_id):
    """
    Mark an alert as read
    """
    if request.method == 'POST':
        try:
            alert = NewsAlert.objects.get(id=alert_id)
            alert.is_read = True
            alert.save()
            return JsonResponse({'status': 'success'})
        except NewsAlert.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alert not found'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
