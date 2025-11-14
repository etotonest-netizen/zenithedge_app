#!/usr/bin/env python
"""
Quick Engine Test Script
=========================
Verifies all Phase 2 components are working.

Usage:
    python test_engine_complete.py
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all module imports."""
    print("\n🧪 Testing Module Imports...")
    
    try:
        # Phase 1 modules
        from engine import models, admin, apps
        from engine import indicators, smc, strategies
        from adapters import tv_historical
        print("  ✅ Phase 1 modules OK")
        
        # Phase 2 modules
        from engine import scoring, visuals, backtest
        from engine import views, urls
        from engine.management.commands import run_backtest, fetch_and_run
        from engine.tests import test_engine
        print("  ✅ Phase 2 modules OK")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_indicators():
    """Test indicators with sample data."""
    print("\n🧪 Testing Indicators...")
    
    try:
        import pandas as pd
        import numpy as np
        from engine.indicators import atr, sma, rsi, bollinger_bands, vwap
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        close = 1.1000 + np.cumsum(np.random.randn(100) * 0.0005)
        
        df = pd.DataFrame({
            'open': close + 0.0001,
            'high': close + 0.0003,
            'low': close - 0.0003,
            'close': close,
            'volume': np.random.randint(1000, 10000, 100),
        }, index=dates)
        
        # Test indicators
        atr_vals = atr(df, period=14)
        sma_vals = sma(df['close'], period=20)
        rsi_vals = rsi(df['close'], period=14)
        upper, middle, lower = bollinger_bands(df, period=20)
        vwap_vals = vwap(df)
        
        assert len(atr_vals) == 100
        assert len(sma_vals) == 100
        assert all(rsi_vals.dropna() >= 0) and all(rsi_vals.dropna() <= 100)
        
        print("  ✅ Indicators working")
        return True
    except Exception as e:
        print(f"  ❌ Indicators failed: {e}")
        return False


def test_smc_detection():
    """Test SMC detector."""
    print("\n🧪 Testing SMC Detection...")
    
    try:
        import pandas as pd
        import numpy as np
        from engine.smc import detect_smc
        
        # Create trending data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='1H')
        trend = np.linspace(1.1000, 1.1100, 200)
        close = trend + np.random.randn(200) * 0.0005
        
        df = pd.DataFrame({
            'open': close + 0.0001,
            'high': close + 0.0003,
            'low': close - 0.0003,
            'close': close,
            'volume': np.random.randint(1000, 10000, 200),
        }, index=dates)
        
        signals = detect_smc(df, 'EURUSD', '1H')
        
        print(f"  ✅ SMC detection working (detected {len(signals)} signals)")
        return True
    except Exception as e:
        print(f"  ❌ SMC detection failed: {e}")
        return False


def test_strategies():
    """Test all strategy detectors."""
    print("\n🧪 Testing Strategy Detectors...")
    
    try:
        import pandas as pd
        import numpy as np
        from engine.strategies import detect_all_strategies, STRATEGY_DETECTORS
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='1H')
        close = 1.1000 + np.cumsum(np.random.randn(200) * 0.0005)
        
        df = pd.DataFrame({
            'open': close + 0.0001,
            'high': close + 0.0003,
            'low': close - 0.0003,
            'close': close,
            'volume': np.random.randint(1000, 10000, 200),
        }, index=dates)
        
        # Test all strategies
        signals = detect_all_strategies(df, 'EURUSD', '1H')
        
        assert len(STRATEGY_DETECTORS) == 10
        print(f"  ✅ All 10 strategies working (detected {len(signals)} total signals)")
        return True
    except Exception as e:
        print(f"  ❌ Strategies failed: {e}")
        return False


def test_scoring():
    """Test scoring module."""
    print("\n🧪 Testing Scoring...")
    
    try:
        from engine.scoring import score_backtest_signal, fallback_engine_score
        
        # Test backtest scoring
        score, breakdown = score_backtest_signal(
            symbol='EURUSD',
            side='BUY',
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            strategy_metadata={
                'confidence': 78,
                'strategy': 'SMC',
                'regime': 'Trending',
                'entry_reason': 'BOS + OB retest',
                'structure_tags': ['BOS', 'OB_retest'],
            }
        )
        
        assert 0 <= score <= 100
        assert 'strategy' in breakdown
        
        print(f"  ✅ Scoring working (sample score: {score}/100)")
        return True
    except Exception as e:
        print(f"  ❌ Scoring failed: {e}")
        return False


def test_visuals():
    """Test visuals generation."""
    print("\n🧪 Testing Visuals...")
    
    try:
        from engine.visuals import generate_signal_visuals, export_to_json
        from decimal import Decimal
        from datetime import datetime
        
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
            'confidence': 82,
            'structure_tags': ['BOS', 'OB_retest'],
        }
        
        visuals = generate_signal_visuals(signal, metadata)
        json_output = export_to_json(visuals)
        
        assert 'boxes' in visuals
        assert 'markers' in visuals
        assert 'version' in json_output
        
        print("  ✅ Visuals working")
        return True
    except Exception as e:
        print(f"  ❌ Visuals failed: {e}")
        return False


def test_backtest():
    """Test backtesting engine."""
    print("\n🧪 Testing Backtest Engine...")
    
    try:
        import pandas as pd
        import numpy as np
        from engine.backtest import BacktestEngine
        from engine.strategies import TrendFollowingDetector
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=300, freq='1H')
        trend = np.linspace(1.1000, 1.1100, 300)
        close = trend + np.random.randn(300) * 0.0005
        
        df = pd.DataFrame({
            'open': close + 0.0001,
            'high': close + 0.0003,
            'low': close - 0.0003,
            'close': close,
            'volume': np.random.randint(1000, 10000, 300),
        }, index=dates)
        
        # Run backtest
        engine = BacktestEngine(initial_balance=10000.0, risk_per_trade_pct=1.0)
        detector = TrendFollowingDetector()
        
        results = engine.run_backtest(df, 'EURUSD', '1H', detector, 'Trend')
        
        assert 'metrics' in results
        assert 'trades' in results
        
        print(f"  ✅ Backtest working (processed {results['bars_processed']} bars)")
        return True
    except Exception as e:
        print(f"  ❌ Backtest failed: {e}")
        return False


def test_sample_data():
    """Test sample data loading."""
    print("\n🧪 Testing Sample Data...")
    
    try:
        import pandas as pd
        
        df = pd.read_csv('adapters/sample_data/eurusd_1h.csv', 
                         parse_dates=['timestamp'],
                         index_col='timestamp')
        
        assert len(df) > 0
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        
        print(f"  ✅ Sample data OK ({len(df)} bars)")
        return True
    except Exception as e:
        print(f"  ❌ Sample data failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("ZenithEdge Engine - Complete Test Suite")
    print("Testing Phase 1 + Phase 2 Components")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Indicators", test_indicators),
        ("SMC Detection", test_smc_detection),
        ("Strategies", test_strategies),
        ("Scoring", test_scoring),
        ("Visuals", test_visuals),
        ("Backtest", test_backtest),
        ("Sample Data", test_sample_data),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Engine is ready for deployment!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
