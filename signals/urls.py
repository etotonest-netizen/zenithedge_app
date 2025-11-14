from django.urls import path
from . import views
from .insights_views import insights_dashboard
from .quick_entry_view import quick_entry

app_name = 'signals'

urlpatterns = [
    path('quick-entry/', quick_entry, name='quick_entry'),
    path('insights/', insights_dashboard, name='insights_dashboard'),
    path('api/webhook/', views.signal_webhook, name='signal_webhook'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('insight/<int:pk>/', views.InsightDetailView.as_view(), name='insight_detail'),
    path('webhook-setup/', views.WebhookSetupView.as_view(), name='webhook_setup'),
    path('strategies/', views.StrategyPerformanceView.as_view(), name='strategies'),
    path('journal/', views.JournalListView.as_view(), name='journal_list'),
    path('journal/<int:pk>/', views.JournalDetailView.as_view(), name='journal_detail'),
    path('journal/api/summary/', views.journal_summary_api, name='journal_summary_api'),
    path('journal/ai-review/', views.journal_ai_review, name='journal_ai_review'),
    path('<int:pk>/replay/', views.TradeReplayView.as_view(), name='trade_replay'),
    path('<int:signal_id>/generate-replay/', views.generate_replay_data, name='generate_replay'),
    path('challenge/setup/', views.ChallengeSetupView.as_view(), name='challenge_setup'),
    path('challenge/overview/', views.ChallengeOverviewView.as_view(), name='challenge_overview'),
    path('validation/track-record/', views.ValidationTrackRecordView.as_view(), name='validation_track_record'),
    path('', views.home, name='home'),
]
