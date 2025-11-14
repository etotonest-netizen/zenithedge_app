"""
Market Insights API URL Configuration

URL patterns for AI Decision Intelligence Console API endpoints.
Replaces /api/signals/ with /api/insights/ terminology.

All endpoints focus on market intelligence, not trading instructions.
"""

from django.urls import path
from signals import api_insights

app_name = 'insights_api'

urlpatterns = [
    # List all insights for authenticated user
    path('', api_insights.insights_list_api, name='insights-list'),
    
    # Get specific insight details
    path('<int:insight_id>/', api_insights.insight_detail_api, name='insight-detail'),
    
    # Summary statistics
    path('summary/', api_insights.insights_summary_api, name='insights-summary'),
    
    # Webhook endpoint for creating insights from TradingView
    path('webhook/create/', api_insights.webhook_insights_create, name='webhook-create'),
]
