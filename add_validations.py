"""
Add AI validations with news context to existing signals
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from signals.models import Signal, TradeValidation
from zennews.models import NewsEvent
from zenbot.validation_engine import validate_signal
from zenbot.contextualizer_v2 import generate_narrative

def add_validation_to_signal(signal):
    """Add validation to a signal that doesn't have one"""
    
    # Skip if already has validation
    if hasattr(signal, 'validation') and signal.validation:
        return None
    
    # Prepare signal data
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
    
    try:
        # Run AI validation
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
        
        # Fetch recent news
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
        except:
            pass
        
        # Add news_context to quality_metrics
        if news_context:
            quality_metrics['news_context'] = news_context
        
        # Create validation
        validation = TradeValidation.objects.create(
            signal=signal,
            truth_index=truth_index,
            status=validation_status,
            breakdown=validation_result.get('breakdown', {}),
            validation_notes=validation_result.get('validation_notes', []),
            context_summary=context_narrative[:500] if len(context_narrative) > 500 else context_narrative,
            recommendation=validation_result.get('recommendation', ''),
            accuracy_history={},
            quality_metrics=quality_metrics,
            kb_concepts_used=kb_concepts_used
        )
        
        return validation
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    print("🔄 Adding validations to existing signals...\n")
    
    # Get signals without validation
    all_signals = Signal.objects.all().order_by('-id')[:60]
    signals_needing_validation = [s for s in all_signals if not (hasattr(s, 'validation') and s.validation)]
    
    print(f"Found {len(signals_needing_validation)} signals without validation\n")
    
    validated_count = 0
    
    for signal in signals_needing_validation:
        validation = add_validation_to_signal(signal)
        
        if validation:
            validated_count += 1
            news_indicator = "📰" if 'news_context' in validation.quality_metrics else "  "
            print(f"{news_indicator} #{signal.id:3d} {signal.symbol:7s} {signal.side:4s} | "
                  f"Truth: {validation.truth_index:5.1f} | KB: {validation.kb_concepts_used:2d} concepts")
        else:
            print(f"  #{signal.id:3d} {signal.symbol:7s} {signal.side:4s} | ⚠️  Failed")
    
    print(f"\n✅ Successfully validated {validated_count} signals")
    print(f"📊 Total validated signals: {TradeValidation.objects.count()}")

if __name__ == '__main__':
    main()
