from django.urls import path
from . import views

app_name = 'bot'

urlpatterns = [
    path('chat/', views.chat_api, name='chat_api'),
    path('ask/', views.bot_ask, name='bot_ask'),  # New slash command endpoint
    path('history/', views.conversation_history, name='conversation_history'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin/clear-conversations/', views.clear_conversations, name='clear_conversations'),
    path('admin/retrain/', views.retrain_bot, name='retrain_bot'),
    path('admin/update-settings/', views.update_settings, name='update_settings'),
]
