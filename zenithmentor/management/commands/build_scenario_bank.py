"""
Management command to build scenario bank from historical data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import pandas as pd
from datetime import datetime, timedelta
import random

from zenithmentor.models import Scenario
from zenithmentor.scenario_engine import scenario_generator

User = get_user_model()


class Command(BaseCommand):
    help = 'Build scenario bank from historical data or generate synthetic scenarios'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            help='Path to historical OHLCV CSV file',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of scenarios to generate',
        )
        parser.add_argument(
            '--synthetic',
            action='store_true',
            help='Generate synthetic scenarios instead of using CSV',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("Building scenario bank...")
        
        if options['synthetic']:
            self._generate_synthetic_scenarios(options['count'])
        elif options['csv']:
            self._build_from_csv(options['csv'], options['count'])
        else:
            self.stdout.write(self.style.ERROR("Provide --csv or --synthetic"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"Scenario bank built successfully!"))
    
    def _generate_synthetic_scenarios(self, count):
        """Generate synthetic scenarios for testing."""
        self.stdout.write(f"Generating {count} synthetic scenarios...")
        
        strategies = ['trend', 'breakout', 'mean_reversion', 'smc', 'scalping']
        regimes = ['trending_bull', 'trending_bear', 'ranging', 'high_volatility', 'breakout']
        
        admin_user = User.objects.filter(is_staff=True).first()
        
        for i in range(count):
            # Generate synthetic candle data
            candle_data = self._generate_synthetic_candles(100)
            
            strategy = random.choice(strategies)
            regime = random.choice(regimes)
            difficulty = random.randint(1, 10)
            
            scenario_dict = scenario_generator.create_scenario_from_historical(
                df=pd.DataFrame(candle_data),
                name=f"Scenario #{i+1}: {regime.replace('_', ' ').title()}",
                strategy_focus=strategy,
                regime=regime,
                difficulty=difficulty,
                inject_news=random.choice([True, False]),
            )
            
            scenario_dict['created_by'] = admin_user
            
            Scenario.objects.create(**scenario_dict)
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f"  Created {i+1}/{count} scenarios")
    
    def _generate_synthetic_candles(self, count):
        """Generate synthetic OHLCV data."""
        from django.utils import timezone
        candles = []
        price = 1.1000
        timestamp = timezone.now() - timedelta(hours=count)
        
        for i in range(count):
            # Random walk
            change = random.uniform(-0.0020, 0.0020)
            price += change
            
            open_price = price
            high = price + random.uniform(0, 0.0015)
            low = price - random.uniform(0, 0.0015)
            close = price + random.uniform(-0.0010, 0.0010)
            
            candles.append({
                'timestamp': timestamp + timedelta(minutes=15 * i),
                'open': round(open_price, 5),
                'high': round(high, 5),
                'low': round(low, 5),
                'close': round(close, 5),
                'volume': random.randint(1000, 10000),
            })
            
            price = close
        
        return candles
    
    def _build_from_csv(self, csv_path, count):
        """Build scenarios from CSV file."""
        self.stdout.write(f"Loading data from {csv_path}...")
        
        try:
            df = pd.read_csv(csv_path)
            
            # Validate columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                self.stdout.write(self.style.ERROR(
                    f"CSV must contain columns: {required_cols}"
                ))
                return
            
            self.stdout.write(f"Loaded {len(df)} candles")
            
            # Sample windows
            admin_user = User.objects.filter(is_staff=True).first()
            
            strategies = ['trend', 'breakout', 'mean_reversion', 'smc', 'scalping']
            
            for i in range(count):
                # Sample random window
                window_df = scenario_generator.sample_historical_window(
                    df, window_size_candles=100
                )
                
                strategy = random.choice(strategies)
                difficulty = random.randint(1, 10)
                
                scenario_dict = scenario_generator.create_scenario_from_historical(
                    df=window_df,
                    name=f"Historical Scenario #{i+1}",
                    strategy_focus=strategy,
                    difficulty=difficulty,
                )
                
                scenario_dict['created_by'] = admin_user
                
                Scenario.objects.create(**scenario_dict)
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f"  Created {i+1}/{count} scenarios")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
