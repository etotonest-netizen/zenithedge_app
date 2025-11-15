"""
Engine API Views
================
REST API endpoints for engine features.
"""

import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def engine_dashboard(request):
    """Engine dashboard homepage - returns JSON or HTML based on Accept header"""
    from engine.models import BacktestRun, MarketBar
    
    stats = {
        'total_backtests': BacktestRun.objects.count(),
        'completed_backtests': BacktestRun.objects.filter(status='completed').count(),
        'market_bars_count': MarketBar.objects.count(),
        'engine_version': '2.0.0',
        'status': 'operational',
    }
    
    # If requesting JSON or if template doesn't exist, return JSON
    if request.META.get('HTTP_ACCEPT', '').startswith('application/json') or 'curl' in request.META.get('HTTP_USER_AGENT', '').lower():
        return JsonResponse({
            'status': 'success',
            'message': 'Trading Engine Dashboard',
            'stats': stats,
            'api_endpoints': {
                'status': '/engine/api/status/',
                'latest_visuals': '/engine/api/visuals/latest/?symbol=EURUSD',
                'signal_visuals': '/engine/api/visuals/{signal_id}/',
                'backtest_visuals': '/engine/api/visuals/backtest/{backtest_id}/',
                'trigger_detection': '/engine/api/detect/',
            },
            'admin_links': {
                'backtests': '/admin/engine/backtestrun/',
                'market_bars': '/admin/engine/marketbar/',
                'backtest_trades': '/admin/engine/backtesttrade/',
            }
        })
    
    # Otherwise try to render HTML template
    try:
        return render(request, 'engine/dashboard.html', {'stats': stats})
    except Exception as e:
        # Fallback to JSON if template missing, but log the error
        logger.error(f"Template rendering failed: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Trading Engine Dashboard (Template error: {str(e)})',
            'stats': stats,
        })


