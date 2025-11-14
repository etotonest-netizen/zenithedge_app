"""
Unit Tests for AI Validation Engine

Tests all 6 validation criteria independently:
1. Technical Integrity
2. Volatility Filter
3. Regime Alignment
4. Sentiment Coherence
5. Historical Reliability
6. Psychological Safety

Author: ZenithEdge Team
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
import django
django.setup()

from zenbot.validation_engine import SignalValidator, validate_signal
from tests.fixtures.test_data import *


class TestTechnicalIntegrity:
    """Test technical_integrity validation criterion"""
    
    def setup_method(self):
        """Initialize validator before each test"""
        self.validator = SignalValidator()
    
    @pytest.mark.unit
    def test_excellent_rr_ratio(self):
        """Test signal with excellent R:R ratio (2:1 or better)"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 85.0,
            'price': 1.0800,
            'sl': 1.0750,  # 50 pips risk
            'tp': 1.0900,  # 100 pips reward = 2:1 R:R
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_technical_integrity(signal_data)
        assert score >= 0.85, f"Expected score ≥0.85 for excellent R:R, got {score}"
    
    @pytest.mark.unit
    def test_poor_rr_ratio(self):
        """Test 0.4:1 R:R ratio is penalized"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'price': 1.0800,
            'sl': 1.0750,  # 50 pips risk
            'tp': 1.0820,  # 20 pips reward (0.4:1 R:R - poor)
            'confidence': 75.0,
            'strategy': 'smc',
            'regime': 'trending'
        }
        score = self.validator._check_technical_integrity(signal_data)
        # Poor R:R (<1.0) should be penalized (score reduced by 0.2)
        assert score <= 0.85, f"Expected score ≤0.85 for poor R:R, got {score}"
    
    @pytest.mark.unit
    def test_high_confidence_bonus(self):
        """Test that high confidence (≥75) improves score"""
        signal_high_conf = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 85.0,  # High confidence
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        signal_low_conf = signal_high_conf.copy()
        signal_low_conf['confidence'] = 45.0  # Low confidence
        
        score_high = self.validator._check_technical_integrity(signal_high_conf)
        score_low = self.validator._check_technical_integrity(signal_low_conf)
        
        assert score_high > score_low, "High confidence should yield better score"
    
    @pytest.mark.unit
    def test_missing_price_defaults_to_zero(self):
        """Test that missing price field doesn't crash"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 75.0,
            # price is missing
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_technical_integrity(signal_data)
        assert 0.0 <= score <= 1.0, f"Score should be in valid range, got {score}"


