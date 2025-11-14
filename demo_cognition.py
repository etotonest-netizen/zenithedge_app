#!/usr/bin/env python3
"""
Interactive Cognition Module Demo
Demonstrates the full cognitive intelligence system in action
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from cognition.models import (
    TraderPsychology, MarketRegime, SignalCluster, 
    PropFirmPrediction, CognitionInsight
)
from cognition.utils import (
    analyze_trader_text,
    detect_market_regime,
    cluster_signals,
    predict_challenge_success
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import numpy as np
import json

User = get_user_model()


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def demo_psychology_analysis():
    """Demo 1: Analyze trader psychology from journal entries"""
    print_header("📝 DEMO 1: TRADER PSYCHOLOGY ANALYSIS")
    
    # Get or create demo user
    user, created = User.objects.get_or_create(
        email='demo_trader@zenithedge.com',
        defaults={'is_trader': True, 'first_name': 'Demo', 'last_name': 'Trader'}
    )
    
    journal_entries = [
        {
            'text': "Amazing day! Hit all my targets. I'm on fire! This strategy can't lose. Going to increase my position size tomorrow.",
            'source': 'journal',
            'expected': 'overconfidence'
        },
        {
            'text': "Lost again today. I need to make this money back quickly. Doubling my position size on the next trade.",
            'source': 'journal',
            'expected': 'revenge_trading'
        },
        {
            'text': "Following my trading plan carefully. Waited for the perfect setup. Patience paid off with a 2R winner.",
            'source': 'journal',
            'expected': 'disciplined'
        },
        {
            'text': "Everyone on Twitter is making money on this crypto pump. I can't miss out! Jumping in now.",
            'source': 'journal',
            'expected': 'fomo'
        },
    ]
    
    print("\nAnalyzing 4 journal entries...")
    
    for i, entry in enumerate(journal_entries, 1):
        print(f"\n{'─'*70}")
        print(f"Entry #{i}: \"{entry['text'][:60]}...\"")
        
        # Analyze the text
        analysis = analyze_trader_text(entry['text'])
        
        # Save to database
        psych = TraderPsychology.objects.create(
            user=user,
            text_content=entry['text'],
            source_type=entry['source'],
            sentiment_score=analysis['sentiment_score'],
            confidence_level=analysis['confidence_level'],
            emotional_tone=analysis['emotional_tone'],
            key_phrases=analysis.get('key_phrases', []),
            entities=analysis.get('entities', []),
            risk_tolerance=analysis['risk_tolerance'],
            patience_score=analysis['patience_score'],
            discipline_score=analysis['discipline_score'],
            detected_biases=analysis['detected_biases'],
            bias_severity=analysis['bias_severity'],
        )
        
        # Display results
        print(f"\n  📊 Analysis Results:")
        print(f"     Emotional Tone: {analysis['emotional_tone'].upper()}")
        print(f"     Sentiment Score: {analysis['sentiment_score']:+.2f} (-1 to +1)")
        print(f"     Confidence Level: {analysis['confidence_level']:.0%}")
        print(f"     Risk Tolerance: {analysis['risk_tolerance']:.0%}")
        print(f"     Discipline Score: {analysis['discipline_score']:.0%}")
        print(f"     Patience Score: {analysis['patience_score']:.0%}")
        
        if analysis['detected_biases']:
            print(f"\n  ⚠️  COGNITIVE BIASES DETECTED:")
            for bias in analysis['detected_biases']:
                print(f"     • {bias.replace('_', ' ').title()}")
            print(f"     Severity: {analysis['bias_severity']:.0%}")
        
        # Get the bias score for AI adjustment
        bias_score = psych.get_psychological_bias_score()
        print(f"\n  🤖 AI Score Adjustment: {bias_score:+.2f} ({-1 if bias_score < 0 else +1}10 points)")
        
        if bias_score < -0.3:
            print(f"     ❌ HIGH RISK: Consider taking a break")
        elif bias_score < 0:
            print(f"     ⚠️  CAUTION: Watch for emotional trading")
        else:
            print(f"     ✅ GOOD STATE: Maintain discipline")
    
    total_entries = TraderPsychology.objects.filter(user=user).count()
    print(f"\n{'─'*70}")
    print(f"✅ Created {total_entries} psychology entries in database")
    
    return user


def demo_market_regime_detection():
    """Demo 2: Detect market regimes from price data"""
    print_header("📊 DEMO 2: MARKET REGIME DETECTION")
    
    symbols = ['EURUSD', 'GBPUSD', 'GOLD']
    timeframe = '15m'
    
    print("\nAnalyzing market conditions for 3 instruments...")
    
    for symbol in symbols:
        print(f"\n{'─'*70}")
        print(f"Symbol: {symbol}")
        
        # Generate synthetic OHLC data with different characteristics
        np.random.seed(hash(symbol) % 2**32)
        dates = pd.date_range(timezone.now() - timedelta(hours=24), periods=100, freq='15min')
        
        if symbol == 'EURUSD':
            # Strong uptrend
            base = np.linspace(1.0800, 1.0950, 100)
            ohlc_data = pd.DataFrame({
                'open': base + np.random.normal(0, 0.0003, 100),
                'high': base + np.random.normal(0.0010, 0.0003, 100),
                'low': base + np.random.normal(-0.0010, 0.0003, 100),
                'close': base + np.random.normal(0, 0.0003, 100),
                'volume': np.random.randint(1000, 5000, 100),
            }, index=dates)
        elif symbol == 'GBPUSD':
            # Choppy market
            base = 1.2800 + np.random.normal(0, 0.002, 100)
            ohlc_data = pd.DataFrame({
                'open': base,
                'high': base + np.abs(np.random.normal(0, 0.001, 100)),
                'low': base - np.abs(np.random.normal(0, 0.001, 100)),
                'close': base + np.random.normal(0, 0.0005, 100),
                'volume': np.random.randint(800, 3000, 100),
            }, index=dates)
        else:  # GOLD
            # Volatile breakout
            base = np.concatenate([
                np.ones(50) * 2650 + np.random.normal(0, 2, 50),
                np.linspace(2650, 2680, 50) + np.random.normal(0, 5, 50)
            ])
            ohlc_data = pd.DataFrame({
                'open': base,
                'high': base + np.abs(np.random.normal(3, 2, 100)),
                'low': base - np.abs(np.random.normal(3, 2, 100)),
                'close': base + np.random.normal(0, 2, 100),
                'volume': np.random.randint(2000, 10000, 100),
            }, index=dates)
        
        # Detect regime
        regime_data = detect_market_regime(ohlc_data)
        
        # Save to database
        regime = MarketRegime.objects.create(
            symbol=symbol,
            timeframe=timeframe,
            regime_type=regime_data['regime_type'],
            regime_confidence=regime_data['regime_confidence'],
            trend_strength=regime_data['trend_strength'],
            volatility_percentile=regime_data['volatility_percentile'],
            volume_profile=regime_data['volume_profile'],
            detected_patterns=regime_data['detected_patterns'],
            feature_vector=regime_data.get('feature_vector', {}),
            regime_bias=regime_data['regime_bias'],
        )
        
        # Display results
        regime_colors = {
            'strong_trend': '🟢',
            'weak_trend': '🟡',
            'choppy': '🔴',
            'squeeze': '🟠',
            'volatile': '🟣',
            'quiet': '⚪',
        }
        
        color = regime_colors.get(regime_data['regime_type'], '⚪')
        print(f"\n  {color} Regime Type: {regime_data['regime_type'].upper().replace('_', ' ')}")
        print(f"     Confidence: {regime_data['regime_confidence']:.0%}")
        print(f"     Trend Strength: {regime_data['trend_strength']:.0%}")
        print(f"     Volatility: {regime_data['volatility_percentile']:.0%} percentile")
        print(f"     Volume: {regime_data['volume_profile']:.2f}x average")
        
        if regime_data['detected_patterns']:
            print(f"\n  📈 Detected Patterns:")
            for pattern in regime_data['detected_patterns']:
                print(f"     • {pattern.replace('_', ' ').title()}")
        
        # Get regime bias for AI adjustment
        bias_score = regime.get_regime_bias_score()
        print(f"\n  🤖 Trading Suitability: {bias_score:+.2f}")
        
        if bias_score > 0.5:
            print(f"     ✅ EXCELLENT: Ideal conditions for trading")
        elif bias_score > 0:
            print(f"     ✅ GOOD: Favorable conditions")
        elif bias_score > -0.3:
            print(f"     ⚠️  NEUTRAL: Exercise caution")
        else:
            print(f"     ❌ AVOID: Poor conditions, stay out")
    
    total_regimes = MarketRegime.objects.count()
    print(f"\n{'─'*70}")
    print(f"✅ Created {total_regimes} regime entries in database")


def demo_signal_clustering():
    """Demo 3: Cluster trading signals by behavior"""
    print_header("🎯 DEMO 3: SIGNAL CLUSTERING & RELIABILITY")
    
    print("\nGenerating 100 historical signals...")
    
    # Generate diverse signal data
    signals = []
    strategies = ['breakout', 'pullback', 'reversal', 'momentum', 'scalp']
    timeframes = ['5m', '15m', '1h', '4h']
    
    np.random.seed(42)
    for i in range(100):
        strategy = np.random.choice(strategies)
        
        # Different strategies have different win rates
        if strategy == 'breakout':
            win_rate = 0.65
        elif strategy == 'pullback':
            win_rate = 0.70
        elif strategy == 'reversal':
            win_rate = 0.45
        elif strategy == 'momentum':
            win_rate = 0.60
        else:  # scalp
            win_rate = 0.55
        
        is_win = np.random.random() < win_rate
        
        signals.append({
            'timestamp': (timezone.now() - timedelta(days=30) + timedelta(hours=i*7)).isoformat(),
            'strategy': strategy,
            'outcome': 'win' if is_win else 'loss',
            'profit_loss': np.random.normal(100, 50) if is_win else np.random.normal(-50, 30),
            'risk_reward': np.random.uniform(1.5, 3.0) if is_win else np.random.uniform(0.3, 0.9),
            'confidence': np.random.uniform(0.6, 0.9),
            'timeframe': np.random.choice(timeframes),
            'symbol': np.random.choice(['EURUSD', 'GBPUSD', 'GOLD']),
        })
    
    # Cluster the signals
    cluster_data = cluster_signals(signals, n_clusters=5)
    
    print(f"\n  Clustered into {cluster_data['n_clusters']} groups")
    print(f"  Silhouette Score: {cluster_data['silhouette_score']:.2f} (quality metric)")
    
    # Save clusters to database
    for cluster in cluster_data['cluster_metrics']:
        SignalCluster.objects.create(
            cluster_id=cluster['cluster_id'],
            cluster_name=f"Cluster {cluster['cluster_id']} - {cluster['strategy_pattern']}",
            strategy_pattern=cluster['strategy_pattern'],
            typical_timeframe=cluster.get('typical_timeframe', '15m'),
            signal_count=cluster['signal_count'],
            win_rate=cluster['win_rate'],
            avg_profit_factor=cluster['avg_profit_factor'],
            avg_risk_reward=cluster['avg_risk_reward'],
            sharpe_ratio=cluster.get('sharpe_ratio', 0),
            feature_centroid=cluster.get('feature_centroid', {}),
            reliability_score=cluster['reliability_score'],
            confidence_interval=cluster.get('confidence_interval', 0.95),
            preferred_regimes=['strong_trend'] if cluster['win_rate'] > 0.6 else ['any'],
        )
    
    print(f"\n{'─'*70}")
    print("  Cluster Performance Analysis:\n")
    
    # Sort by reliability
    sorted_clusters = sorted(cluster_data['cluster_metrics'], 
                            key=lambda x: x['reliability_score'], reverse=True)
    
    for i, cluster in enumerate(sorted_clusters, 1):
        print(f"  #{i} {cluster['strategy_pattern'].upper()}")
        print(f"     Signals: {cluster['signal_count']}")
        print(f"     Win Rate: {cluster['win_rate']:.1%}")
        print(f"     Profit Factor: {cluster['avg_profit_factor']:.2f}")
        print(f"     Avg Risk/Reward: {cluster['avg_risk_reward']:.2f}R")
        
        reliability = cluster['reliability_score']
        if reliability > 0.7:
            rating = "⭐⭐⭐ EXCELLENT"
        elif reliability > 0.5:
            rating = "⭐⭐ GOOD"
        elif reliability > 0.3:
            rating = "⭐ AVERAGE"
        else:
            rating = "❌ POOR"
        
        print(f"     Reliability: {reliability:.2f} - {rating}")
        print()
    
    total_clusters = SignalCluster.objects.count()
    print(f"{'─'*70}")
    print(f"✅ Created {total_clusters} signal clusters in database")


def demo_prop_firm_prediction(user):
    """Demo 4: Predict prop firm challenge success"""
    print_header("💰 DEMO 4: PROP FIRM CHALLENGE PREDICTOR")
    
    scenarios = [
        {
            'name': 'Strong Performer (Phase 1)',
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
        },
        {
            'name': 'Struggling Trader (Phase 1)',
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
        },
        {
            'name': 'Steady Progress (Phase 2)',
            'challenge_type': 'phase2',
            'account_size': 100000,
            'profit_target': 5000,
            'max_drawdown': 4000,
            'current_profit': 3200,
            'current_drawdown': 1500,
            'days_remaining': 20,
            'trades_taken': 55,
            'current_win_rate': 0.58,
            'current_profit_factor': 1.4,
            'current_sharpe': 0.9,
            'avg_confidence_score': 0.65,
            'avg_discipline_score': 0.7,
            'recent_bias_severity': 0.3,
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{'─'*70}")
        print(f"Scenario: {scenario['name']}")
        print(f"Challenge: {scenario['challenge_type'].upper()}")
        print(f"Target: ${scenario['profit_target']:,} | Max DD: ${scenario['max_drawdown']:,}")
        print(f"Current P/L: ${scenario['current_profit']:,} | Current DD: ${scenario['current_drawdown']:,}")
        print(f"Days Left: {scenario['days_remaining']}")
        
        # Predict outcome
        prediction = predict_challenge_success(scenario)
        
        # Save to database
        prop_pred = PropFirmPrediction.objects.create(
            user=user,
            challenge_type=scenario['challenge_type'],
            account_size=scenario['account_size'],
            profit_target=scenario['profit_target'],
            max_drawdown=scenario['max_drawdown'],
            current_profit=scenario['current_profit'],
            current_drawdown=scenario['current_drawdown'],
            trades_taken=scenario['trades_taken'],
            days_remaining=scenario['days_remaining'],
            current_win_rate=scenario['current_win_rate'],
            current_profit_factor=scenario['current_profit_factor'],
            current_sharpe=scenario['current_sharpe'],
            avg_confidence_score=scenario['avg_confidence_score'],
            avg_discipline_score=scenario['avg_discipline_score'],
            recent_bias_severity=scenario['recent_bias_severity'],
            pass_probability=prediction['pass_probability'],
            estimated_completion_days=prediction['estimated_completion_days'],
            risk_of_failure=prediction['risk_of_failure'],
            recommended_adjustments=prediction['recommended_adjustments'],
        )
        
        # Display prediction
        pass_prob = prediction['pass_probability']
        if pass_prob > 0.7:
            status = "🟢 LIKELY TO PASS"
        elif pass_prob > 0.5:
            status = "🟡 UNCERTAIN"
        else:
            status = "🔴 AT RISK"
        
        print(f"\n  {status}")
        print(f"  Pass Probability: {pass_prob:.1%}")
        print(f"  Failure Risk: {prediction['risk_of_failure']:.1%}")
        print(f"  Est. Completion: {prediction['estimated_completion_days']} days")
        
        if prediction['recommended_adjustments']:
            print(f"\n  📋 Recommendations:")
            for rec in prediction['recommended_adjustments'][:5]:
                print(f"     • {rec}")
        
        # Get status badge
        badge_color, badge_label = prop_pred.get_status_badge()
        print(f"\n  Status Badge: {badge_color.upper()} - {badge_label}")
    
    total_predictions = PropFirmPrediction.objects.filter(user=user).count()
    print(f"\n{'─'*70}")
    print(f"✅ Created {total_predictions} prop firm predictions in database")


def demo_insights_generation(user):
    """Demo 5: Generate cognition insights"""
    print_header("💡 DEMO 5: COGNITION INSIGHTS & ALERTS")
    
    print("\nGenerating intelligent insights from analysis...")
    
    # Get latest psychology entry
    latest_psych = TraderPsychology.objects.filter(user=user).order_by('-timestamp').first()
    if latest_psych and latest_psych.detected_biases:
        CognitionInsight.objects.create(
            user=user,
            insight_type='psychology',
            title='Cognitive Bias Detected',
            message=f"Your recent journal shows signs of {', '.join(latest_psych.detected_biases)}. "
                   f"Consider taking a break or reviewing your trading rules.",
            severity='warning',
            related_data={'biases': latest_psych.detected_biases},
            is_actionable=True,
        )
    
    # Get best performing cluster
    best_cluster = SignalCluster.objects.order_by('-reliability_score').first()
    if best_cluster:
        CognitionInsight.objects.create(
            user=user,
            insight_type='performance',
            title='High-Performance Pattern Identified',
            message=f"Your {best_cluster.strategy_pattern} signals have a {best_cluster.win_rate:.1%} win rate "
                   f"with reliability score of {best_cluster.reliability_score:.2f}. Focus on this pattern.",
            severity='info',
            related_data={'cluster_id': best_cluster.cluster_id},
            is_actionable=True,
        )
    
    # Check regime conditions
    unfavorable_regimes = MarketRegime.objects.filter(regime_bias__lt=-0.3)
    if unfavorable_regimes.exists():
        regime = unfavorable_regimes.first()
        CognitionInsight.objects.create(
            user=user,
            insight_type='market',
            title='Unfavorable Market Conditions',
            message=f"{regime.symbol} ({regime.timeframe}) is in a {regime.regime_type} regime. "
                   f"Consider reducing exposure or avoiding trades.",
            severity='warning',
            related_data={'symbol': regime.symbol, 'regime': regime.regime_type},
            is_actionable=True,
        )
    
    # Check prop firm predictions
    at_risk_predictions = PropFirmPrediction.objects.filter(
        user=user, 
        pass_probability__lt=0.5
    )
    if at_risk_predictions.exists():
        pred = at_risk_predictions.first()
        CognitionInsight.objects.create(
            user=user,
            insight_type='alert',
            title='Prop Challenge At Risk',
            message=f"Your {pred.challenge_type} challenge has only {pred.pass_probability:.0%} pass probability. "
                   f"Review recommendations urgently.",
            severity='critical',
            related_data={'challenge_type': pred.challenge_type},
            is_actionable=True,
        )
    
    # Display all insights
    insights = CognitionInsight.objects.filter(user=user).order_by('-timestamp')
    
    print(f"\n  Generated {insights.count()} insights:\n")
    
    severity_icons = {
        'info': 'ℹ️ ',
        'warning': '⚠️ ',
        'critical': '🚨',
    }
    
    for insight in insights:
        icon = severity_icons.get(insight.severity, '📝')
        print(f"  {icon} [{insight.insight_type.upper()}] {insight.title}")
        print(f"     {insight.message}")
        if insight.is_actionable:
            print(f"     ⚡ ACTION REQUIRED")
        print()
    
    print(f"{'─'*70}")
    print(f"✅ Created {insights.count()} insights in database")


def demo_database_summary():
    """Show summary of all data in database"""
    print_header("📊 DATABASE SUMMARY")
    
    print("\nCognition Module Data:")
    print(f"\n  TraderPsychology entries: {TraderPsychology.objects.count()}")
    print(f"  MarketRegime entries: {MarketRegime.objects.count()}")
    print(f"  SignalCluster entries: {SignalCluster.objects.count()}")
    print(f"  PropFirmPrediction entries: {PropFirmPrediction.objects.count()}")
    print(f"  CognitionInsight entries: {CognitionInsight.objects.count()}")
    
    # Show latest entries
    print("\n  Latest Psychology Analysis:")
    latest_psych = TraderPsychology.objects.order_by('-timestamp').first()
    if latest_psych:
        print(f"    User: {latest_psych.user.email}")
        print(f"    Emotional Tone: {latest_psych.emotional_tone}")
        print(f"    Sentiment: {latest_psych.sentiment_score:+.2f}")
        print(f"    Discipline: {latest_psych.discipline_score:.0%}")
    
    print("\n  Latest Market Regime:")
    latest_regime = MarketRegime.objects.order_by('-timestamp').first()
    if latest_regime:
        print(f"    Symbol: {latest_regime.symbol}")
        print(f"    Regime: {latest_regime.regime_type}")
        print(f"    Trading Bias: {latest_regime.regime_bias:+.2f}")
    
    print("\n  Best Performing Cluster:")
    best_cluster = SignalCluster.objects.order_by('-reliability_score').first()
    if best_cluster:
        print(f"    Strategy: {best_cluster.strategy_pattern}")
        print(f"    Win Rate: {best_cluster.win_rate:.1%}")
        print(f"    Reliability: {best_cluster.reliability_score:.2f}")
    
    print("\n  Latest Prop Prediction:")
    latest_pred = PropFirmPrediction.objects.order_by('-timestamp').first()
    if latest_pred:
        print(f"    Challenge: {latest_pred.challenge_type}")
        print(f"    Pass Probability: {latest_pred.pass_probability:.1%}")
        print(f"    Status: {latest_pred.get_status_badge()[1]}")


def main():
    """Run the full interactive demo"""
    print("\n" + "="*70)
    print("  🧠 ZENITHEDGE COGNITION MODULE - INTERACTIVE DEMO")
    print("="*70)
    print("\n  This demo will:")
    print("  1. Analyze trader psychology from journal entries")
    print("  2. Detect market regimes from price data")
    print("  3. Cluster trading signals by behavior")
    print("  4. Predict prop firm challenge outcomes")
    print("  5. Generate intelligent insights and alerts")
    print("\n  All data will be saved to the database for inspection.")
    
    input("\n  Press ENTER to begin demo...")
    
    try:
        # Run all demos in sequence
        user = demo_psychology_analysis()
        demo_market_regime_detection()
        demo_signal_clustering()
        demo_prop_firm_prediction(user)
        demo_insights_generation(user)
        demo_database_summary()
        
        # Final summary
        print_header("🎉 DEMO COMPLETE!")
        
        print("\n  ✅ All 5 intelligence systems demonstrated successfully!")
        print("\n  Next Steps:")
        print("  • Integrate with ZenBot AI scoring (bot/ai_score.py)")
        print("  • Build dashboard UI for visualizations")
        print("  • Create management commands for automation")
        print("  • Configure Django admin for management")
        print("\n  📖 See COGNITION_STATUS.md for full documentation")
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