@csrf_exempt
@require_http_methods(["GET"])
def get_latest_visuals(request):
    """
    Get visual overlays for the latest signal.
    
    Query params:
        - symbol: Trading symbol (e.g., EURUSD)
        - timeframe: Optional timeframe filter
        - token: Authentication token (or use session auth)
    
    Returns:
        JSON with visual elements (boxes, lines, markers, labels, arrows)
    """
    try:
        from signals.models import Signal
        from engine.visuals import generate_signal_visuals, export_to_json
        
        # Get query params
        symbol = request.GET.get('symbol')
        timeframe = request.GET.get('timeframe')
        token = request.GET.get('token')
        
        if not symbol:
            return JsonResponse({
                'status': 'error',
                'message': 'Symbol parameter is required'
            }, status=400)
        
        # Authenticate via token or session
        user = None
        if token:
            # Token-based auth
            from signals.models import Signal
            # Simple token check - you can enhance this
            if token != request.user.auth_token if hasattr(request.user, 'auth_token') else None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid token'
                }, status=401)
            user = request.user
        elif request.user.is_authenticated:
            user = request.user
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Authentication required'
            }, status=401)
        
        # Query latest signal
        query = Signal.objects.filter(user=user, symbol=symbol)
        
        if timeframe:
            query = query.filter(timeframe=timeframe)
        
        latest_signal = query.order_by('-received_at').first()
        
        if not latest_signal:
            return JsonResponse({
                'status': 'success',
                'message': f'No signals found for {symbol}',
                'visuals': None
            })
        
        # Get strategy metadata from signal's webhook_raw
        strategy_metadata = {}
        if hasattr(latest_signal, 'webhook_raw') and latest_signal.webhook_raw:
            import json
            try:
                webhook_data = json.loads(latest_signal.webhook_raw)
                strategy_metadata = webhook_data.get('metadata', {})
            except:
                pass
        
        # If no webhook data, try to get from engine detection
        if not strategy_metadata and hasattr(latest_signal, 'ai_metadata'):
            strategy_metadata = latest_signal.ai_metadata or {}
        
        # Generate visuals
        visuals = generate_signal_visuals(latest_signal, strategy_metadata)
        json_output = export_to_json(visuals)
        
        return JsonResponse({
            'status': 'success',
            'signal_id': latest_signal.id,
            'symbol': symbol,
            'timeframe': latest_signal.timeframe if hasattr(latest_signal, 'timeframe') else None,
            'timestamp': latest_signal.timestamp.isoformat() if latest_signal.timestamp else None,
            'visuals': json_output
        })
        
    except Exception as e:
        logger.error(f"Error in get_latest_visuals: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_signal_visuals(request, signal_id):
    """
    Get visual overlays for a specific signal by ID.
    
    Args:
        signal_id: Signal ID
    
    Returns:
        JSON with visual elements
    """
    try:
        from signals.models import Signal
        from engine.visuals import generate_signal_visuals, export_to_json
        
        # Get signal
        signal = Signal.objects.filter(id=signal_id).first()
        
        if not signal:
            return JsonResponse({
                'status': 'error',
                'message': f'Signal {signal_id} not found'
            }, status=404)
        
        # Check permissions
        if not request.user.is_authenticated or signal.user != request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Unauthorized'
            }, status=403)
        
        # Get strategy metadata
        strategy_metadata = {}
        if hasattr(signal, 'webhook_raw') and signal.webhook_raw:
            import json
            try:
                webhook_data = json.loads(signal.webhook_raw)
                strategy_metadata = webhook_data.get('metadata', {})
            except:
                pass
        
        if not strategy_metadata and hasattr(signal, 'ai_metadata'):
            strategy_metadata = signal.ai_metadata or {}
        
        # Generate visuals
        visuals = generate_signal_visuals(signal, strategy_metadata)
        json_output = export_to_json(visuals)
        
        return JsonResponse({
            'status': 'success',
            'signal_id': signal.id,
            'symbol': signal.symbol,
            'visuals': json_output
        })
        
    except Exception as e:
        logger.error(f"Error in get_signal_visuals: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_backtest_visuals(request, backtest_id):
    """
    Get visual overlays for a backtest run.
    
    Args:
        backtest_id: BacktestRun ID
    
    Returns:
        JSON with equity curve, trades, and statistics
    """
    try:
        from engine.models import BacktestRun, BacktestTrade
        from engine.visuals import generate_backtest_visuals
        
        # Get backtest run
        backtest = BacktestRun.objects.filter(id=backtest_id).first()
        
        if not backtest:
            return JsonResponse({
                'status': 'error',
                'message': f'Backtest {backtest_id} not found'
            }, status=404)
        
        # Get all trades
        trades = BacktestTrade.objects.filter(backtest_run=backtest).order_by('entry_time')
        
        # Convert to dict format
        trades_data = [
            {
                'entry_time': trade.entry_time.isoformat(),
                'entry_price': float(trade.entry_price),
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'exit_price': float(trade.exit_price) if trade.exit_price else None,
                'side': trade.side,
                'pnl': float(trade.pnl) if trade.pnl else 0,
            }
            for trade in trades
        ]
        
        # Generate visuals
        visuals = generate_backtest_visuals(trades_data)
        
        return JsonResponse({
            'status': 'success',
            'backtest_id': backtest.id,
            'symbol': backtest.symbol,
            'timeframe': backtest.timeframe,
            'strategy': backtest.strategy,
            'date_range': f"{backtest.start_date} to {backtest.end_date}",
            'visuals': visuals
        })
        
    except Exception as e:
        logger.error(f"Error in get_backtest_visuals: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_engine_status(request):
    """
    Get engine status and statistics.
    
    Returns:
        JSON with engine health and recent activity
    """
    try:
        from engine.models import MarketBar, BacktestRun
        from signals.models import Signal
        from django.utils import timezone
        
        # Get recent activity (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        
        recent_bars = MarketBar.objects.filter(timestamp__gte=yesterday).count()
        recent_signals = Signal.objects.filter(received_at__gte=yesterday).count()
        recent_backtests = BacktestRun.objects.filter(created_at__gte=yesterday).count()
        
        # Get latest bars by symbol
        latest_bars = {}
        symbols = MarketBar.objects.values_list('symbol', flat=True).distinct()[:10]
        
        for symbol in symbols:
            latest = MarketBar.objects.filter(symbol=symbol).order_by('-timestamp').first()
            if latest:
                latest_bars[symbol] = {
                    'timestamp': latest.timestamp.isoformat(),
                    'close': float(latest.close),
                    'timeframe': latest.timeframe,
                }
        
        return JsonResponse({
            'status': 'success',
            'engine_version': '1.0.0',
            'uptime': 'Running',
            'recent_activity': {
                'bars_added_24h': recent_bars,
                'signals_generated_24h': recent_signals,
                'backtests_run_24h': recent_backtests,
            },
            'latest_bars': latest_bars,
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Error in get_engine_status: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def trigger_detection(request):
    """
    Manually trigger signal detection for a symbol/timeframe.
    
    POST data:
        - symbol: Trading symbol
        - timeframe: Timeframe (e.g., '1H')
        - strategies: Optional list of strategy names
    
    Returns:
        JSON with detected signals
    """
    try:
        import json
        from engine.strategies import detect_all_strategies
        from engine.models import MarketBar
        from signals.models import Signal
        import pandas as pd
        
        # Parse request body
        data = json.loads(request.body)
        symbol = data.get('symbol')
        timeframe = data.get('timeframe', '1H')
        strategies = data.get('strategies')  # None = all strategies
        
        if not symbol:
            return JsonResponse({
                'status': 'error',
                'message': 'Symbol is required'
            }, status=400)
        
        # Get recent bars (last 200)
        bars = MarketBar.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp')[:200]
        
        if not bars:
            return JsonResponse({
                'status': 'error',
                'message': f'No market data found for {symbol} {timeframe}'
            }, status=404)
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': float(bar.volume),
            }
            for bar in reversed(list(bars))
        ])
        df.set_index('timestamp', inplace=True)
        
        # Run detection
        signals = detect_all_strategies(df, symbol, timeframe, strategies)
        
        logger.info(f"Manual detection for {symbol} {timeframe}: {len(signals)} signals")
        
        return JsonResponse({
            'status': 'success',
            'symbol': symbol,
            'timeframe': timeframe,
            'bars_analyzed': len(df),
            'signals_detected': len(signals),
            'signals': signals
        })
        
    except Exception as e:
        logger.error(f"Error in trigger_detection: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
