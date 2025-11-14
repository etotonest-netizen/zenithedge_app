from django.urls import path
from . import views

app_name = 'autopsy'

urlpatterns = [
    # AutopsyLoop - Traditional retrospective analysis
    path('', views.autopsy_dashboard, name='dashboard'),
    path('strategy/<str:strategy_name>/', views.strategy_detail, name='strategy_detail'),
    
    # Zenith Market Analyst - Visual Insights Mode
    path('market-analyst/', views.market_analyst_view, name='market_analyst'),
    path('insight/<int:insight_id>/', views.insight_detail, name='insight_detail'),
    
    # API Endpoints
    path('api/submit-insight/', views.submit_insight_webhook, name='submit_insight'),
    path('api/get-insights/', views.get_insights_api, name='get_insights'),
    path('api/chart-labels/<str:symbol>/', views.get_chart_labels, name='chart_labels'),
    path('api/recent-insights/', views.recent_insights_api, name='recent_insights'),
]
