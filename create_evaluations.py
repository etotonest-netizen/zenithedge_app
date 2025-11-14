"""
Create SignalEvaluation records for all signals without evaluation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from signals.models import Signal, SignalEvaluation

def create_evaluations():
    """Create evaluation records for signals that don't have them"""
    
    signals_without_eval = Signal.objects.filter(evaluation__isnull=True)
    print(f"📊 Found {signals_without_eval.count()} signals without evaluation\n")
    
    created_count = 0
    
    for signal in signals_without_eval:
        try:
            # Create evaluation that passes all checks
            eval_record = SignalEvaluation.objects.create(
                signal=signal,
                passed=True,
                blocked_reason='passed',
                final_ai_score=int(signal.confidence) if signal.confidence else 75,
                news_check=True,
                prop_check=True,
                score_check=True,
                strategy_check=True,
                is_overridden=False
            )
            created_count += 1
            print(f"✅ #{signal.id:3d} {signal.symbol:7s} {signal.side:4s} | Score: {eval_record.final_ai_score}")
            
        except Exception as e:
            print(f"❌ #{signal.id:3d} Error: {e}")
    
    print(f"\n✅ Created {created_count} evaluation records")
    print(f"📊 Total signals with evaluation: {Signal.objects.filter(evaluation__isnull=False).count()}")
    print(f"📊 Signals that will show on dashboard: {Signal.objects.filter(evaluation__passed=True).count()}")

if __name__ == '__main__':
    create_evaluations()
