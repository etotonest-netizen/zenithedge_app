"""
ZenithMentor URL Configuration
"""
from django.urls import path
from . import views

app_name = 'zenithmentor'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Curriculum
    path('curriculum/', views.curriculum, name='curriculum'),
    path('lesson/<uuid:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    
    # Scenarios
    path('scenarios/', views.scenario_list, name='scenario_list'),
    
    # Simulation
    path('simulation/launch/', views.launch_simulation, name='launch_simulation'),
    path('simulation/<uuid:simulation_id>/', views.simulation_replay, name='simulation_replay'),
    path('simulation/<uuid:simulation_id>/results/', views.simulation_results, name='simulation_results'),
    
    # Trading actions (API endpoints)
    path('api/trade/submit/', views.submit_trade, name='submit_trade'),
    path('api/trade/close/', views.close_trade, name='close_trade'),
    path('api/journal/add/', views.add_journal_entry, name='add_journal'),
    path('api/simulation/complete/', views.complete_simulation, name='complete_simulation'),
    
    # Progress & Reports
    path('progress/', views.progress_report, name='progress_report'),
    path('badges/', views.badges, name='badges'),
]
