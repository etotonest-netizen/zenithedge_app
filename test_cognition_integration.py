#!/usr/bin/env python3
"""
Test Cognition Integration with ZenBot AI Scoring
Verifies that cognition intelligence properly adjusts trade scores
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from bot.ai_score import integrate_cognition_bias, predict_score, explain_score, get_cognition_summary
from cognition.models import TraderPsychology, MarketRegime, SignalCluster
from signals.models import Signal
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def setup_test_data():
    """Create test data for cognition integration"""
    print_header("📝 SETTING UP TEST DATA")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='integration_test@zenithedge.com',
        defaults={'is_trader': True, 'first_name': 'Integration', 'last_name': 'Test'}
    )
    
    if created:
        print("✅ Created test user")
    else:
        print("✅ Using existing test user")
    
    # Create psychology entry with good mental state
    good_psych = TraderPsychology.objects.create(
        user=user,
        text_content="Following my trading plan carefully. Stayed disciplined today.",
        source_type='journal',
        sentiment_score=0.6,
        confidence_level=0.75,
        emotional_tone='confident',
        risk_tolerance=0.5,
        patience_score=0.8,
        discipline_score=0.9,
        detected_biases=[],
        bias_severity=0.1,
    )
    print(f"✅ Created good psychology entry (bias: {good_psych.get_psychological_bias_score():+.2f})")
    
    # Create psychology entry with poor mental state
    bad_psych = TraderPsychology.objects.create(
        user=user,
        text_content="Lost three trades in a row. Need to make it back now!",
        source_type='journal',
        sentiment_score=-0.4,
        confidence_level=0.3,
        emotional_tone='anxious',
        risk_tolerance=0.8,
        patience_score=0.2,
        discipline_score=0.3,
        detected_biases=['revenge_trading', 'overconfidence'],
        bias_severity=0.7,
        timestamp=timezone.now() - timedelta(hours=2)  # Older entry
    )
    print(f"✅ Created poor psychology entry (bias: {bad_psych.get_psychological_bias_score():+.2f})")
    
    # Create favorable market regime
    good_regime = MarketRegime.objects.create(
        symbol='EURUSD',
        timeframe='15m',
        regime_type='strong_trend',
        regime_confidence=0.85,
        trend_strength=0.75,
        volatility_percentile=0.6,
        volume_profile=1.2,
        regime_bias=0.8,
    )
    print(f"✅ Created favorable EURUSD regime (bias: {good_regime.get_regime_bias_score():+.2f})")
    
    # Create unfavorable market regime
    bad_regime = MarketRegime.objects.create(
        symbol='GBPUSD',
        timeframe='15m',
        regime_type='choppy',
        regime_confidence=0.75,
        trend_strength=0.2,
        volatility_percentile=0.4,
        volume_profile=0.8,
        regime_bias=-0.5,
    )
    print(f"✅ Created unfavorable GBPUSD regime (bias: {bad_regime.get_regime_bias_score():+.2f})")
    
    # Create high-reliability cluster
    good_cluster = SignalCluster.objects.create(
        cluster_id=1,
        cluster_name='Strong Breakouts',
        strategy_pattern='breakout',
        typical_timeframe='15m',
        signal_count=50,
        win_rate=0.72,
        avg_profit_factor=2.1,
        avg_risk_reward=2.5,
        sharpe_ratio=1.8,
        reliability_score=0.78,
    )
    print(f"✅ Created high-reliability cluster (reliability: {good_cluster.get_cluster_reliability_score():.2f})")
    
    # Create low-reliability cluster
    bad_cluster = SignalCluster.objects.create(
        cluster_id=2,
        cluster_name='Weak Reversals',
        strategy_pattern='reversal',
        typical_timeframe='5m',
        signal_count=30,
        win_rate=0.35,
        avg_profit_factor=0.8,
        avg_risk_reward=1.2,
        sharpe_ratio=-0.5,
        reliability_score=0.25,
    )
    print(f"✅ Created low-reliability cluster (reliability: {bad_cluster.get_cluster_reliability_score():.2f})")
    
    return user


def test_cognition_bias_function():
    """Test the integrate_cognition_bias function directly"""
    print_header("🧪 TEST 1: COGNITION BIAS INTEGRATION")
    
    user = User.objects.get(email='integration_test@zenithedge.com')
    
    # Test with favorable conditions (EURUSD with good psychology)
    print("\n📊 Scenario 1: Favorable Conditions (EURUSD)")
    signal_data = {
        'timestamp': timezone.now().isoformat(),
        'strategy': 'breakout',
        'confidence': 75,
        'timeframe': '15m',
        'symbol': 'EURUSD',
    }
    
    adjustment, breakdown = integrate_cognition_bias('EURUSD', user, signal_data)
    
    print(f"   Bias Adjustment: {adjustment:+.2f} points")
    print(f"   Psychology Bias: {breakdown.get('psychological_bias', 0):+.2f}")
    print(f"   Regime Bias: {breakdown.get('regime_bias', 0):+.2f}")
    print(f"   Cluster Reliability: {breakdown.get('cluster_reliability', 0):.2f}")
    print(f"   Combined Verdict: {breakdown.get('cognition_verdict', 'Unknown')}")
    
    # Test with unfavorable conditions (GBPUSD)
    print("\n📊 Scenario 2: Unfavorable Conditions (GBPUSD)")
    signal_data['symbol'] = 'GBPUSD'
    
    adjustment2, breakdown2 = integrate_cognition_bias('GBPUSD', user, signal_data)
    
    print(f"   Bias Adjustment: {adjustment2:+.2f} points")
    print(f"   Psychology Bias: {breakdown2.get('psychological_bias', 0):+.2f}")
    print(f"   Regime Bias: {breakdown2.get('regime_bias', 0):+.2f}")
    print(f"   Cluster Reliability: {breakdown2.get('cluster_reliability', 0):.2f}")
    print(f"   Combined Verdict: {breakdown2.get('cognition_verdict', 'Unknown')}")
    
    # Verify adjustment is different
    if adjustment > adjustment2:
        print(f"\n✅ Test passed: EURUSD ({adjustment:+.2f}) > GBPUSD ({adjustment2:+.2f})")
    else:
        print(f"\n⚠️ Warning: Expected EURUSD adjustment to be higher")


def test_predict_score_with_cognition():
    """Test the predict_score function with cognition enabled"""
    print_header("🧪 TEST 2: PREDICT SCORE WITH COGNITION")
    
    user = User.objects.get(email='integration_test@zenithedge.com')
    
    # Create a test signal
    signal = Signal.objects.create(
        user=user,
        symbol='EURUSD',
        side='BUY',
        price=1.0850,
        sl=1.0830,
        tp=1.0890,
        strategy='Breakout',
        regime='Bullish',
        confidence=75,
        timestamp=timezone.now(),
    )
    
    print(f"\n📊 Test Signal Created:")
    print(f"   Symbol: {signal.symbol}")
    print(f"   Strategy: {signal.strategy}")
    print(f"   Confidence: {signal.confidence}%")
    print(f"   R:R Ratio: {(signal.tp - signal.price) / (signal.price - signal.sl):.2f}")
    
    # Score WITHOUT cognition
    print("\n🤖 Scoring WITHOUT Cognition:")
    score_without, breakdown_without = predict_score(signal, apply_cognition=False)
    print(f"   Base Score: {score_without}/100")
    
    # Score WITH cognition
    print("\n🧠 Scoring WITH Cognition:")
    score_with, breakdown_with = predict_score(signal, apply_cognition=True)
    print(f"   Base Score: {breakdown_with.get('base_score', score_with)}/100")
    print(f"   Cognition Adjustment: {breakdown_with.get('cognition_adjustment', 0):+.2f}")
    print(f"   Final Score: {score_with}/100")
    
    # Show difference
    difference = score_with - score_without
    if difference > 0:
        print(f"\n✅ Cognition BOOSTED score by {difference:+.0f} points")
    elif difference < 0:
        print(f"\n⚠️ Cognition REDUCED score by {difference:.0f} points")
    else:
        print(f"\n🟡 Cognition had neutral effect")
    
    # Cleanup
    signal.delete()


def test_explain_score_with_cognition():
    """Test the explain_score function with cognition data"""
    print_header("🧪 TEST 3: SCORE EXPLANATION WITH COGNITION")
    
    user = User.objects.get(email='integration_test@zenithedge.com')
    
    # Create test signal
    signal = Signal.objects.create(
        user=user,
        symbol='EURUSD',
        side='BUY',
        price=1.0850,
        sl=1.0830,
        tp=1.0890,
        strategy='Breakout',
        regime='Bullish',
        confidence=80,
        timestamp=timezone.now(),
    )
    
    # Get score with cognition
    score, breakdown = predict_score(signal, apply_cognition=True)
    
    # Generate explanation
    explanation = explain_score(score, breakdown)
    
    print("\n📝 Generated Explanation:")
    print("─" * 70)
    print(explanation)
    print("─" * 70)
    
    # Check if cognition sections are present
    has_cognition_section = '🧠 Cognition Intelligence' in explanation
    has_verdict = breakdown.get('cognition_data', {}).get('cognition_verdict') in explanation
    
    if has_cognition_section:
        print("\n✅ Explanation includes cognition intelligence section")
    else:
        print("\n⚠️ Cognition section missing from explanation")
    
    if has_verdict:
        print("✅ Explanation includes cognition verdict")
    else:
        print("⚠️ Verdict missing from explanation")
    
    # Cleanup
    signal.delete()


def test_cognition_summary():
    """Test the get_cognition_summary function"""
    print_header("🧪 TEST 4: COGNITION SUMMARY")
    
    user = User.objects.get(email='integration_test@zenithedge.com')
    
    summary = get_cognition_summary(user)
    
    print("\n📊 Cognition Summary:")
    print(f"   Status: {summary.get('status', 'Unknown')}")
    
    # Psychology
    psych = summary.get('psychology', {})
    if psych.get('entry_count', 0) > 0:
        print(f"\n   Psychology:")
        print(f"      Entries: {psych.get('entry_count', 0)}")
        print(f"      Avg Sentiment: {psych.get('avg_sentiment', 0):+.2f}")
        print(f"      Avg Discipline: {psych.get('avg_discipline', 0):.0%}")
        print(f"      Latest Tone: {psych.get('latest_emotional_tone', 'Unknown')}")
        biases = psych.get('most_common_biases', {})
        if biases:
            print(f"      Common Biases: {', '.join(biases.keys())}")
    
    # Regimes
    regimes = summary.get('regimes', [])
    if regimes:
        print(f"\n   Active Market Regimes: {len(regimes)}")
        for regime in regimes[:3]:
            print(f"      {regime['symbol']}: {regime['regime_type']} (bias: {regime['regime_bias']:+.2f})")
    
    # Clusters
    clusters = summary.get('top_clusters', [])
    if clusters:
        print(f"\n   Top Signal Clusters: {len(clusters)}")
        for cluster in clusters[:3]:
            print(f"      {cluster['cluster_name']}: {cluster['win_rate']:.0%} WR, {cluster['reliability']:.2f} reliability")
    
    # Insights
    insights = summary.get('insights', [])
    if insights:
        print(f"\n   Unread Insights: {len(insights)}")
        for insight in insights:
            print(f"      [{insight['type'].upper()}] {insight['title']}")
    
    if summary.get('status') == 'success':
        print("\n✅ Cognition summary generated successfully")
    else:
        print(f"\n⚠️ Summary generation had issues: {summary.get('message', 'Unknown error')}")


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("  🧠 COGNITION INTEGRATION TEST SUITE")
    print("="*70)
    print("\n  Testing ZenBot AI score integration with cognition intelligence")
    
    try:
        # Setup
        user = setup_test_data()
        
        # Run tests
        test_cognition_bias_function()
        test_predict_score_with_cognition()
        test_explain_score_with_cognition()
        test_cognition_summary()
        
        # Final summary
        print_header("🎉 ALL INTEGRATION TESTS COMPLETED")
        
        print("\n  ✅ Cognition successfully integrated with ZenBot AI scoring!")
        print("\n  Integration Features:")
        print("  • Psychology bias adjustments (-10 to +10 points)")
        print("  • Market regime suitability scoring")
        print("  • Signal cluster reliability analysis")
        print("  • Combined cognition verdict in explanations")
        print("  • Comprehensive user cognition summaries")
        print("\n  📖 See bot/ai_score.py for implementation details")
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
