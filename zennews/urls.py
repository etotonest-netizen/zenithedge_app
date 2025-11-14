"""
ZenNews URL Configuration
"""
from django.urls import path
from . import views

app_name = 'zennews'

urlpatterns = [
    path('', views.news_dashboard, name='dashboard'),
    path('api/news/', views.news_api, name='news_api'),
    path('api/sentiment-chart/', views.sentiment_chart_data, name='sentiment_chart'),
    path('api/alert/<int:alert_id>/read/', views.mark_alert_read, name='mark_alert_read'),
]
