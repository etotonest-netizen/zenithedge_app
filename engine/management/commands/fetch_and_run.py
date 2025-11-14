"""
Django Management Command: fetch_and_run
=========================================
Fetch latest market data and run all strategy detectors.

This command is designed to be run by cron every 1-5 minutes.

Usage:
    python manage.py fetch_and_run --settings=zenithedge.settings_production

Cron example (every 5 minutes):
    */5 * * * * cd ~/etotonest.com && python manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch latest market data and run strategy detectors (for cron)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            default='EURUSD,GBPUSD,USDJPY,AUDUSD,BTCUSD',
            help='Comma-separated list of symbols (default: major pairs + BTC)'
        )
        parser.add_argument(
            '--timeframes',
            type=str,
            default='15m,1H,4H',
            help='Comma-separated list of timeframes (default: 15m,1H,4H)'
        )
        parser.add_argument(
            '--strategies',
            type=str,
            default='all',
            help='Comma-separated strategy names or "all" (default: all)'
        )
        parser.add_argument(
            '--lookback',
            type=int,
            default=200,
            help='Number of bars to fetch (default: 200)'
        )
        parser.add_argument(
            '--create-signals',
            action='store_true',
            help='Create Signal entries in database (default: False, only log)'
        )
        parser.add_argument(
            '--score-signals',
            action='store_true',
            help='Score signals with ZenBot (default: False)'
        )
    
    def handle(self, *args, **options):
        from engine.models import MarketBar
        from engine.strategies import detect_all_strategies
        from adapters.tv_historical import fetch_historical_data
        
        start_time = timezone.now()
        self.stdout.write(f"\n🚀 Engine Pipeline Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Parse arguments
        symbols = [s.strip() for s in options['symbols'].split(',')]
        timeframes = [tf.strip() for tf in options['timeframes'].split(',')]
        
        if options['strategies'] == 'all':
            strategies = None  # Run all strategies
        else:
            strategies = [s.strip() for s in options['strategies'].split(',')]
        
        total_signals = 0
        total_bars_fetched = 0
        errors = []
        
        # Process each symbol x timeframe combination
        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    self.stdout.write(f"📊 Processing {symbol} {timeframe}...")
                    
                    # Fetch latest data
                    bars_fetched = self._fetch_and_store_data(
                        symbol, timeframe, options['lookback']
                    )
                    total_bars_fetched += bars_fetched
                    
                    if bars_fetched == 0:
                        self.stdout.write(f"   ⚠️  No new data for {symbol} {timeframe}")
                        continue
                    
                    # Get data for detection (last 200 bars)
                    bars = MarketBar.objects.filter(
                        symbol=symbol,
                        timeframe=timeframe
                    ).order_by('-timestamp')[:200]
                    
                    if not bars:
                        self.stdout.write(f"   ⚠️  No historical data for {symbol} {timeframe}")
                        continue
                    
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
                    
                    if signals:
                        self.stdout.write(f"   ✅ Detected {len(signals)} signals")
                        total_signals += len(signals)
                        
                        # Create Signal entries if requested
                        if options['create_signals']:
                            created = self._create_signal_entries(
                                signals, symbol, timeframe, options['score_signals']
                            )
                            self.stdout.write(f"   💾 Created {created} Signal entries")
                    else:
                        self.stdout.write(f"   📉 No signals detected")
                    
                except Exception as e:
                    error_msg = f"Error processing {symbol} {timeframe}: {str(e)}"
                    self.stdout.write(self.style.ERROR(f"   ❌ {error_msg}"))
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)
        
        # Summary
        execution_time = (timezone.now() - start_time).total_seconds()
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("PIPELINE SUMMARY")
        self.stdout.write("="*60)
        self.stdout.write(f"Symbols Processed: {len(symbols)}")
        self.stdout.write(f"Timeframes: {len(timeframes)}")
        self.stdout.write(f"Total Combinations: {len(symbols) * len(timeframes)}")
        self.stdout.write(f"Bars Fetched: {total_bars_fetched}")
        self.stdout.write(f"Signals Detected: {total_signals}")
        self.stdout.write(f"Errors: {len(errors)}")
        self.stdout.write(f"Execution Time: {execution_time:.2f}s")
        self.stdout.write("="*60 + "\n")
        
        if errors:
            self.stdout.write(self.style.WARNING("\n⚠️  ERRORS:"))
            for error in errors:
                self.stdout.write(f"   - {error}")
            self.stdout.write("")
        
        if total_signals > 0:
            self.stdout.write(self.style.SUCCESS("✅ Pipeline Complete - Signals Detected!\n"))
        else:
            self.stdout.write("✅ Pipeline Complete - No Signals\n")
    
    def _fetch_and_store_data(self, symbol: str, timeframe: str, lookback: int) -> int:
        """
        Fetch latest data and store in database.
        
        Returns:
            Number of new bars added
        """
        from engine.models import MarketBar
        from adapters.tv_historical import fetch_historical_data
        from decimal import Decimal
        
        try:
            # Calculate date range
            end_date = timezone.now()
            
            # Map timeframe to days of data needed
            tf_days = {
                '1m': 2, '5m': 7, '15m': 14, '30m': 30,
                '1H': 60, '4H': 180, 'D': 365
            }
            days_needed = tf_days.get(timeframe, 60)
            start_date = end_date - timedelta(days=days_needed)
            
            # Fetch data
            df = fetch_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                return 0
            
            # Store in database (skip duplicates)
            new_bars = 0
            
            for timestamp, row in df.iterrows():
                # Check if bar already exists
                exists = MarketBar.objects.filter(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp
                ).exists()
                
                if not exists:
                    MarketBar.objects.create(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=timestamp,
                        open=Decimal(str(row['open'])),
                        high=Decimal(str(row['high'])),
                        low=Decimal(str(row['low'])),
                        close=Decimal(str(row['close'])),
                        volume=Decimal(str(row['volume'])),
                    )
                    new_bars += 1
            
            return new_bars
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol} {timeframe}: {e}")
            return 0
    
    def _create_signal_entries(
        self,
        signals: list,
        symbol: str,
        timeframe: str,
        score_signals: bool
    ) -> int:
        """
        Create Signal entries in database.
        
        Returns:
            Number of signals created
        """
        from signals.models import Signal
        from engine.scoring import score_and_save
        from django.contrib.auth import get_user_model
        from decimal import Decimal
        import json
        
        User = get_user_model()
        
        # Get or create engine user
        engine_user, _ = User.objects.get_or_create(
            username='engine_bot',
            defaults={
                'email': 'engine@zenithedge.local',
                'first_name': 'Engine',
                'last_name': 'Bot',
            }
        )
        
        created_count = 0
        
        for signal_data in signals:
            try:
                # Extract signal fields
                side = signal_data.get('side', 'BUY')
                price = signal_data.get('price', 0)
                sl = signal_data.get('sl', 0)
                tp = signal_data.get('tp', 0)
                confidence = signal_data.get('confidence', 50)
                strategy = signal_data.get('strategy', 'Unknown')
                regime = signal_data.get('regime', 'Unknown')
                entry_reason = signal_data.get('entry_reason', '')
                
                # Create Signal
                signal = Signal.objects.create(
                    user=engine_user,
                    symbol=symbol,
                    side=side,
                    price=Decimal(str(price)),
                    sl=Decimal(str(sl)),
                    tp=Decimal(str(tp)),
                    confidence=confidence,
                    strategy=strategy,
                    regime=regime,
                    timestamp=timezone.now(),
                    received_at=timezone.now(),
                    webhook_raw=json.dumps(signal_data),
                    is_live_trade=False,  # Engine signals are paper trades by default
                )
                
                created_count += 1
                
                # Score signal if requested
                if score_signals:
                    try:
                        ai_score, trade_score = score_and_save(signal, signal_data)
                        logger.info(f"Scored signal {signal.id}: {ai_score}/100")
                    except Exception as e:
                        logger.error(f"Failed to score signal {signal.id}: {e}")
                
            except Exception as e:
                logger.error(f"Failed to create signal: {e}")
        
        return created_count
