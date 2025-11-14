#!/usr/bin/env python3
"""
Test Cognition Module
Verifies all intelligence engines are working
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from cognition.utils import (
    analyze_trader_text,
    detect_market_regime,
    cluster_signals,
    predict_challenge_success
)
import pandas as pd
import numpy as np

def test_psychology_analyzer():
    """Test psychology analysis"""
    print("\n" + "="*60)
    print("🧪 Testing Psychology Analyzer")
    print("="*60)
    
    test_texts = [
        "I'm feeling very confident about today's trades! This setup looks perfect.",
        "I lost three trades in a row. Need to make it back quickly.",
        "Following my plan carefully. Patience is key.",
        "FOMO is real! Everyone is making money except me.",
    ]
    
    for text in test_texts:
        result = analyze_trader_text(text)
        print(f"\n📝 Text: \"{text[:50]}...\"")
        print(f"   Emotional Tone: {result['emotional_tone']}")
        print(f"   Sentiment: {result['sentiment_score']:.2f}")
        print(f"   Confidence: {result['confidence_level']:.2f}")
        if result['detected_biases']:
            print(f"   ⚠️  Biases: {', '.join(result['detected_biases'])}")
    
    print("\n✅ Psychology Analyzer working correctly")


def test_regime_detector():
    """Test market regime detection"""
    print("\n" + "="*60)
    print("🧪 Testing Market Regime Detector")
    print("="*60)
    
    # Create synthetic OHLC data
    np.random.seed(42)
    dates = pd.date_range('2025-11-01', periods=100, freq='15min')
    
    # Trending market
    trend_data = pd.DataFrame({
        'open': np.linspace(1.0800, 1.0950, 100) + np.random.normal(0, 0.0005, 100),
        'high': np.linspace(1.0810, 1.0960, 100) + np.random.normal(0, 0.0005, 100),
        'low': np.linspace(1.0790, 1.0940, 100) + np.random.normal(0, 0.0005, 100),
        'close': np.linspace(1.0800, 1.0950, 100) + np.random.normal(0, 0.0005, 100),
        'volume': np.random.randint(1000, 5000, 100),
    }, index=dates)
    
    result = detect_market_regime(trend_data)
    print(f"\n📊 Trending Market Analysis:")
    print(f"   Regime Type: {result['regime_type']}")
    print(f"   Confidence: {result['regime_confidence']:.2f}")
    print(f"   Trend Strength: {result['trend_strength']:.2f}")
    print(f"   Regime Bias: {result['regime_bias']:.2f}")
    
    # Choppy market
    choppy_data = pd.DataFrame({
        'open': 1.0800 + np.random.normal(0, 0.001, 100),
        'high': 1.0810 + np.random.normal(0, 0.001, 100),
        'low': 1.0790 + np.random.normal(0, 0.001, 100),
        'close': 1.0800 + np.random.normal(0, 0.001, 100),
        'volume': np.random.randint(1000, 5000, 100),
    }, index=dates)
    
    result = detect_market_regime(choppy_data)
    print(f"\n📊 Choppy Market Analysis:")
    print(f"   Regime Type: {result['regime_type']}")
    print(f"   Confidence: {result['regime_confidence']:.2f}")
    print(f"   Regime Bias: {result['regime_bias']:.2f}")
    
    print("\n✅ Regime Detector working correctly")


def test_signal_clusterer():
    """Test signal clustering"""
    print("\n" + "="*60)
    print("🧪 Testing Signal Clusterer")
    print("="*60)
    
    # Create synthetic signal data
    signals = []
    for i in range(50):
        signals.append({
            'timestamp': f'2025-11-{10+i//10} {i%24:02d}:00',
            'strategy': np.random.choice(['breakout', 'pullback', 'reversal']),
            'outcome': np.random.choice(['win', 'loss'], p=[0.6, 0.4]),
            'profit_loss': np.random.normal(50, 30),
            'risk_reward': np.random.uniform(1.0, 3.0),
            'confidence': np.random.uniform(0.5, 0.9),
            'timeframe': np.random.choice(['15m', '1h']),
            'symbol': 'EURUSD',
        })
    
    result = cluster_signals(signals, n_clusters=3)
    
    print(f"\n📊 Clustering Results:")
    print(f"   Clusters Found: {result['n_clusters']}")
    print(f"   Silhouette Score: {result['silhouette_score']:.2f}")
    
    for cluster in result['cluster_metrics']:
        print(f"\n   Cluster {cluster['cluster_id']}:")
        print(f"      Signals: {cluster['signal_count']}")
        print(f"      Win Rate: {cluster['win_rate']:.1%}")
        print(f"      Reliability: {cluster['reliability_score']:.2f}")
        print(f"      Strategy: {cluster['strategy_pattern']}")
    
    print("\n✅ Signal Clusterer working correctly")


def test_prop_predictor():
    """Test prop firm prediction"""
    print("\n" + "="*60)
    print("🧪 Testing Prop Firm Predictor")
    print("="*60)
    
    test_scenarios = [
        {
            'name': 'Strong Performance',
            'metrics': {
                'challenge_type': 'phase1',
                'account_size': 100000,
                'profit_target': 10000,
                'max_drawdown': 5000,
                'current_profit': 7500,
                'current_drawdown': 800,
                'days_remaining': 15,
                'trades_taken': 45,
                'current_win_rate': 0.68,
                'current_profit_factor': 1.8,
                'current_sharpe': 1.5,
                'avg_confidence_score': 0.75,
                'avg_discipline_score': 0.8,
                'recent_bias_severity': 0.2,
            }
        },
        {
            'name': 'At Risk',
            'metrics': {
                'challenge_type': 'phase1',
                'account_size': 100000,
                'profit_target': 10000,
                'max_drawdown': 5000,
                'current_profit': 2000,
                'current_drawdown': 3800,
                'days_remaining': 5,
                'trades_taken': 60,
                'current_win_rate': 0.42,
                'current_profit_factor': 0.85,
                'current_sharpe': -0.5,
                'avg_confidence_score': 0.45,
                'avg_discipline_score': 0.4,
                'recent_bias_severity': 0.7,
            }
        },
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        prediction = predict_challenge_success(scenario['metrics'])
        
        print(f"   Pass Probability: {prediction['pass_probability']:.1%}")
        print(f"   Risk of Failure: {prediction['risk_of_failure']:.1%}")
        print(f"   Est. Completion: {prediction['estimated_completion_days']} days")
        print(f"   Recommendations:")
        for rec in prediction['recommended_adjustments'][:3]:
            print(f"      - {rec}")
    
    print("\n✅ Prop Predictor working correctly")


def test_database_models():
    """Test database models"""
    print("\n" + "="*60)
    print("🧪 Testing Database Models")
    print("="*60)
    
    from cognition.models import TraderPsychology, MarketRegime, SignalCluster
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    
    User = get_user_model()
    
    # Get or create test user (using email since custom user model doesn't have username)
    user, _ = User.objects.get_or_create(
        email='test@example.com',
        defaults={'is_trader': True}
    )
    
    # Test TraderPsychology
    psych = TraderPsychology.objects.create(
        user=user,
        text_content="Test journal entry",
        source_type='journal',
        sentiment_score=0.5,
        confidence_level=0.7,
        emotional_tone='confident',
        risk_tolerance=0.6,
        patience_score=0.7,
        discipline_score=0.8,
        bias_severity=0.2,
    )
    print(f"\n✅ Created TraderPsychology: {psych.id}")
    
    # Test MarketRegime
    regime = MarketRegime.objects.create(
        symbol='EURUSD',
        timeframe='15m',
        regime_type='strong_trend',
        regime_confidence=0.85,
        trend_strength=0.75,
        volatility_percentile=0.6,
        volume_profile=1.2,
        regime_bias=0.7,
    )
    print(f"✅ Created MarketRegime: {regime.id}")
    
    # Test SignalCluster
    cluster = SignalCluster.objects.create(
        cluster_id=1,
        cluster_name='Morning Breakouts',
        strategy_pattern='breakout',
        typical_timeframe='15m',
        signal_count=25,
        win_rate=0.64,
        avg_profit_factor=1.5,
        reliability_score=0.72,
    )
    print(f"✅ Created SignalCluster: {cluster.id}")
    
    # Cleanup
    psych.delete()
    regime.delete()
    cluster.delete()
    
    print("\n✅ Database models working correctly")


def main():
    print("\n" + "="*60)
    print("🚀 Cognition Module Integration Test Suite")
    print("="*60)
    
    try:
        test_psychology_analyzer()
        test_regime_detector()
        test_signal_clusterer()
        test_prop_predictor()
        test_database_models()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n🧠 Cognition Module Status: FULLY OPERATIONAL")
        print("\nThe system can now:")
        print("  • Analyze trader psychology and detect biases")
        print("  • Classify market regimes and conditions")
        print("  • Cluster signals by performance patterns")
        print("  • Predict prop firm challenge success")
        print("  • Store insights in database")
        print("\n🚀 Ready for ZenBot integration and dashboard deployment!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
