"""
UUID-based webhook URLs for TradingView signals.
This allows users to have unique webhook URLs without exposing API keys.
"""
from django.urls import path
from . import views

app_name = 'webhook'

urlpatterns = [
    # UUID-based webhook endpoint: /api/v1/signal/<uuid>/
    path('', views.uuid_webhook, name='uuid_webhook'),
]
