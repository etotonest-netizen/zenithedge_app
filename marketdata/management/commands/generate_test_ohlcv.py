"""
Generate synthetic OHLCV test data for AutopsyLoop testing.

Creates realistic candle data with trends, noise, and occasional volatility spikes.

Usage:
    python manage.py generate_test_ohlcv --symbol EURUSD --days 30 --timeframe 1m
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from marketdata.models import OHLCVCandle, DataSource


class Command(BaseCommand):
    help = 'Generate synthetic OHLCV test data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            default='EURUSD',
            help='Trading symbol (default: EURUSD)'
        )
        
        parser.add_argument(
            '--timeframe',
            default='1m',
            help='Candle timeframe (default: 1m)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to generate (default: 7)'
        )
        
        parser.add_argument(
            '--start-price',
            type=float,
            default=None,
            help='Starting price (default: auto-select based on symbol)'
        )
        
        parser.add_argument(
            '--volatility',
            type=float,
            default=0.0001,
            help='Price volatility (default: 0.0001 = 1 pip for forex)'
        )
    
    def handle(self, *args, **options):
        symbol = options['symbol'].upper()
        timeframe = options['timeframe']
        days = options['days']
        volatility = options['volatility']
        
        # Auto-select starting price based on symbol
        if options['start_price']:
            start_price = Decimal(str(options['start_price']))
        else:
            start_prices = {
                'EURUSD': Decimal('1.0850'),
                'GBPUSD': Decimal('1.2786'),
                'USDJPY': Decimal('149.50'),
                'AUDUSD': Decimal('0.6550'),
                'USDCAD': Decimal('1.3920'),
                'NZDUSD': Decimal('0.5880'),
                'XAUUSD': Decimal('2630.00'),
                'BTCUSD': Decimal('89500.00'),
            }
            start_price = start_prices.get(symbol, Decimal('1.0000'))
        
        # Timeframe to minutes mapping
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        minutes_per_candle = timeframe_minutes.get(timeframe, 1)
        
        # Calculate total candles
        total_minutes = days * 24 * 60
        total_candles = total_minutes // minutes_per_candle
        
        self.stdout.write(f"\n🔬 Generating Test OHLCV Data")
        self.stdout.write(f"{'=' * 50}")
        self.stdout.write(f"Symbol: {symbol}")
        self.stdout.write(f"Timeframe: {timeframe}")
        self.stdout.write(f"Days: {days}")
        self.stdout.write(f"Start Price: {start_price}")
        self.stdout.write(f"Volatility: {volatility}")
        self.stdout.write(f"Total Candles: {total_candles}")
        
        # Get or create data source
        data_source, _ = DataSource.objects.get_or_create(
            name='synthetic_generator',
            defaults={
                'source_type': 'manual',
                'is_active': True
            }
        )
        
        # Generate candles
        candles = []
        current_price = start_price
        start_time = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"\n📦 Generating candles...")
        
        for i in range(total_candles):
            timestamp = start_time + timedelta(minutes=i * minutes_per_candle)
            
            # Generate OHLC with realistic patterns
            open_price = current_price
            
            # Random walk with trend
            trend = random.uniform(-volatility, volatility) * 0.5
            noise = random.uniform(-volatility, volatility)
            
            # Occasional volatility spikes
            if random.random() < 0.05:  # 5% chance
                noise *= random.uniform(2, 5)
            
            close = open_price + Decimal(str(trend + noise))
            
            # High and low
            range_factor = random.uniform(0.5, 2.0)
            high = max(open_price, close) + Decimal(str(abs(noise) * range_factor))
            low = min(open_price, close) - Decimal(str(abs(noise) * range_factor))
            
            # Volume (random but realistic)
            volume = Decimal(str(random.uniform(100, 1000)))
            
            candle = OHLCVCandle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=timestamp,
                open_price=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                source='synthetic_generator'
            )
            candles.append(candle)
            
            # Update current price for next candle
            current_price = close
            
            # Progress indicator
            if (i + 1) % 1000 == 0:
                self.stdout.write(f"   Generated {i + 1}/{total_candles} candles...", ending='\r')
        
        # Bulk create
        self.stdout.write(f"\n\n💾 Saving to database...")
        try:
            created_candles = OHLCVCandle.objects.bulk_create(
                candles,
                batch_size=1000,
                ignore_conflicts=True
            )
            
            created_count = len(created_candles)
            duplicates = len(candles) - created_count
            
            self.stdout.write(f"\n✅ Generation Complete!")
            self.stdout.write(f"   Created: {created_count} candles")
            if duplicates > 0:
                self.stdout.write(f"   Skipped: {duplicates} duplicates")
            
            # Stats
            first = candles[0]
            last = candles[-1]
            price_change = ((last.close - first.open_price) / first.open_price) * 100
            
            self.stdout.write(f"\n📈 Data Summary:")
            self.stdout.write(f"   Start: {first.timestamp.strftime('%Y-%m-%d %H:%M')} @ {first.open_price}")
            self.stdout.write(f"   End: {last.timestamp.strftime('%Y-%m-%d %H:%M')} @ {last.close}")
            self.stdout.write(f"   Price Change: {price_change:+.2f}%")
            
            # Update data source
            data_source.mark_sync_success(candles_synced=created_count)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Failed to save: {e}"))
