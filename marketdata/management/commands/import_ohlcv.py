"""
Management command to import OHLCV data from CSV files.

Usage:
    python manage.py import_ohlcv --csv data.csv --symbol EURUSD --timeframe 1m
    python manage.py import_ohlcv --csv data.csv --symbol GBPUSD --timeframe 5m --source "Oanda API"
"""

from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from datetime import datetime
from marketdata.models import OHLCVCandle, DataSource


class Command(BaseCommand):
    help = 'Import OHLCV data from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            required=True,
            help='Path to CSV file with OHLCV data'
        )
        
        parser.add_argument(
            '--symbol',
            required=True,
            help='Trading symbol (e.g., EURUSD, GBPUSD)'
        )
        
        parser.add_argument(
            '--timeframe',
            default='1m',
            help='Candle timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)'
        )
        
        parser.add_argument(
            '--source',
            default='csv_import',
            help='Data source name'
        )
        
        parser.add_argument(
            '--date-column',
            default='timestamp',
            help='Name of timestamp column in CSV'
        )
        
        parser.add_argument(
            '--date-format',
            default=None,
            help='Date format (e.g., "%%Y-%%m-%%d %%H:%%M:%%S")'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
    
    def handle(self, *args, **options):
        csv_path = options['csv']
        symbol = options['symbol'].upper()
        timeframe = options['timeframe']
        source_name = options['source']
        date_column = options['date_column']
        date_format = options['date_format']
        dry_run = options['dry_run']
        
        self.stdout.write(f"\n📊 Importing OHLCV Data")
        self.stdout.write(f"{'=' * 50}")
        self.stdout.write(f"Symbol: {symbol}")
        self.stdout.write(f"Timeframe: {timeframe}")
        self.stdout.write(f"Source: {source_name}")
        self.stdout.write(f"File: {csv_path}")
        
        # Read CSV
        try:
            df = pd.read_csv(csv_path)
            self.stdout.write(f"\n✅ Loaded CSV with {len(df)} rows")
        except Exception as e:
            raise CommandError(f"Failed to read CSV: {e}")
        
        # Validate columns
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.stdout.write(f"\n📋 Available columns: {list(df.columns)}")
            raise CommandError(f"Missing required columns: {missing_cols}")
        
        if date_column not in df.columns:
            raise CommandError(f"Date column '{date_column}' not found in CSV")
        
        # Parse timestamps
        try:
            if date_format:
                df[date_column] = pd.to_datetime(df[date_column], format=date_format)
            else:
                df[date_column] = pd.to_datetime(df[date_column])
        except Exception as e:
            raise CommandError(f"Failed to parse timestamps: {e}")
        
        # Get or create data source
        if not dry_run:
            data_source, created = DataSource.objects.get_or_create(
                name=source_name,
                defaults={
                    'source_type': 'csv_import',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f"✅ Created data source: {source_name}")
        
        # Prepare candles
        candles = []
        duplicates = 0
        errors = 0
        
        self.stdout.write(f"\n📦 Processing {len(df)} candles...")
        
        for idx, row in df.iterrows():
            try:
                candle = OHLCVCandle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=row[date_column],
                    open_price=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row.get('volume', None),
                    source=source_name
                )
                candles.append(candle)
            except Exception as e:
                errors += 1
                if errors <= 5:  # Show first 5 errors
                    self.stdout.write(f"⚠️  Error at row {idx}: {e}")
        
        if errors > 5:
            self.stdout.write(f"⚠️  ... and {errors - 5} more errors")
        
        # Import candles
        if dry_run:
            self.stdout.write(f"\n🔍 DRY RUN - Would import {len(candles)} candles")
            self.stdout.write(f"   Date range: {df[date_column].min()} to {df[date_column].max()}")
            return
        
        try:
            # Bulk create with ignore_conflicts to skip duplicates
            created_candles = OHLCVCandle.objects.bulk_create(
                candles,
                batch_size=1000,
                ignore_conflicts=True
            )
            
            created_count = len(created_candles)
            duplicates = len(candles) - created_count
            
            self.stdout.write(f"\n✅ Import Complete!")
            self.stdout.write(f"   Created: {created_count} candles")
            if duplicates > 0:
                self.stdout.write(f"   Skipped: {duplicates} duplicates")
            if errors > 0:
                self.stdout.write(f"   Errors: {errors}")
            
            # Update data source stats
            data_source.mark_sync_success(candles_synced=created_count)
            
            self.stdout.write(f"\n📈 Database Stats:")
            total = OHLCVCandle.objects.filter(symbol=symbol, timeframe=timeframe).count()
            self.stdout.write(f"   Total {symbol} {timeframe} candles: {total}")
            
        except Exception as e:
            raise CommandError(f"Failed to import candles: {e}")
