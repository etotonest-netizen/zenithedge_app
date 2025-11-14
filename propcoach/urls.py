"""
URL patterns for PropCoach app
"""
from django.urls import path
from . import views

app_name = 'propcoach'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Challenge management
    path('start/', views.start_challenge, name='start_challenge'),
    path('challenge/<uuid:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('challenge/<uuid:challenge_id>/trades/', views.trade_log, name='trade_log'),
    path('challenge/<uuid:challenge_id>/coaching/', views.coaching_panel, name='coaching_panel'),
    
    # Community
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # API endpoints
    path('api/challenge/<uuid:challenge_id>/status/', views.api_challenge_status, name='api_challenge_status'),
]
