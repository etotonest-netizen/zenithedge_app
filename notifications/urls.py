"""
URL configuration for notifications app
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # API endpoints
    path('api/list/', views.notification_list_api, name='notification_list_api'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
    path('api/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('api/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    
    # Preferences
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),
    path('api/update-preferences/', views.update_preferences, name='update_preferences'),
]