class TestVolatilityFilter:
    """Test volatility_filter validation criterion"""
    
    def setup_method(self):
        """Initialize validator and create test signals"""
        self.validator = SignalValidator()
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_stable_market_high_score(self):
        """Test that stable markets get high volatility scores"""
        from signals.models import Signal
        
        # Create 20 recent signals with stable prices
        symbol = "EURUSD_STABLE_TEST"
        base_price = 1.0800
        
        for i in range(20):
            Signal.objects.create(
                symbol=symbol,
                timeframe="1H",
                side="buy",
                sl=base_price - 0.0010,
                tp=base_price + 0.0020,
                confidence=75.0,
                strategy="smc",
                regime="Trend",
                price=base_price + (i * 0.0002),  # Small incremental changes
                received_at=timezone.now() - timedelta(hours=20-i)
            )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 75.0,
            'price': base_price,
            'sl': base_price - 0.0050,
            'tp': base_price + 0.0100,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_volatility(signal_data)
        
        # Clean up
        Signal.objects.filter(symbol=symbol).delete()
        
        assert score >= 0.80, f"Expected high score for stable market, got {score}"
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_volatile_market_low_score(self):
        """Test that volatile markets get low volatility scores"""
        from signals.models import Signal
        import random
        
        symbol = "BTCUSDT_VOLATILE_TEST"
        base_price = 43000.0
        
        for i in range(20):
            # High volatility - price swings wildly
            price_change = random.uniform(-2000, 2000)
            Signal.objects.create(
                symbol=symbol,
                timeframe="5M",
                side="buy" if i % 2 == 0 else "sell",
                sl=base_price - 1000,
                tp=base_price + 2000,
                confidence=70.0,
                strategy="breakout",
                regime="Breakout",
                price=base_price + price_change,
                received_at=timezone.now() - timedelta(hours=20-i)
            )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',
            'strategy': 'breakout',
            'confidence': 70.0,
            'price': base_price,
            'sl': base_price - 1000,
            'tp': base_price + 2000,
            'regime': 'volatile',
            'timeframe': '5M'
        }
        
        score = self.validator._check_volatility(signal_data)
        
        # Clean up
        Signal.objects.filter(symbol=symbol).delete()
        
        assert score <= 0.85, f"Expected lower score for volatile market, got {score}"
    
    @pytest.mark.unit
    def test_insufficient_data_returns_neutral(self):
        """Test that insufficient signal history returns neutral score"""
        signal_data = {
            'symbol': 'NEWPAIR_NO_HISTORY',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_volatility(signal_data)
        
        # Should return neutral score (0.7) when no historical data
        assert 0.65 <= score <= 0.75, f"Expected neutral score for no data, got {score}"


class TestRegimeAlignment:
    """Test regime_alignment validation criterion"""
    
    def setup_method(self):
        """Initialize validator"""
        self.validator = SignalValidator()
    
    @pytest.mark.unit
    def test_trending_regime_matches_directional_signal(self):
        """Test that trending regime works well with buy/sell signals"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 80.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',  # Good match for directional trade
            'timeframe': '1H'
        }
        
        score = self.validator._check_regime_match(signal_data)
        assert score >= 0.80, f"Trending regime should match directional signal, got {score}"
    
    @pytest.mark.unit
    def test_breakout_regime_matches(self):
        """Test breakout regime validation"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'breakout',
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'breakout',
            'timeframe': '1H'
        }
        
        score = self.validator._check_regime_match(signal_data)
        assert score >= 0.75, f"Breakout regime should be valid, got {score}"
    
    @pytest.mark.unit
    def test_ranging_regime_lower_score(self):
        """Test that ranging regime with breakout strategy gets lower score"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'breakout',  # Breakout in ranging market = risky
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'ranging',  # Breakout in range = lower confidence
            'timeframe': '1H'
        }
        
        score = self.validator._check_regime_match(signal_data)
        assert score <= 0.70, f"Ranging regime with breakout should get lower score, got {score}"


class TestSentimentCoherence:
    """Test sentiment_coherence validation criterion"""
    
    def setup_method(self):
        """Initialize validator"""
        self.validator = SignalValidator()
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_bullish_news_matches_buy_signal(self):
        """Test that bullish news aligns with buy signals"""
        from zennews.models import NewsEvent
        
        symbol = "EURUSD_BULLISH_TEST"
        
        # Create bullish news event
        NewsEvent.objects.create(
            symbol=symbol,
            headline="ECB Raises Rates - Bullish for EUR",
            sentiment=0.75,  # Bullish
            impact_level='high',
            timestamp=timezone.now() - timedelta(hours=2)
        )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',  # Matches bullish sentiment
            'strategy': 'smc',
            'confidence': 80.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_sentiment(signal_data)
        
        # Clean up
        NewsEvent.objects.filter(symbol=symbol).delete()
        
        assert score >= 0.85, f"Bullish news + buy signal should score high, got {score}"
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_bearish_news_conflicts_with_buy_signal(self):
        """Test that bearish news conflicts with buy signals"""
        from zennews.models import NewsEvent
        
        symbol = "EURUSD_BEARISH_TEST"
        
        # Create bearish news event
        NewsEvent.objects.create(
            symbol=symbol,
            headline="Eurozone GDP Contracts - Bearish for EUR",
            sentiment=-0.70,  # Bearish
            impact_level='high',
            timestamp=timezone.now() - timedelta(hours=1)
        )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',  # Conflicts with bearish sentiment
            'strategy': 'smc',
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_sentiment(signal_data)
        
        # Clean up
        NewsEvent.objects.filter(symbol=symbol).delete()
        
        assert score <= 0.50, f"Bearish news + buy signal should score low, got {score}"
    
    @pytest.mark.unit
    def test_no_news_returns_neutral(self):
        """Test that lack of news returns neutral score"""
        signal_data = {
            'symbol': 'NOPAIR_NO_NEWS',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_sentiment(signal_data)
        
        # Should return neutral score when no news
        assert 0.70 <= score <= 0.80, f"Expected neutral score for no news, got {score}"


class TestHistoricalReliability:
    """Test historical_reliability validation criterion"""
    
    def setup_method(self):
        """Initialize validator"""
        self.validator = SignalValidator()
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_good_strategy_performance_high_score(self):
        """Test that strategies with good win rates score high"""
        from signals.models import StrategyPerformance
        
        strategy_name = "smc_test_good"
        symbol = "EURUSD"
        
        # Create strategy with good performance
        StrategyPerformance.objects.create(
            strategy_name=strategy_name,
            symbol=symbol,
            total_trades=50,
            winning_trades=35,
            losing_trades=15,
            win_rate=70.0,  # Good win rate
            avg_win=85.5,
            avg_loss=48.2,
            profit_factor=1.77
        )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',
            'strategy': strategy_name,
            'confidence': 80.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_historical_performance(signal_data)
        
        # Clean up
        StrategyPerformance.objects.filter(strategy_name=strategy_name).delete()
        
        assert score >= 0.85, f"Good win rate (70%) should score high, got {score}"
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_poor_strategy_performance_low_score(self):
        """Test that strategies with poor win rates score low"""
        from signals.models import StrategyPerformance
        
        strategy_name = "random_test_poor"
        symbol = "USDJPY"
        
        # Create strategy with poor performance
        StrategyPerformance.objects.create(
            strategy_name=strategy_name,
            symbol=symbol,
            total_trades=30,
            winning_trades=10,
            losing_trades=20,
            win_rate=33.3,  # Poor win rate
            avg_win=50.0,
            avg_loss=55.0,
            profit_factor=0.91
        )
        
        signal_data = {
            'symbol': symbol,
            'side': 'sell',
            'strategy': strategy_name,
            'confidence': 70.0,
            'price': 149.50,
            'sl': 150.00,
            'tp': 148.50,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_historical_performance(signal_data)
        
        # Clean up
        StrategyPerformance.objects.filter(strategy_name=strategy_name).delete()
        
        assert score <= 0.50, f"Poor win rate (33%) should score low, got {score}"
    
    @pytest.mark.unit
    def test_insufficient_trades_returns_neutral(self):
        """Test that strategies with <10 trades return neutral score"""
        signal_data = {
            'symbol': 'GBPJPY',
            'side': 'buy',
            'strategy': 'new_untested_strategy',
            'confidence': 75.0,
            'price': 185.00,
            'sl': 184.50,
            'tp': 186.00,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_historical_performance(signal_data)
        
        # Should return neutral score (0.7) for insufficient data
        assert 0.65 <= score <= 0.75, f"Expected neutral score for new strategy, got {score}"


class TestPsychologicalSafety:
    """Test psychological_safety validation criterion"""
    
    def setup_method(self):
        """Initialize validator"""
        self.validator = SignalValidator()
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_normal_trading_frequency_high_score(self):
        """Test that normal trading frequency gets high score"""
        from signals.models import Signal
        
        symbol = "EURUSD_NORMAL_FREQ"
        
        # Create 3 signals in last 4 hours (normal)
        for i in range(3):
            Signal.objects.create(
                symbol=symbol,
                timeframe="1H",
                side="buy",
                sl=1.0750,
                tp=1.0900,
                confidence=75.0,
                strategy="smc",
                regime="Trend",
                price=1.0800,
                received_at=timezone.now() - timedelta(hours=4-i)
            )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 80.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        score = self.validator._check_psychological_factors(signal_data)
        
        # Clean up
        Signal.objects.filter(symbol=symbol).delete()
        
        assert score >= 0.85, f"Normal frequency should score high, got {score}"
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_overtrading_low_score(self):
        """Test that overtrading (≥5 signals in 4 hours) scores low"""
        from signals.models import Signal
        
        symbol = "EURUSD_OVERTRADE"
        
        # Create 8 signals in last 4 hours (overtrading)
        for i in range(8):
            Signal.objects.create(
                symbol=symbol,
                timeframe="15M",
                side="buy" if i % 2 == 0 else "sell",
                sl=1.0750,
                tp=1.0900,
                confidence=70.0,
                strategy="scalping",
                regime="Trend",
                price=1.0800 + (i * 0.0010),
                received_at=timezone.now() - timedelta(minutes=(240-i*30))
            )
        
        signal_data = {
            'symbol': symbol,
            'side': 'buy',
            'strategy': 'scalping',
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '15M'
        }
        
        score = self.validator._check_psychological_factors(signal_data)
        
        # Clean up
        Signal.objects.filter(symbol=symbol).delete()
        
        assert score <= 0.75, f"Overtrading should score low (≤0.75), got {score}"


class TestValidateSignalEndToEnd:
    """Test the complete validate_signal() function"""
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    def test_high_quality_signal_approved(self):
        """Test that high-quality signals get approved status"""
        result = validate_signal(VALID_WEBHOOK_HIGH_QUALITY)
        
        assert result['status'] == 'approved', f"High quality signal should be approved, got {result['status']}"
        assert result['truth_index'] >= 75, f"Truth index should be ≥75, got {result['truth_index']}"
        assert len(result['validation_notes']) > 0, "Should have validation notes"
        assert 'breakdown' in result, "Should include breakdown"
        assert 'recommendation' in result, "Should include recommendation"
    
    @pytest.mark.unit
    @pytest.mark.requires_db
    def test_low_quality_signal_rejected(self):
        """Test that low-quality signals get rejected or conditional status"""
        result = validate_signal(VALID_WEBHOOK_LOW_QUALITY)
        
        assert result['status'] in ['rejected', 'conditional'], f"Low quality signal should be rejected/conditional, got {result['status']}"
        assert result['truth_index'] <= 75, f"Truth index should be ≤75, got {result['truth_index']}"
    
    @pytest.mark.unit
    def test_poor_rr_signal_penalized(self):
        """Test that poor R:R ratio lowers truth index"""
        result = validate_signal(WEBHOOK_POOR_RISK_REWARD)
        
        assert result['truth_index'] < 80, f"Poor R:R should result in reduced truth index, got {result['truth_index']}"
        assert result['breakdown']['technical_integrity'] < 85.0, "Technical score should be penalized for poor R:R"
    
    @pytest.mark.unit
    def test_missing_fields_handled_gracefully(self):
        """Test that missing optional fields don't crash validation"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',
            'confidence': 75.0,
            # price missing (optional)
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        result = validate_signal(signal_data)
        
        assert 'truth_index' in result, "Should return valid result even with missing price"
        assert 0 <= result['truth_index'] <= 100, "Truth index should be in valid range"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
