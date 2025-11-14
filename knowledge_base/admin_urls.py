"""
Knowledge Base Admin URL Configuration
"""
from django.urls import path
from . import admin_views

app_name = 'kb_admin'

urlpatterns = [
    path('dashboard/', admin_views.kb_dashboard, name='kb_dashboard'),
    path('search-test/', admin_views.kb_search_test, name='kb_search_test'),
    path('regenerate-embeddings/', admin_views.regenerate_embeddings, name='kb_regenerate_embeddings'),
    path('clear-cache/', admin_views.clear_cache, name='kb_clear_cache'),
    path('approval-queue/', admin_views.entry_approval_queue, name='kb_approval_queue'),
    path('statistics/', admin_views.kb_statistics, name='kb_statistics'),
]
