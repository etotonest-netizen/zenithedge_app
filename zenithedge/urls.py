"""
URL configuration for zenithedge project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from signals.tradingview_webhook import tradingview_webhook, webhook_health_check, webhook_test

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('admin_dashboard.urls')),  # Admin control panel
    path('accounts/', include('accounts.urls')),
    path('signals/', include('signals.urls')),
    path('api/insights/', include('signals.api_urls')),  # NEW: Insights API endpoints
    path('analytics/', include('analytics.urls')),  # Analytics & backtesting
    path('backtest/', include('analytics.urls')),  # Alias for backward compatibility
    path('support/', include('support.urls')),
    path('bot/', include('bot.urls')),  # ZenBot endpoints
    path('news/', include('zennews.urls')),  # Financial news
    path('propcoach/', include('propcoach.urls')),  # Prop firm training
    path('mentor/', include('zenithmentor.urls')),  # Training system
    path('notifications/', include('notifications.urls')),  # Real-time notifications
    path('autopsy/', include('autopsy.urls')),  # AutopsyLoop analytics dashboard
    path('engine/', include('engine.urls')),  # Trading Engine API
    
    # TradingView Webhook Endpoints (Token-based authentication for production)
    path('api/signals/webhook/', tradingview_webhook, name='tradingview_webhook'),
    path('api/signals/webhook/health/', webhook_health_check, name='webhook_health'),
    path('api/signals/webhook/test/', webhook_test, name='webhook_test'),
    
    # UUID-based webhook endpoint (legacy)
    path('api/v1/signal/<uuid:webhook_uuid>/', include('signals.webhook_urls')),
]
