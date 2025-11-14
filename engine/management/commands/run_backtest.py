"""
Django Management Command: run_backtest
========================================
Run backtests from command line.

Usage:
    python manage.py run_backtest --strategy=SMC --symbol=EURUSD --timeframe=1H \\
        --start=2024-01-01 --end=2024-11-01 --save
"""

from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
import pandas as pd


class Command(BaseCommand):
    help = 'Run backtest for a strategy on historical data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            required=True,
            help='Strategy name (SMC, ICT, Trend, Breakout, etc.)'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            required=True,
            help='Trading symbol (e.g., EURUSD)'
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            default='1H',
            help='Timeframe (1m, 5m, 15m, 30m, 1H, 4H, D)'
        )
        parser.add_argument(
            '--start',
            type=str,
            required=True,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end',
            type=str,
            required=True,
            help='End date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--balance',
            type=float,
            default=10000.0,
            help='Initial balance (default: 10000)'
        )
        parser.add_argument(
            '--risk',
            type=float,
            default=1.0,
            help='Risk per trade percentage (default: 1.0)'
        )
        parser.add_argument(
            '--commission',
            type=float,
            default=0.0,
            help='Commission percentage (default: 0.0)'
        )
        parser.add_argument(
            '--slippage',
            type=float,
            default=0.0,
            help='Slippage in pips (default: 0.0)'
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save results to database'
        )
        parser.add_argument(
            '--fetch',
            action='store_true',
            help='Fetch fresh data from yfinance (instead of using database)'
        )
    
    def handle(self, *args, **options):
        from engine.backtest import BacktestEngine
        from engine.strategies import STRATEGY_DETECTORS
        from engine.models import MarketBar
        from adapters.tv_historical import fetch_historical_data
        
        strategy_name = options['strategy']
        symbol = options['symbol']
        timeframe = options['timeframe']
        start_date = datetime.strptime(options['start'], '%Y-%m-%d')
        end_date = datetime.strptime(options['end'], '%Y-%m-%d')
        
        self.stdout.write(f"\n🚀 Starting Backtest")
        self.stdout.write(f"   Strategy: {strategy_name}")
        self.stdout.write(f"   Symbol: {symbol}")
        self.stdout.write(f"   Timeframe: {timeframe}")
        self.stdout.write(f"   Period: {start_date.date()} to {end_date.date()}")
        self.stdout.write(f"   Balance: ${options['balance']:.2f}")
        self.stdout.write(f"   Risk: {options['risk']}% per trade\n")
        
        # Get strategy detector
        if strategy_name not in STRATEGY_DETECTORS:
            raise CommandError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {', '.join(STRATEGY_DETECTORS.keys())}"
            )
        
        detector_class = STRATEGY_DETECTORS[strategy_name]
        detector = detector_class()
        
        # Get historical data
        if options['fetch']:
            self.stdout.write("📡 Fetching fresh data from yfinance...")
            df = fetch_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                raise CommandError("Failed to fetch historical data")
            
            self.stdout.write(f"✅ Fetched {len(df)} bars\n")
        else:
            self.stdout.write("📊 Loading data from database...")
            
            # Query database
            bars = MarketBar.objects.filter(
                symbol=symbol,
                timeframe=timeframe,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if not bars.exists():
                raise CommandError(
                    f"No data found in database for {symbol} {timeframe}. "
                    "Use --fetch to download from yfinance."
                )
            
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
                for bar in bars
            ])
            df.set_index('timestamp', inplace=True)
            
            self.stdout.write(f"✅ Loaded {len(df)} bars from database\n")
        
        # Create backtester
        engine = BacktestEngine(
            initial_balance=options['balance'],
            risk_per_trade_pct=options['risk'],
            commission_pct=options['commission'],
            slippage_pips=options['slippage'],
        )
        
        # Run backtest
        self.stdout.write("⚙️  Running backtest...\n")
        
        results = engine.run_backtest(
            df=df,
            symbol=symbol,
            timeframe=timeframe,
            strategy_detector=detector,
            strategy_name=strategy_name
        )
        
        # Display results
        self._display_results(results)
        
        # Save to database if requested
        if options['save']:
            self.stdout.write("\n💾 Saving results to database...")
            backtest_run = engine.save_to_database(results)
            
            if backtest_run:
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Saved as BacktestRun #{backtest_run.id}"
                ))
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to save results"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Backtest Complete!\n"))
    
    def _display_results(self, results: dict):
        """Display backtest results in formatted output."""
        metrics = results['metrics']
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("BACKTEST RESULTS")
        self.stdout.write("="*60 + "\n")
        
        # Overview
        self.stdout.write("📊 OVERVIEW:")
        self.stdout.write(f"   Symbol: {results['symbol']}")
        self.stdout.write(f"   Timeframe: {results['timeframe']}")
        self.stdout.write(f"   Strategy: {results['strategy']}")
        self.stdout.write(f"   Period: {results['start_date']} to {results['end_date']}")
        self.stdout.write(f"   Bars Processed: {results['bars_processed']}")
        self.stdout.write(f"   Execution Time: {results['execution_time_sec']:.2f}s\n")
        
        # Performance
        self.stdout.write("💰 PERFORMANCE:")
        self.stdout.write(f"   Initial Balance: ${results['initial_balance']:.2f}")
        self.stdout.write(f"   Final Balance: ${results['final_balance']:.2f}")
        
        net_profit = metrics['net_profit']
        profit_color = self.style.SUCCESS if net_profit > 0 else self.style.ERROR
        self.stdout.write(profit_color(
            f"   Net Profit: ${net_profit:.2f} ({metrics['return_pct']:.2f}%)"
        ))
        self.stdout.write(f"   Expectancy: ${metrics['expectancy']:.2f} per trade\n")
        
        # Trade Statistics
        self.stdout.write("📈 TRADE STATISTICS:")
        self.stdout.write(f"   Total Trades: {metrics['total_trades']}")
        self.stdout.write(f"   Winning Trades: {metrics['winning_trades']}")
        self.stdout.write(f"   Losing Trades: {metrics['losing_trades']}")
        
        win_rate = metrics['win_rate']
        wr_color = self.style.SUCCESS if win_rate >= 50 else self.style.WARNING
        self.stdout.write(wr_color(f"   Win Rate: {win_rate:.2f}%"))
        
        self.stdout.write(f"   Average Win: ${metrics['avg_win']:.2f}")
        self.stdout.write(f"   Average Loss: ${metrics['avg_loss']:.2f}")
        self.stdout.write(f"   Largest Win: ${metrics['largest_win']:.2f}")
        self.stdout.write(f"   Largest Loss: ${metrics['largest_loss']:.2f}")
        
        pf = metrics['profit_factor']
        pf_color = self.style.SUCCESS if pf > 1.5 else self.style.WARNING
        self.stdout.write(pf_color(f"   Profit Factor: {pf:.2f}"))
        
        self.stdout.write(f"   Max Consecutive Wins: {metrics['max_consecutive_wins']}")
        self.stdout.write(f"   Max Consecutive Losses: {metrics['max_consecutive_losses']}")
        self.stdout.write(f"   Avg Trade Duration: {metrics['avg_trade_duration_bars']:.1f} bars\n")
        
        # Risk Metrics
        self.stdout.write("⚠️  RISK METRICS:")
        
        max_dd = metrics['max_drawdown_pct']
        dd_color = self.style.WARNING if max_dd > 10 else self.style.SUCCESS
        self.stdout.write(dd_color(f"   Max Drawdown: {max_dd:.2f}%"))
        
        sharpe = metrics['sharpe_ratio']
        sharpe_color = self.style.SUCCESS if sharpe > 1.0 else self.style.WARNING
        self.stdout.write(sharpe_color(f"   Sharpe Ratio: {sharpe:.2f}\n"))
        
        # Recent Trades (last 5)
        if results['trades']:
            self.stdout.write("🔍 RECENT TRADES (Last 5):")
            for trade in results['trades'][-5:]:
                pnl = trade['pnl']
                pnl_str = f"${pnl:.2f}"
                pnl_color = self.style.SUCCESS if pnl > 0 else self.style.ERROR
                
                self.stdout.write(
                    f"   {trade['side']} @ {trade['entry_price']:.5f} → "
                    f"{trade['exit_price']:.5f} "
                    f"({trade['exit_reason']}) "
                    + pnl_color(pnl_str)
                )
        
        self.stdout.write("\n" + "="*60)
