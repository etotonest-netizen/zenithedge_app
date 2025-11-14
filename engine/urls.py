"""
Engine URL Configuration
=========================
API endpoints for engine features.
"""

from django.urls import path
from . import views

app_name = 'engine'

urlpatterns = [
    # Dashboard
    path('', views.engine_dashboard, name='dashboard'),
    
    # Visual overlays
    path('api/visuals/latest/', views.get_latest_visuals, name='latest_visuals'),
    path('api/visuals/<int:signal_id>/', views.get_signal_visuals, name='signal_visuals'),
    path('api/visuals/backtest/<int:backtest_id>/', views.get_backtest_visuals, name='backtest_visuals'),
    
    # Engine status and control
    path('api/status/', views.get_engine_status, name='engine_status'),
    path('api/detect/', views.trigger_detection, name='trigger_detection'),
]
