from django.urls import path
from . import views

urlpatterns = [
    # Main backtest form
    path('', views.backtest_form, name='backtest_form'),
    
    # Run backtest
    path('run/', views.backtest_run, name='backtest_run'),
    
    # View results
    path('<int:backtest_id>/', views.backtest_results, name='backtest_results'),
    
    # Save backtest
    path('<int:backtest_id>/save/', views.backtest_save, name='backtest_save'),
    
    # Export CSV
    path('<int:backtest_id>/export/', views.backtest_export_csv, name='backtest_export'),
    
    # List saved backtests
    path('saved/', views.backtest_list, name='backtest_list'),
    
    # Delete backtest
    path('<int:backtest_id>/delete/', views.backtest_delete, name='backtest_delete'),
]
