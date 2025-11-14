from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

from .models import BacktestRun
from .backtester import TradeBacktester
from signals.models import Signal


@login_required
def backtest_form(request):
    """
    Display the backtest form with filters.
    """
    # Get unique values for dropdowns
    strategies = Signal.objects.filter(
        user=request.user
    ).values_list('strategy', flat=True).distinct().order_by('strategy')
    
    symbols = Signal.objects.filter(
        user=request.user
    ).values_list('symbol', flat=True).distinct().order_by('symbol')
    
    timeframes = Signal.objects.filter(
        user=request.user
    ).values_list('timeframe', flat=True).distinct().order_by('timeframe')
    
    # Get date range from signals
    signals_qs = Signal.objects.filter(user=request.user)
    if signals_qs.exists():
        earliest = signals_qs.earliest('received_at').received_at
        latest = signals_qs.latest('received_at').received_at
    else:
        earliest = timezone.now() - timedelta(days=30)
        latest = timezone.now()
    
    # Get recent saved backtests
    saved_backtests = BacktestRun.objects.filter(
        user=request.user,
        is_saved=True
    )[:10]
    
    context = {
        'strategies': strategies,
        'symbols': symbols,
        'timeframes': timeframes,
        'earliest_date': earliest.date() if earliest else None,
        'latest_date': latest.date() if latest else None,
        'saved_backtests': saved_backtests,
        'total_signals': signals_qs.count(),
    }
    
    return render(request, 'analytics/backtest_form.html', context)


@login_required
@require_http_methods(["POST"])
def backtest_run(request):
    """
    Execute a backtest based on form parameters.
    """
    # Get form parameters
    strategy = request.POST.get('strategy', '')
    symbol = request.POST.get('symbol', '')
    timeframe = request.POST.get('timeframe', '')
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        if end_date:
            end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Additional filters
    filters = {}
    min_score = request.POST.get('min_score')
    if min_score:
        try:
            filters['min_score'] = int(min_score)
        except ValueError:
            pass
    
    ignore_news = request.POST.get('ignore_news') == 'on'
    filters['ignore_news'] = ignore_news
    
    # Run backtest
    backtester = TradeBacktester(request.user)
    results = backtester.run(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        filters=filters
    )
    
    # Save backtest run
    backtest_run = BacktestRun.objects.create(
        user=request.user,
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date.date() if start_date else timezone.now().date(),
        end_date=end_date.date() if end_date else timezone.now().date(),
        params=filters,
        total_trades=results['total_trades'],
        winning_trades=results['winning_trades'],
        losing_trades=results['losing_trades'],
        win_rate=results['win_rate'],
        avg_rr=results['avg_rr'],
        max_drawdown=results['max_drawdown'],
        profit_factor=results['profit_factor'],
        total_pnl=results['total_pnl'],
        equity_curve=results['equity_curve'],
        trade_details=results['trade_details'],
    )
    
    # Redirect to results page
    return redirect('backtest_results', backtest_id=backtest_run.id)


@login_required
def backtest_results(request, backtest_id):
    """
    Display backtest results with charts and trade details.
    """
    backtest = get_object_or_404(BacktestRun, id=backtest_id, user=request.user)
    
    # Calculate additional metrics for display
    summary = backtest.get_summary()
    
    # Prepare chart data
    equity_labels = [point['date'] for point in backtest.equity_curve]
    equity_data = [point['equity'] for point in backtest.equity_curve]
    
    # Calculate win/loss distribution by day
    trades_by_date = {}
    for trade in backtest.trade_details:
        date = trade['date'].split(' ')[0]  # Get date part only
        if date not in trades_by_date:
            trades_by_date[date] = {'wins': 0, 'losses': 0}
        
        if trade['outcome'] == 'win':
            trades_by_date[date]['wins'] += 1
        elif trade['outcome'] == 'loss':
            trades_by_date[date]['losses'] += 1
    
    winloss_labels = list(trades_by_date.keys())
    winloss_wins = [trades_by_date[d]['wins'] for d in winloss_labels]
    winloss_losses = [trades_by_date[d]['losses'] for d in winloss_labels]
    
    ending_equity = backtest.equity_curve[-1]['equity'] if backtest.equity_curve else 10000
    
    context = {
        'backtest': backtest,
        'summary': summary,
        'equity_labels': json.dumps(equity_labels),
        'equity_data': json.dumps(equity_data),
        'winloss_labels': json.dumps(winloss_labels),
        'winloss_wins': json.dumps(winloss_wins),
        'winloss_losses': json.dumps(winloss_losses),
        'starting_capital': backtest.equity_curve[0]['equity'] if backtest.equity_curve else 10000,
        'ending_equity': ending_equity,
    }
    
    return render(request, 'analytics/backtest_results.html', context)


@login_required
@require_http_methods(["POST"])
def backtest_save(request, backtest_id):
    """
    Mark a backtest as saved and optionally give it a name.
    """
    backtest = get_object_or_404(BacktestRun, id=backtest_id, user=request.user)
    
    name = request.POST.get('name', '')
    backtest.is_saved = True
    if name:
        backtest.name = name
    backtest.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Backtest saved successfully'
    })


@login_required
def backtest_export_csv(request, backtest_id):
    """
    Export backtest trade details as CSV.
    """
    backtest = get_object_or_404(BacktestRun, id=backtest_id, user=request.user)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="backtest_{backtest_id}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Date', 'Symbol', 'Side', 'Entry', 'Stop Loss', 'Take Profit',
        'RR Ratio', 'Outcome', 'P&L', 'Equity', 'AI Score', 'Strategy'
    ])
    
    # Write trade data
    for trade in backtest.trade_details:
        writer.writerow([
            trade['date'],
            trade['symbol'],
            trade['side'],
            trade['entry'],
            trade['sl'],
            trade['tp'],
            trade['rr'],
            trade['outcome'],
            trade['pnl'],
            trade['equity'],
            trade['ai_score'],
            trade['strategy'],
        ])
    
    return response


@login_required
def backtest_detail(request, backtest_id):
    """
    View a saved backtest by ID.
    """
    return backtest_results(request, backtest_id)


@login_required
def backtest_list(request):
    """
    List all saved backtests.
    """
    backtests = BacktestRun.objects.filter(user=request.user, is_saved=True)
    
    context = {
        'backtests': backtests,
    }
    
    return render(request, 'analytics/backtest_list.html', context)


@login_required
@require_http_methods(["DELETE", "POST"])
def backtest_delete(request, backtest_id):
    """
    Delete a backtest run.
    """
    backtest = get_object_or_404(BacktestRun, id=backtest_id, user=request.user)
    backtest.delete()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Backtest deleted successfully'
    })
