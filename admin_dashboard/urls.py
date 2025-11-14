"""
Admin Dashboard URL Configuration
"""
from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('settings/', views.system_settings, name='settings'),
    path('analytics/', views.system_analytics, name='analytics'),
    
    # Module management views
    path('signals/', views.signals_management, name='signals'),
    path('strategies/', views.strategies_management, name='strategies'),
    path('sessions/', views.sessions_management, name='sessions'),
    path('risk-control/', views.risk_control_management, name='risk_control'),
    path('prop-rules/', views.prop_rules_management, name='prop_rules'),
    path('trade-journal/', views.trade_journal_management, name='trade_journal'),
    
    # Additional module management
    path('zenithmentor/', views.zenithmentor_management, name='zenithmentor'),
    path('propcoach/', views.propcoach_management, name='propcoach'),
    path('zenbot/', views.zenbot_management, name='zenbot'),
    path('zennews/', views.zennews_management, name='zennews'),
    path('support/', views.support_management, name='support'),
]
