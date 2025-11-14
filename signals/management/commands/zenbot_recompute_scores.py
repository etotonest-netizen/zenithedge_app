"""
Management command to recompute AI scores for existing signals.
Usage: python manage.py zenbot_recompute_scores [options]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from signals.models import Signal, ScoringWeights
from bot.score_engine import bulk_rescore_signals


class Command(BaseCommand):
    help = 'Recompute AI scores for trading signals'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Rescore all signals (default: only unscored signals)'
        )
        parser.add_argument(
            '--since-date',
            type=str,
            help='Rescore signals since date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--min-id',
            type=int,
            help='Rescore signals with ID >= this value'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be rescored without actually doing it'
        )
    
    def handle(self, *args, **options):
        # Build queryset
        queryset = Signal.objects.all()
        
        if not options['all']:
            # Default: only unscored signals
            queryset = queryset.filter(ai_score__isnull=True)
        
        if options['since_date']:
            try:
                from datetime import datetime
                since_date = datetime.strptime(options['since_date'], '%Y-%m-%d')
                queryset = queryset.filter(received_at__gte=since_date)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        
        if options['min_id']:
            queryset = queryset.filter(id__gte=options['min_id'])
        
        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('No signals match the criteria.'))
            return
        
        # Show what will be rescored
        self.stdout.write(f"\nFound {total_count} signals to rescore")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes will be made\n'))
            for signal in queryset[:10]:
                self.stdout.write(f"  - Signal #{signal.id}: {signal.symbol} {signal.strategy}")
            if total_count > 10:
                self.stdout.write(f"  ... and {total_count - 10} more")
            return
        
        # Confirm before proceeding
        if not options['all']:
            confirm = input(f"\nProceed with rescoring {total_count} signals? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Aborted'))
                return
        
        # Get active weights
        weights_obj = ScoringWeights.get_active_weights()
        self.stdout.write(
            self.style.SUCCESS(f"\nUsing weights: {weights_obj.version}")
        )
        
        # Rescore signals
        self.stdout.write(self.style.SUCCESS('\nRescoring signals...'))
        
        result = bulk_rescore_signals(queryset)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully rescored {result['scored']}/{result['total']} signals"
            )
        )
        self.stdout.write(f"   Version: {result['version']}")
