"""
Engine Test Suite
==================
Comprehensive tests for all engine modules.

Run tests:
    python manage.py test engine.tests
    
Run specific test:
    python manage.py test engine.tests.test_indicators
"""

from django.test import TestCase
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal


class IndicatorsTestCase(TestCase):
    """Test technical indicators module."""
    
    def setUp(self):
        """Create sample data."""
        # Generate 100 bars of sample OHLCV data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        
        close_prices = 1.1000 + np.cumsum(np.random.randn(100) * 0.0005)
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices + np.random.randn(100) * 0.0002,
            'high': close_prices + np.abs(np.random.randn(100)) * 0.0003,
            'low': close_prices - np.abs(np.random.randn(100)) * 0.0003,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 100),
        })
        self.df.set_index('timestamp', inplace=True)
    
    def test_atr_calculation(self):
        """Test ATR indicator."""
        from engine.indicators import atr
        
        atr_values = atr(self.df, period=14)
        
        # ATR should be positive and reasonable
        self.assertTrue(all(atr_values[14:] > 0))
        self.assertTrue(all(atr_values[14:] < 0.01))  # Should be small for forex
    
    def test_sma_calculation(self):
        """Test Simple Moving Average."""
        from engine.indicators import sma
        
        sma_values = sma(self.df['close'], period=20)
        
        # SMA should smooth the data
        self.assertEqual(len(sma_values), len(self.df))
        self.assertTrue(np.isnan(sma_values.iloc[0]))  # First values are NaN
        self.assertFalse(np.isnan(sma_values.iloc[-1]))  # Last value should exist
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average."""
        from engine.indicators import ema
        
        ema_values = ema(self.df['close'], period=20)
        
        # EMA should be similar to but more responsive than SMA
        self.assertEqual(len(ema_values), len(self.df))
        self.assertFalse(np.isnan(ema_values.iloc[-1]))
    
    def test_rsi_calculation(self):
        """Test RSI indicator."""
        from engine.indicators import rsi
        
        rsi_values = rsi(self.df['close'], period=14)
        
        # RSI should be between 0 and 100
        valid_rsi = rsi_values.dropna()
        self.assertTrue(all(valid_rsi >= 0))
        self.assertTrue(all(valid_rsi <= 100))
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands."""
        from engine.indicators import bollinger_bands
        
        upper, middle, lower = bollinger_bands(self.df, period=20, std_dev=2.0)
        
        # Upper should be above middle, middle above lower
        valid_idx = ~upper.isna()
        self.assertTrue(all(upper[valid_idx] > middle[valid_idx]))
        self.assertTrue(all(middle[valid_idx] > lower[valid_idx]))
    
    def test_vwap_calculation(self):
        """Test VWAP indicator."""
        from engine.indicators import vwap
        
        vwap_values = vwap(self.df)
        
        # VWAP should exist and be reasonable
        self.assertEqual(len(vwap_values), len(self.df))
        self.assertFalse(np.isnan(vwap_values.iloc[-1]))
    
    def test_swing_detection(self):
        """Test swing high/low detection."""
        from engine.indicators import swing_highs_lows
        
        swing_highs, swing_lows = swing_highs_lows(self.df, left_bars=5, right_bars=5)
        
        # Should detect some swings
        num_swing_highs = swing_highs.sum()
        num_swing_lows = swing_lows.sum()
        
        self.assertGreater(num_swing_highs, 0)
        self.assertGreater(num_swing_lows, 0)


class SMCTestCase(TestCase):
    """Test SMC detection module."""
    
    def setUp(self):
        """Create sample trending data."""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')
        
        # Create uptrend
        trend = np.linspace(1.1000, 1.1100, 200)
        noise = np.random.randn(200) * 0.0005
        close_prices = trend + noise
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices + np.random.randn(200) * 0.0002,
            'high': close_prices + np.abs(np.random.randn(200)) * 0.0003,
            'low': close_prices - np.abs(np.random.randn(200)) * 0.0003,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 200),
        })
        self.df.set_index('timestamp', inplace=True)
    
    def test_smc_detector_initialization(self):
        """Test SMC detector can be initialized."""
        from engine.smc import SMCDetector
        
        detector = SMCDetector(swing_length=5, ob_lookback=20)
        
        self.assertEqual(detector.swing_length, 5)
        self.assertEqual(detector.ob_lookback, 20)
    
    def test_smc_signal_detection(self):
        """Test SMC signal detection."""
        from engine.smc import detect_smc
        
        signals = detect_smc(self.df, 'EURUSD', '1H')
        
        # Should return a list
        self.assertIsInstance(signals, list)
        
        # If signals detected, check structure
        if signals:
            signal = signals[0]
            self.assertIn('side', signal)
            self.assertIn('price', signal)
            self.assertIn('sl', signal)
            self.assertIn('tp', signal)
            self.assertIn('confidence', signal)


