from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    # User URLs
    path('', views.support_list, name='list'),
    path('create/', views.support_create_thread, name='create_thread'),
    path('<int:thread_id>/', views.support_thread_detail, name='thread_detail'),
    path('<int:thread_id>/send/', views.support_send_message, name='send_message'),
    
    # Admin URLs
    path('admin/inbox/', views.admin_support_inbox, name='admin_inbox'),
    path('admin/<int:thread_id>/', views.admin_support_thread_detail, name='admin_thread_detail'),
    path('admin/<int:thread_id>/send/', views.admin_send_message, name='admin_send_message'),
    path('admin/<int:thread_id>/close/', views.admin_close_thread, name='admin_close_thread'),
    path('admin/<int:thread_id>/reopen/', views.admin_reopen_thread, name='admin_reopen_thread'),
    
    # API
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
]
