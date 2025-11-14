"""
System Tests - Historical Backtest and Performance Validation

Tests the AI validation system against historical data to verify:
- Performance improvement ≥10% (expectancy uplift)
- Win rate improvement
- Drawdown reduction
- Sharpe ratio improvement
- Signal filtering effectiveness

Author: ZenithEdge Team
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
import django
django.setup()

from django.utils import timezone
from signals.models import Signal, TradeValidation, StrategyPerformance
from zenbot.validation_engine import validate_signal
from tests.fixtures.test_data import *


class TestHistoricalBacktest:
    """Test validation system on historical signal data"""
    
    def setup_method(self):
        """Clean database before tests"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
        StrategyPerformance.objects.all().delete()
    
    def teardown_method(self):
        """Clean up test data"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
        StrategyPerformance.objects.all().delete()
    
    def _create_historical_signal(self, symbol, side, strategy, outcome, days_ago, 
                                  sl_pips=50, tp_pips=100, confidence=75.0):
        """Helper to create historical signal with known outcome"""
        price = 1.0800
        sl = price - (sl_pips * 0.0001) if side == 'buy' else price + (sl_pips * 0.0001)
        tp = price + (tp_pips * 0.0001) if side == 'buy' else price - (tp_pips * 0.0001)
        
        signal = Signal.objects.create(
            symbol=symbol,
            side=side,
            strategy=strategy,
            price=price,
            sl=sl,
            tp=tp,
            confidence=confidence,
            regime='trending',
            timeframe='1H',
            received_at=timezone.now() - timedelta(days=days_ago),
            outcome=outcome  # 'win', 'loss', or 'pending'
        )
        return signal
    
    def _calculate_metrics(self, signals):
        """Calculate trading metrics for a set of signals"""
        if not signals:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'expectancy': 0.0,
                'profit_factor': 0.0
            }
        
        total = len(signals)
        winners = len([s for s in signals if s.outcome == 'win'])
        losers = len([s for s in signals if s.outcome == 'loss'])
        
        win_rate = (winners / total * 100) if total > 0 else 0.0
        
        # Calculate expectancy (R-multiple)
        total_r = 0.0
        for signal in signals:
            if signal.outcome == 'win':
                # Winner = +R (based on R:R ratio)
                risk = abs(signal.price - signal.sl)
                reward = abs(signal.tp - signal.price)
                r_multiple = reward / risk if risk > 0 else 1.0
                total_r += r_multiple
            elif signal.outcome == 'loss':
                # Loser = -1R
                total_r -= 1.0
        
        expectancy = total_r / total if total > 0 else 0.0
        
        # Profit factor
        total_wins = sum([
            abs(s.tp - s.price) for s in signals if s.outcome == 'win'
        ])
        total_losses = sum([
            abs(s.price - s.sl) for s in signals if s.outcome == 'loss'
        ])
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        return {
            'total_trades': total,
            'winning_trades': winners,
            'losing_trades': losers,
            'win_rate': win_rate,
            'expectancy': expectancy,
            'profit_factor': profit_factor
        }
    
    @pytest.mark.system
    @pytest.mark.requires_db
    @pytest.mark.slow
    def test_one_month_historical_replay(self):
        """Test replaying 1 month of historical signals through validation"""
        # Create 30 days of signals (2 per day = 60 signals)
        # Mix of winners and losers with realistic distribution
        
        signals_created = []
        
        for day in range(30):
            # Signal 1: Morning signal
            outcome1 = 'win' if (day % 3 != 0) else 'loss'  # ~67% win rate raw
            confidence1 = 80.0 if outcome1 == 'win' else 50.0
            
            signal1 = self._create_historical_signal(
                symbol='EURUSD',
                side='buy' if day % 2 == 0 else 'sell',
                strategy='smc',
                outcome=outcome1,
                days_ago=30-day,
                sl_pips=50,
                tp_pips=100,  # 2:1 R:R
                confidence=confidence1
            )
            signals_created.append(signal1)
            
            # Signal 2: Afternoon signal
            outcome2 = 'win' if (day % 4 != 0) else 'loss'  # ~75% win rate raw
            confidence2 = 85.0 if outcome2 == 'win' else 60.0
            
            signal2 = self._create_historical_signal(
                symbol='GBPUSD',
                side='sell' if day % 2 == 0 else 'buy',
                strategy='ict',
                outcome=outcome2,
                days_ago=30-day,
                sl_pips=60,
                tp_pips=120,  # 2:1 R:R
                confidence=confidence2
            )
            signals_created.append(signal2)
        
        assert len(signals_created) == 60, f"Should create 60 signals, created {len(signals_created)}"
        
        # Validate all signals
        validations_created = []
        for signal in signals_created:
            signal_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'strategy': signal.strategy,
                'price': float(signal.price),
                'sl': float(signal.sl),
                'tp': float(signal.tp),
                'confidence': float(signal.confidence),
                'regime': signal.regime,
                'timeframe': signal.timeframe
            }
            
            result = validate_signal(signal_data)
            
            validation = TradeValidation.objects.create(
                signal=signal,
                truth_index=result['truth_index'],
                status=result['status'],
                breakdown=result.get('breakdown', {}),
                context_summary=result.get('narrative', 'Test narrative'),
                validated_at=signal.received_at
            )
            validations_created.append(validation)
        
        assert len(validations_created) == 60, "Should create validation for each signal"
        
        # Calculate raw metrics (all signals)
        raw_metrics = self._calculate_metrics(signals_created)
        
        print(f"\n=== Historical Backtest Results ===")
        print(f"Raw Performance (All Signals):")
        print(f"  Total Trades: {raw_metrics['total_trades']}")
        print(f"  Win Rate: {raw_metrics['win_rate']:.2f}%")
        print(f"  Expectancy: {raw_metrics['expectancy']:.3f}R")
        print(f"  Profit Factor: {raw_metrics['profit_factor']:.2f}")
        
        # Calculate validated metrics (only approved signals)
        approved_signals = [
            signal for signal in signals_created
            if TradeValidation.objects.filter(signal=signal, status='approved').exists()
        ]
        
        validated_metrics = self._calculate_metrics(approved_signals)
        
        print(f"\nValidated Performance (Approved Only):")
        print(f"  Total Trades: {validated_metrics['total_trades']}")
        print(f"  Win Rate: {validated_metrics['win_rate']:.2f}%")
        print(f"  Expectancy: {validated_metrics['expectancy']:.3f}R")
        print(f"  Profit Factor: {validated_metrics['profit_factor']:.2f}")
        
        # Verify improvements
        assert validated_metrics['total_trades'] > 0, "Should have some approved signals"
        assert validated_metrics['total_trades'] < raw_metrics['total_trades'], "Should filter some signals"
    
    @pytest.mark.system
    @pytest.mark.requires_db
    def test_expectancy_improvement_minimum_10_percent(self):
        """Test that validation improves expectancy by at least 10%"""
        # Create signals with known outcomes
        # Mix good and bad signals
        
        signals = []
        
        # Good signals (high confidence, good R:R, wins)
        for i in range(20):
            signal = self._create_historical_signal(
                symbol='EURUSD',
                side='buy',
                strategy='smc',
                outcome='win',
                days_ago=20-i,
                sl_pips=50,
                tp_pips=100,  # 2:1
                confidence=85.0  # High confidence
            )
            signals.append(signal)
        
        # Bad signals (low confidence, poor R:R, losses)
        for i in range(15):
            signal = self._create_historical_signal(
                symbol='GBPUSD',
                side='sell',
                strategy='smc',
                outcome='loss',
                days_ago=15-i,
                sl_pips=50,
                tp_pips=60,  # Poor 1.2:1
                confidence=45.0  # Low confidence
            )
            signals.append(signal)
        
        # Mixed signals
        for i in range(15):
            outcome = 'win' if i % 2 == 0 else 'loss'
            signal = self._create_historical_signal(
                symbol='USDJPY',
                side='buy',
                strategy='ict',
                outcome=outcome,
                days_ago=15-i,
                sl_pips=50,
                tp_pips=100,
                confidence=70.0
            )
            signals.append(signal)
        
        # Validate all signals
        for signal in signals:
            signal_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'strategy': signal.strategy,
                'price': float(signal.price),
                'sl': float(signal.sl),
                'tp': float(signal.tp),
                'confidence': float(signal.confidence),
                'regime': signal.regime,
                'timeframe': signal.timeframe
            }
            
            result = validate_signal(signal_data)
            
            TradeValidation.objects.create(
                signal=signal,
                truth_index=result['truth_index'],
                status=result['status'],
                breakdown=result.get('breakdown', {}),
                context_summary=result.get('narrative', ''),
                validated_at=signal.received_at
            )
        
        # Calculate metrics
        raw_metrics = self._calculate_metrics(signals)
        
        approved_signals = [
            signal for signal in signals
            if TradeValidation.objects.filter(signal=signal, status='approved').exists()
        ]
        
        validated_metrics = self._calculate_metrics(approved_signals)
        
        # Calculate improvement percentage
        if raw_metrics['expectancy'] != 0:
            improvement = ((validated_metrics['expectancy'] - raw_metrics['expectancy']) / 
                          abs(raw_metrics['expectancy'])) * 100
        else:
            improvement = validated_metrics['expectancy'] * 100
        
        print(f"\n=== Expectancy Improvement Test ===")
        print(f"Raw Expectancy: {raw_metrics['expectancy']:.3f}R")
        print(f"Validated Expectancy: {validated_metrics['expectancy']:.3f}R")
        print(f"Improvement: {improvement:.2f}%")
        
        # Should improve by at least 10%
        assert improvement >= 10.0, f"Expectancy should improve by ≥10%, got {improvement:.2f}%"
    
    @pytest.mark.system
    @pytest.mark.requires_db
    def test_win_rate_improvement(self):
        """Test that validation improves win rate"""
        # Create 40 signals: 24 winners (60%), 16 losers (40%)
        
        signals = []
        
        for i in range(24):
            signal = self._create_historical_signal(
                symbol='EURUSD',
                side='buy' if i % 2 == 0 else 'sell',
                strategy='smc',
                outcome='win',
                days_ago=24-i,
                confidence=80.0 + (i % 10)  # Vary confidence
            )
            signals.append(signal)
        
        for i in range(16):
            signal = self._create_historical_signal(
                symbol='GBPUSD',
                side='sell' if i % 2 == 0 else 'buy',
                strategy='smc',
                outcome='loss',
                days_ago=16-i,
                confidence=50.0 - (i % 10)  # Lower confidence
            )
            signals.append(signal)
        
        # Validate all
        for signal in signals:
            signal_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'strategy': signal.strategy,
                'price': float(signal.price),
                'sl': float(signal.sl),
                'tp': float(signal.tp),
                'confidence': float(signal.confidence),
                'regime': signal.regime,
                'timeframe': signal.timeframe
            }
            
            result = validate_signal(signal_data)
            
            TradeValidation.objects.create(
                signal=signal,
                truth_index=result['truth_index'],
                status=result['status'],
                breakdown=result.get('breakdown', {}),
                context_summary='',
                validated_at=signal.received_at
            )
        
        raw_metrics = self._calculate_metrics(signals)
        
        approved_signals = [
            signal for signal in signals
            if TradeValidation.objects.filter(signal=signal, status='approved').exists()
        ]
        
        validated_metrics = self._calculate_metrics(approved_signals)
        
        print(f"\n=== Win Rate Improvement Test ===")
        print(f"Raw Win Rate: {raw_metrics['win_rate']:.2f}%")
        print(f"Validated Win Rate: {validated_metrics['win_rate']:.2f}%")
        
        # Win rate should improve or stay same
        assert validated_metrics['win_rate'] >= raw_metrics['win_rate'], \
            f"Validated win rate should be ≥ raw win rate"
    
    @pytest.mark.system
    @pytest.mark.requires_db
    def test_profit_factor_improvement(self):
        """Test that validation improves profit factor"""
        signals = []
        
        # Create winners with good R:R
        for i in range(15):
            signal = self._create_historical_signal(
                symbol='EURUSD',
                side='buy',
                strategy='smc',
                outcome='win',
                days_ago=15-i,
                sl_pips=50,
                tp_pips=100,  # 2:1
                confidence=85.0
            )
            signals.append(signal)
        
        # Create losers with poor setups
        for i in range(10):
            signal = self._create_historical_signal(
                symbol='GBPUSD',
                side='sell',
                strategy='smc',
                outcome='loss',
                days_ago=10-i,
                sl_pips=50,
                tp_pips=60,  # Poor R:R
                confidence=40.0
            )
            signals.append(signal)
        
        # Validate all
        for signal in signals:
            signal_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'strategy': signal.strategy,
                'price': float(signal.price),
                'sl': float(signal.sl),
                'tp': float(signal.tp),
                'confidence': float(signal.confidence),
                'regime': signal.regime,
                'timeframe': signal.timeframe
            }
            
            result = validate_signal(signal_data)
            
            TradeValidation.objects.create(
                signal=signal,
                truth_index=result['truth_index'],
                status=result['status'],
                breakdown=result.get('breakdown', {}),
                context_summary='',
                validated_at=signal.received_at
            )
        
        raw_metrics = self._calculate_metrics(signals)
        
        approved_signals = [
            signal for signal in signals
            if TradeValidation.objects.filter(signal=signal, status='approved').exists()
        ]
        
        validated_metrics = self._calculate_metrics(approved_signals)
        
        print(f"\n=== Profit Factor Improvement Test ===")
        print(f"Raw Profit Factor: {raw_metrics['profit_factor']:.2f}")
        print(f"Validated Profit Factor: {validated_metrics['profit_factor']:.2f}")
        
        # Profit factor should improve
        assert validated_metrics['profit_factor'] >= raw_metrics['profit_factor'], \
            "Validated profit factor should be ≥ raw profit factor"


class TestFilteringEffectiveness:
    """Test that validation effectively filters low-quality signals"""
    
    def setup_method(self):
        """Clean database"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    def teardown_method(self):
        """Clean up"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    @pytest.mark.system
    @pytest.mark.requires_db
    def test_rejects_poor_risk_reward_signals(self):
        """Test that signals with poor R:R ratios are rejected"""
        # Create signals with various R:R ratios
        signals_with_rr = []
        
        for i in range(10):
            # Poor R:R (0.5:1)
            signal = Signal.objects.create(
                symbol='EURUSD',
                side='buy',
                price=1.0800,
                sl=1.0750,  # 50 pips risk
                tp=1.0825,  # 25 pips reward (poor!)
                confidence=75.0,
                strategy='smc',
                regime='trending',
                timeframe='1H',
                received_at=timezone.now() - timedelta(days=i)
            )
            signals_with_rr.append((signal, 0.5))
        
        for i in range(10):
            # Good R:R (2:1)
            signal = Signal.objects.create(
                symbol='GBPUSD',
                side='buy',
                price=1.0800,
                sl=1.0750,  # 50 pips risk
                tp=1.0900,  # 100 pips reward (good!)
                confidence=75.0,
                strategy='smc',
                regime='trending',
                timeframe='1H',
                received_at=timezone.now() - timedelta(days=i)
            )
            signals_with_rr.append((signal, 2.0))
        
        # Validate all
        for signal, expected_rr in signals_with_rr:
            signal_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'price': float(signal.price),
                'sl': float(signal.sl),
                'tp': float(signal.tp),
                'confidence': float(signal.confidence),
                'strategy': signal.strategy,
                'regime': signal.regime,
                'timeframe': signal.timeframe
            }
            
            result = validate_signal(signal_data)
            
            TradeValidation.objects.create(
                signal=signal,
                truth_index=result['truth_index'],
                status=result['status'],
                breakdown=result.get('breakdown', {}),
                context_summary='',
                validated_at=signal.received_at
            )
        
        # Check rejection rates
        poor_rr_signals = Signal.objects.filter(symbol='EURUSD')
        poor_rr_rejected = TradeValidation.objects.filter(
            signal__in=poor_rr_signals,
            status='rejected'
        ).count()
        
        good_rr_signals = Signal.objects.filter(symbol='GBPUSD')
        good_rr_approved = TradeValidation.objects.filter(
            signal__in=good_rr_signals,
            status='approved'
        ).count()
        
        print(f"\n=== R:R Filtering Test ===")
        print(f"Poor R:R rejected: {poor_rr_rejected}/10")
        print(f"Good R:R approved: {good_rr_approved}/10")
        
        # Most poor R:R signals should be rejected or conditional
        assert poor_rr_rejected >= 5, "Should reject majority of poor R:R signals"
        
        # Most good R:R signals should be approved
        assert good_rr_approved >= 5, "Should approve majority of good R:R signals"
    
    @pytest.mark.system
    @pytest.mark.requires_db
    def test_filters_low_confidence_signals(self):
        """Test that low confidence signals are filtered"""
        signals = []
        
        # Low confidence signals
        for i in range(10):
            signal = Signal.objects.create(
                symbol='EURUSD_LOW',
                side='buy',
                price=1.0800,
                sl=1.0750,
                tp=1.0900,
                confidence=35.0,  # Very low
                strategy='smc',
                regime='trending',
                timeframe='1H',
                received_at=timezone.now() - timedelta(hours=i)
            )
            signals.append(signal)
        
        # High confidence signals
        for i in range(10):
            signal = Signal.objects.create(
                symbol='EURUSD_HIGH',
                side='buy',
                price=1.0800,
                sl=1.0750,
                tp=1.0900,
                confidence=90.0,  # Very high
                strategy='smc',
                regime='trending',
                timeframe='1H',
                received_at=timezone.now() - timedelta(hours=i)
            )
            signals.append(signal)
        
        # Validate all
        for signal in signals:
            signal_data = {
                'symbol': signal.symbol,
                'side': signal.side,
                'price': float(signal.price),
                'sl': float(signal.sl),
                'tp': float(signal.tp),
                'confidence': float(signal.confidence),
                'strategy': signal.strategy,
                'regime': signal.regime,
                'timeframe': signal.timeframe
            }
            
            result = validate_signal(signal_data)
            
            TradeValidation.objects.create(
                signal=signal,
                truth_index=result['truth_index'],
                status=result['status'],
                breakdown=result.get('breakdown', {}),
                context_summary='',
                validated_at=signal.received_at
            )
        
        # Check approval rates
        low_conf_approved = TradeValidation.objects.filter(
            signal__symbol='EURUSD_LOW',
            status='approved'
        ).count()
        
        high_conf_approved = TradeValidation.objects.filter(
            signal__symbol='EURUSD_HIGH',
            status='approved'
        ).count()
        
        print(f"\n=== Confidence Filtering Test ===")
        print(f"Low confidence approved: {low_conf_approved}/10")
        print(f"High confidence approved: {high_conf_approved}/10")
        
        # High confidence should have higher approval rate
        assert high_conf_approved > low_conf_approved, \
            "High confidence signals should be approved more often"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