class StrategiesTestCase(TestCase):
    """Test strategy detectors."""
    
    def setUp(self):
        """Create sample data."""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')
        
        close_prices = 1.1000 + np.cumsum(np.random.randn(200) * 0.0005)
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices + np.random.randn(200) * 0.0002,
            'high': close_prices + np.abs(np.random.randn(200)) * 0.0003,
            'low': close_prices - np.abs(np.random.randn(200)) * 0.0003,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 200),
        })
        self.df.set_index('timestamp', inplace=True)
    
    def test_strategy_registry(self):
        """Test that all 10 strategies are registered."""
        from engine.strategies import STRATEGY_DETECTORS
        
        expected_strategies = [
            'SMC', 'ICT', 'Trend', 'Breakout', 'MeanReversion',
            'Squeeze', 'Scalping', 'VWAP', 'SupplyDemand', 'MultiTimeframe'
        ]
        
        for strategy in expected_strategies:
            self.assertIn(strategy, STRATEGY_DETECTORS)
    
    def test_detect_all_strategies(self):
        """Test running all strategies at once."""
        from engine.strategies import detect_all_strategies
        
        signals = detect_all_strategies(self.df, 'EURUSD', '1H')
        
        # Should return a list
        self.assertIsInstance(signals, list)
        
        # Each signal should have required fields
        for signal in signals:
            self.assertIn('strategy', signal)
            self.assertIn('side', signal)
            self.assertIn('confidence', signal)
    
    def test_trend_detector(self):
        """Test Trend Following detector."""
        from engine.strategies import TrendFollowingDetector
        
        detector = TrendFollowingDetector()
        signals = detector.detect(self.df, 'EURUSD', '1H')
        
        self.assertIsInstance(signals, list)
    
    def test_breakout_detector(self):
        """Test Breakout detector."""
        from engine.strategies import BreakoutDetector
        
        detector = BreakoutDetector()
        signals = detector.detect(self.df, 'EURUSD', '1H')
        
        self.assertIsInstance(signals, list)


class ScoringTestCase(TestCase):
    """Test scoring module."""
    
    def test_backtest_scoring(self):
        """Test stateless backtest scoring."""
        from engine.scoring import score_backtest_signal
        
        score, breakdown = score_backtest_signal(
            symbol='EURUSD',
            side='BUY',
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            strategy_metadata={
                'confidence': 75,
                'strategy': 'SMC',
                'regime': 'Trending',
                'entry_reason': 'OB retest',
                'structure_tags': ['BOS', 'OB_retest'],
            }
        )
        
        # Score should be 0-100
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # Breakdown should have key fields
        self.assertIn('strategy', breakdown)
        self.assertIn('confidence', breakdown)
    
    def test_fallback_scoring(self):
        """Test fallback scoring when ZenBot unavailable."""
        from engine.scoring import fallback_engine_score
        
        score, breakdown = fallback_engine_score({
            'confidence': 80,
            'strategy': 'SMC',
            'regime': 'Trending',
            'structure_tags': ['BOS', 'OB_retest'],
            'extra': {'risk_reward_ratio': 2.0}
        })
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class VisualsTestCase(TestCase):
    """Test visuals generation."""
    
    def test_visual_generation(self):
        """Test generating visuals for a signal."""
        from engine.visuals import generate_signal_visuals
        from decimal import Decimal
        
        # Mock signal
        class MockSignal:
            id = 1
            symbol = 'EURUSD'
            side = 'BUY'
            price = Decimal('1.1000')
            sl = Decimal('1.0950')
            tp = Decimal('1.1100')
            timestamp = datetime.now()
        
        signal = MockSignal()
        metadata = {
            'strategy': 'SMC',
            'confidence': 80,
            'structure_tags': ['BOS', 'OB_retest'],
        }
        
        visuals = generate_signal_visuals(signal, metadata)
        
        # Should have all visual types
        self.assertIn('boxes', visuals)
        self.assertIn('lines', visuals)
        self.assertIn('markers', visuals)
        self.assertIn('labels', visuals)
        self.assertIn('arrows', visuals)
        
        # Should have entry marker
        self.assertGreater(len(visuals['markers']), 0)
    
    def test_export_to_json(self):
        """Test JSON export."""
        from engine.visuals import export_to_json
        
        visuals = {
            'boxes': [],
            'lines': [],
            'markers': [],
            'labels': [],
            'arrows': [],
        }
        
        json_output = export_to_json(visuals)
        
        self.assertIn('version', json_output)
        self.assertIn('generator', json_output)


