"""
Process Signals Management Command

Cron-friendly command to process pending webhook signals without Celery/Redis.
Designed for shared hosting environments where background workers aren't available.

Usage:
    python manage.py process_signals [--limit=50] [--max-age=24]

Cron Setup (every 5 minutes):
    */5 * * * * cd /home/username/zenithedge_trading_hub && python manage.py process_signals >> logs/cron.log 2>&1

What it does:
1. Finds all signals with status='pending'
2. Runs AI validation and scoring
3. Checks prop rules and risk controls
4. Updates signal status to 'processed' or 'failed'
5. Logs all activity for monitoring

Options:
    --limit: Maximum number of signals to process per run (default: 50)
    --max-age: Maximum age in hours of signals to process (default: 24)
    --force: Process signals regardless of age
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from signals.models import Signal
import logging

logger = logging.getLogger('signals')


class Command(BaseCommand):
    help = 'Process pending webhook signals (cron-friendly, no Celery required)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of signals to process (default: 50)'
        )
        parser.add_argument(
            '--max-age',
            type=int,
            default=24,
            help='Maximum age of signals in hours (default: 24)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Process all pending signals regardless of age'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        max_age_hours = options['max_age']
        force = options['force']
        dry_run = options['dry-run']

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🔄 SIGNAL PROCESSING STARTED"))
        self.stdout.write(f"Timestamp: {timezone.now().isoformat()}")
        self.stdout.write(f"Limit: {limit} signals")
        self.stdout.write(f"Max Age: {max_age_hours} hours")
        self.stdout.write(f"Force Mode: {'Yes' if force else 'No'}")
        self.stdout.write(f"Dry Run: {'Yes' if dry_run else 'No'}")
        self.stdout.write("=" * 70)

        # Build query
        query = Signal.objects.filter(status='pending')

        if not force:
            # Only process recent signals
            cutoff = timezone.now() - timedelta(hours=max_age_hours)
            query = query.filter(received_at__gte=cutoff)

        # Get pending signals
        pending_signals = query.order_by('received_at')[:limit]
        count = pending_signals.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("✅ No pending signals to process"))
            return

        self.stdout.write(self.style.SUCCESS(f"\n📊 Found {count} pending signals to process\n"))

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made\n"))
            for signal in pending_signals:
                self.stdout.write(
                    f"  • Signal #{signal.id}: {signal.symbol} {signal.timeframe} {signal.side} "
                    f"(Confidence: {signal.confidence}%) - {signal.received_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            return

        # Process signals
        processed = 0
        failed = 0
        skipped = 0

        for signal in pending_signals:
            try:
                self.stdout.write(f"\n⚙️  Processing Signal #{signal.id}: {signal.symbol} {signal.timeframe} {signal.side}")
                
                # Mark as processing
                signal.status = 'processing'
                signal.save(update_fields=['status'])

                # Step 1: Validate prop rules (if user has prop rules configured)
                if signal.user and hasattr(signal.user, 'prop_challenges'):
                    try:
                        prop_challenge = signal.user.prop_challenges.filter(is_active=True).first()
                        if prop_challenge and prop_challenge.prop_rule:
                            self.stdout.write("  ├─ Checking prop rules...")
                            
                            # Import validation function
                            from signals.validation import validate_signal_against_prop_rules
                            
                            is_allowed, reason = validate_signal_against_prop_rules(
                                signal,
                                prop_challenge.prop_rule
                            )
                            
                            signal.is_allowed = is_allowed
                            signal.rejection_reason = reason if not is_allowed else ''
                            signal.prop_rule_checked = prop_challenge.prop_rule
                            
                            if is_allowed:
                                self.stdout.write(self.style.SUCCESS("  │  ✅ Prop rules: PASSED"))
                            else:
                                self.stdout.write(self.style.WARNING(f"  │  ⚠️  Prop rules: FAILED - {reason}"))
                    
                    except Exception as e:
                        logger.warning(f"Prop rule validation error for signal {signal.id}: {e}")
                        self.stdout.write(self.style.WARNING(f"  │  ⚠️  Prop rules: ERROR - {str(e)}"))

                # Step 2: Check risk controls (if user has risk controls configured)
                if signal.user and hasattr(signal.user, 'risk_controls'):
                    try:
                        risk_control = signal.user.risk_controls.filter(is_active=True).first()
                        if risk_control:
                            self.stdout.write("  ├─ Checking risk controls...")
                            
                            # Import risk control function
                            from signals.views import check_risk_control
                            
                            is_blocked, block_reason = check_risk_control(signal, risk_control)
                            
                            signal.is_risk_blocked = is_blocked
                            signal.risk_control_checked = risk_control
                            
                            if not is_blocked:
                                self.stdout.write(self.style.SUCCESS("  │  ✅ Risk controls: PASSED"))
                            else:
                                self.stdout.write(self.style.WARNING(f"  │  ⚠️  Risk controls: BLOCKED - {block_reason}"))
                    
                    except Exception as e:
                        logger.warning(f"Risk control validation error for signal {signal.id}: {e}")
                        self.stdout.write(self.style.WARNING(f"  │  ⚠️  Risk controls: ERROR - {str(e)}"))

                # Step 3: Run AI scoring (if bot/cognition modules are available)
                try:
                    self.stdout.write("  ├─ Running AI scoring...")
                    
                    # Check if bot AI modules are available
                    try:
                        from bot.ai_score import AITradeScorePredictor
                        
                        predictor = AITradeScorePredictor()
                        
                        # Create signal data dict for AI
                        signal_data = {
                            'symbol': signal.symbol,
                            'timeframe': signal.timeframe,
                            'side': signal.side,
                            'strategy': signal.strategy,
                            'regime': signal.regime,
                            'confidence': float(signal.confidence),
                        }
                        
                        # Get AI prediction
                        prediction = predictor.predict(signal_data)
                        
                        if prediction:
                            ai_score = prediction.get('predicted_score', 0)
                            self.stdout.write(self.style.SUCCESS(f"  │  ✅ AI Score: {ai_score:.1f}/100"))
                            
                            # Store AI score in raw_data
                            if not signal.raw_data:
                                signal.raw_data = {}
                            signal.raw_data['ai_score'] = ai_score
                            signal.raw_data['ai_prediction'] = prediction
                        else:
                            self.stdout.write(self.style.WARNING("  │  ⚠️  AI Score: Not available"))
                    
                    except ImportError:
                        self.stdout.write(self.style.WARNING("  │  ⚠️  AI modules not available (skipping)"))
                    
                except Exception as e:
                    logger.warning(f"AI scoring error for signal {signal.id}: {e}")
                    self.stdout.write(self.style.WARNING(f"  │  ⚠️  AI scoring: ERROR - {str(e)}"))

                # Mark as successfully processed
                signal.status = 'processed'
                signal.processed_at = timezone.now()
                signal.error_message = ''
                signal.save()

                processed += 1
                self.stdout.write(self.style.SUCCESS(f"  └─ ✅ Signal #{signal.id} processed successfully\n"))

            except Exception as e:
                # Mark as failed
                signal.status = 'failed'
                signal.error_message = str(e)
                signal.processed_at = timezone.now()
                signal.save()

                failed += 1
                logger.error(f"Failed to process signal {signal.id}: {e}", exc_info=True)
                self.stdout.write(self.style.ERROR(f"  └─ ❌ Signal #{signal.id} failed: {str(e)}\n"))

        # Summary
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("📊 PROCESSING COMPLETE"))
        self.stdout.write(f"✅ Processed: {processed}")
        self.stdout.write(f"❌ Failed: {failed}")
        self.stdout.write(f"⏭️  Skipped: {skipped}")
        self.stdout.write(f"📈 Total: {count}")
        self.stdout.write(f"⏱️  Duration: {(timezone.now() - timezone.now()).total_seconds():.2f}s")
        self.stdout.write("=" * 70)

        if failed > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠️  {failed} signals failed to process. Check logs for details."))
