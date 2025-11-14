"""
Generate diverse test trading signals with AI validation
"""
import os
import django
import random
from datetime import timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from signals.models import Signal, TradeValidation
from zennews.models import NewsEvent
from zenbot.contextualizer_v2 import generate_narrative

User = get_user_model()

# Trading pairs with realistic price ranges
TRADING_PAIRS = {
    'EURUSD': {'price_range': (1.0500, 1.1200), 'pip_value': 0.0001},
    'GBPUSD': {'price_range': (1.2400, 1.3200), 'pip_value': 0.0001},
    'USDJPY': {'price_range': (145.00, 152.00), 'pip_value': 0.01},
    'AUDUSD': {'price_range': (0.6400, 0.6800), 'pip_value': 0.0001},
    'USDCAD': {'price_range': (1.3500, 1.3900), 'pip_value': 0.0001},
    'NZDUSD': {'price_range': (0.5800, 0.6200), 'pip_value': 0.0001},
    'XAUUSD': {'price_range': (2600.00, 2750.00), 'pip_value': 0.01},
    'BTCUSD': {'price_range': (85000.00, 95000.00), 'pip_value': 1.00},
}

TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1D']
SIDES = ['buy', 'sell']
STRATEGIES = ['ZenithEdge', 'TrendFollower', 'MeanReversion', 'BreakoutPro']
REGIMES = ['Trend', 'Range', 'Breakout', 'Reversal', 'Consolidation']

def generate_realistic_signal(symbol, user):
    """Generate a realistic trading signal"""
    config = TRADING_PAIRS[symbol]
    price = round(random.uniform(*config['price_range']), 4 if config['pip_value'] < 1 else 2)
    side = random.choice(SIDES)
    timeframe = random.choice(TIMEFRAMES)
    strategy = random.choice(STRATEGIES)
    regime = random.choice(REGIMES)
    confidence = round(random.uniform(65.0, 95.0), 1)
    
    # Calculate SL and TP based on side and realistic R:R
    pip_value = config['pip_value']
    sl_pips = random.randint(20, 80) * pip_value
    rr_ratio = random.uniform(1.5, 3.0)
    tp_pips = sl_pips * rr_ratio
    
    if side == 'buy':
        sl = round(price - sl_pips, 4 if pip_value < 1 else 2)
        tp = round(price + tp_pips, 4 if pip_value < 1 else 2)
    else:
        sl = round(price + sl_pips, 4 if pip_value < 1 else 2)
        tp = round(price - tp_pips, 4 if pip_value < 1 else 2)
    
    # Random timestamp within last 7 days
    hours_ago = random.randint(0, 168)
    timestamp = timezone.now() - timedelta(hours=hours_ago)
    
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'side': side,
        'sl': sl,
        'tp': tp,
        'confidence': confidence,
        'strategy': strategy,
        'regime': regime,
        'price': price,
        'timestamp': timestamp,
        'user': user,
        'is_allowed': True,
        'rejection_reason': ''  # Empty string instead of None
    }

def create_validation_for_signal(signal):
    """Create AI validation with news context for signal"""
    from zenbot.validation_engine import validate_signal
    
    # Prepare signal data for validation
    signal_data = {
        'symbol': signal.symbol,
        'timeframe': signal.timeframe,
        'side': signal.side,
        'sl': float(signal.sl),
        'tp': float(signal.tp),
        'confidence': float(signal.confidence),
        'strategy': signal.strategy,
        'regime': signal.regime,
        'price': float(signal.price) if signal.price else None
    }
    
    # Run AI validation
    try:
        validation_result = validate_signal(signal_data)
        truth_index = validation_result.get('truth_index', 75.0)
        validation_status = validation_result.get('status', 'conditional')
        
        # Generate narrative
        narrative_result = generate_narrative(
            signal_data,
            validation_result,
            return_metadata=True
        )
        
        # Handle both dict and string returns
        if isinstance(narrative_result, dict):
            context_narrative = narrative_result.get('composed_narrative', 
                                                    narrative_result.get('narrative', 'AI analysis complete'))
            quality_metrics = narrative_result.get('quality_metrics', {})
            kb_concepts_used = narrative_result.get('kb_concepts_used', 0)
        else:
            context_narrative = str(narrative_result)
            quality_metrics = {}
            kb_concepts_used = 0
        
        # Fetch recent news for this symbol
        news_context = None
        try:
            cutoff_time = timezone.now() - timedelta(hours=12)
            recent_news = NewsEvent.objects.filter(
                symbol__iexact=signal.symbol,
                timestamp__gte=cutoff_time
            ).order_by('-timestamp')[:3]
            
            if recent_news.exists():
                news_items = []
                for news in recent_news:
                    news_items.append(f"{news.get_time_ago()}: {news.headline}")
                news_context = " | ".join(news_items)
        except Exception as e:
            print(f"  ⚠️  Failed to fetch news: {e}")
        
        # Add news_context to quality_metrics
        if news_context:
            quality_metrics['news_context'] = news_context
        
        # Create validation record
        validation = TradeValidation.objects.create(
            signal=signal,
            truth_index=truth_index,
            status=validation_status,
            breakdown=validation_result.get('breakdown', {}),
            validation_notes=validation_result.get('validation_notes', []),
            context_summary=context_narrative,
            recommendation=validation_result.get('recommendation', ''),
            accuracy_history={},
            quality_metrics=quality_metrics,
            kb_concepts_used=kb_concepts_used
        )
        
        return validation
        
    except Exception as e:
        print(f"  ⚠️  Validation failed: {e}")
        return None

def main():
    print("🚀 Generating 50 test trading signals...\n")
    
    # Get or create test user
    user = User.objects.filter(email='admin1@zenithedge.com').first()
    if not user:
        print("❌ User admin1@zenithedge.com not found!")
        return
    
    print(f"✅ Using user: {user.email}\n")
    
    created_count = 0
    validated_count = 0
    
    for i in range(50):
        # Pick random symbol
        symbol = random.choice(list(TRADING_PAIRS.keys()))
        
        try:
            # Generate signal data
            signal_data = generate_realistic_signal(symbol, user)
            
            # Create signal
            signal = Signal.objects.create(**signal_data)
            created_count += 1
            
            # Create validation
            validation = create_validation_for_signal(signal)
            if validation:
                validated_count += 1
                news_indicator = "📰" if 'news_context' in validation.quality_metrics else "  "
                print(f"{news_indicator} #{signal.id:3d} {signal.symbol:7s} {signal.side:4s} @ {signal.price:9.4f} | "
                      f"Truth: {validation.truth_index:.1f} | Concepts: {validation.kb_concepts_used}")
            else:
                print(f"  #{signal.id:3d} {signal.symbol:7s} {signal.side:4s} @ {signal.price:9.4f} | ⚠️  No validation")
            
        except Exception as e:
            print(f"❌ Error creating signal #{i+1}: {e}")
            continue
    
    print(f"\n✅ Created {created_count} signals")
    print(f"✅ Validated {validated_count} signals")
    print(f"\n📊 Total signals in database: {Signal.objects.count()}")
    print(f"📊 Signals for {user.email}: {Signal.objects.filter(user=user).count()}")
    print(f"\n🎯 Dashboard URL: http://127.0.0.1:8000/signals/dashboard/")

if __name__ == '__main__':
    main()