class BacktestTestCase(TestCase):
    """Test backtesting engine."""
    
    def setUp(self):
        """Create sample data."""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=300, freq='1H')
        
        # Create trending market
        trend = np.linspace(1.1000, 1.1100, 300)
        noise = np.random.randn(300) * 0.0005
        close_prices = trend + noise
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices + np.random.randn(300) * 0.0002,
            'high': close_prices + np.abs(np.random.randn(300)) * 0.0003,
            'low': close_prices - np.abs(np.random.randn(300)) * 0.0003,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 300),
        })
        self.df.set_index('timestamp', inplace=True)
    
    def test_backtest_engine_initialization(self):
        """Test backtester can be initialized."""
        from engine.backtest import BacktestEngine
        
        engine = BacktestEngine(
            initial_balance=10000.0,
            risk_per_trade_pct=1.0,
        )
        
        self.assertEqual(engine.initial_balance, 10000.0)
        self.assertEqual(engine.balance, 10000.0)
    
    def test_quick_backtest(self):
        """Test quick backtest function."""
        from engine.backtest import quick_backtest
        
        # Test with Trend strategy
        results = quick_backtest(
            df=self.df,
            symbol='EURUSD',
            timeframe='1H',
            strategy_name='Trend',
            initial_balance=10000.0,
            risk_per_trade_pct=1.0,
        )
        
        # Check results structure
        self.assertIn('symbol', results)
        self.assertIn('strategy', results)
        self.assertIn('metrics', results)
        self.assertIn('trades', results)
        
        # Metrics should have required fields
        metrics = results['metrics']
        self.assertIn('total_trades', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('net_profit', metrics)


class ModelTestCase(TestCase):
    """Test database models."""
    
    def test_market_bar_creation(self):
        """Test creating MarketBar entry."""
        from engine.models import MarketBar
        from django.utils import timezone
        
        bar = MarketBar.objects.create(
            symbol='EURUSD',
            timeframe='1H',
            timestamp=timezone.now(),
            open=Decimal('1.1000'),
            high=Decimal('1.1010'),
            low=Decimal('1.0990'),
            close=Decimal('1.1005'),
            volume=Decimal('50000'),
        )
        
        self.assertEqual(bar.symbol, 'EURUSD')
        self.assertEqual(bar.timeframe, '1H')
        
        # Test ohlc_dict method
        ohlc = bar.ohlc_dict
        self.assertEqual(ohlc['open'], 1.1000)
    
    def test_backtest_run_creation(self):
        """Test creating BacktestRun entry."""
        from engine.models import BacktestRun
        from datetime import date
        
        backtest = BacktestRun.objects.create(
            symbol='EURUSD',
            timeframe='1H',
            strategy='SMC',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 11, 1),
            initial_balance=Decimal('10000.00'),
            final_balance=Decimal('11500.00'),
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=Decimal('60.00'),
        )
        
        self.assertEqual(backtest.total_trades, 50)
        self.assertEqual(backtest.win_rate, Decimal('60.00'))
        
        # Test metrics_dict method
        metrics = backtest.metrics_dict
        self.assertEqual(metrics['win_rate'], 60.00)


class IntegrationTestCase(TestCase):
    """End-to-end integration tests."""
    
    def test_full_pipeline(self):
        """Test complete pipeline: data -> detection -> scoring -> storage."""
        from engine.models import MarketBar
        from engine.strategies import detect_all_strategies
        from engine.scoring import score_backtest_signal
        from django.utils import timezone
        import pandas as pd
        
        # 1. Create sample market data
        symbol = 'EURUSD'
        timeframe = '1H'
        
        timestamps = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        np.random.seed(42)
        close_prices = 1.1000 + np.cumsum(np.random.randn(100) * 0.0005)
        
        for i, ts in enumerate(timestamps):
            MarketBar.objects.create(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts,
                open=Decimal(str(close_prices[i] + 0.0001)),
                high=Decimal(str(close_prices[i] + 0.0003)),
                low=Decimal(str(close_prices[i] - 0.0003)),
                close=Decimal(str(close_prices[i])),
                volume=Decimal('5000'),
            )
        
        # 2. Load data from database
        bars = MarketBar.objects.filter(symbol=symbol, timeframe=timeframe).order_by('timestamp')
        
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
        
        # 3. Run detection
        signals = detect_all_strategies(df, symbol, timeframe)
        
        self.assertIsInstance(signals, list)
        
        # 4. Score signals (if any detected)
        if signals:
            signal_data = signals[0]
            score, breakdown = score_backtest_signal(
                symbol=symbol,
                side=signal_data['side'],
                price=signal_data['price'],
                sl=signal_data['sl'],
                tp=signal_data['tp'],
                strategy_metadata=signal_data,
            )
            
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)


# Test runner
def run_tests():
    """Run all tests and print summary."""
    import sys
    from django.test.runner import DiscoverRunner
    
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(['engine.tests'])
    
    if failures:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")


if __name__ == '__main__':
    run_tests()
