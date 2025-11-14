"""
Management command to aggregate daily performance statistics
Run this as a daily cron job or Celery task
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta
from decimal import Decimal

from accounts.models import CustomUser
from signals.models import Signal, TradeJournalEntry
from analytics.models import DailyPerformanceCache


class Command(BaseCommand):
    help = 'Aggregate daily performance statistics for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to aggregate (YYYY-MM-DD), defaults to yesterday'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username/email to aggregate (optional, processes all users if not specified)'
        )

    def handle(self, *args, **options):
        # Determine target date
        if options['date']:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            # Default to yesterday
            target_date = (timezone.now() - timedelta(days=1)).date()
        
        self.stdout.write(f"Aggregating performance for date: {target_date}")
        
        # Determine which users to process
        if options['user']:
            users = CustomUser.objects.filter(email=options['user'])
            if not users.exists():
                self.stdout.write(self.style.ERROR(f"User {options['user']} not found"))
                return
        else:
            users = CustomUser.objects.filter(is_active=True)
        
        processed_count = 0
        for user in users:
            try:
                self.aggregate_user_performance(user, target_date)
                processed_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Processed {user.email}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error processing {user.email}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nCompleted: {processed_count}/{users.count()} users processed"))

    def aggregate_user_performance(self, user, target_date):
        """Aggregate performance for a single user on a specific date"""
        
        # Date range for the target date (00:00:00 to 23:59:59)
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Make timezone aware
        start_datetime = timezone.make_aware(start_datetime)
        end_datetime = timezone.make_aware(end_datetime)
        
        # Get all signals for this user on this date
        signals = Signal.objects.filter(
            user=user,
            received_at__gte=start_datetime,
            received_at__lte=end_datetime
        )
        
        # Count signals
        total_signals = signals.count()
        allowed_signals = signals.filter(is_allowed=True).count()
        rejected_signals = signals.filter(is_allowed=False).count()
        
        # Count outcomes
        win_count = signals.filter(outcome='win').count()
        loss_count = signals.filter(outcome='loss').count()
        breakeven_count = signals.filter(outcome='breakeven').count()
        
        # Get journal entries for pips calculation
        journal_entries = TradeJournalEntry.objects.filter(
            user=user,
            created_at__gte=start_datetime,
            created_at__lte=end_datetime,
            pips__isnull=False
        )
        
        total_pips = journal_entries.aggregate(Sum('pips'))['pips__sum'] or Decimal('0.00')
        
        # Calculate average AI score
        signals_with_score = signals.filter(ai_score__isnull=False)
        if signals_with_score.exists():
            avg_ai_score = signals_with_score.aggregate(
                Avg('ai_score__ai_score')
            )['ai_score__ai_score__avg'] or 0.0
        else:
            avg_ai_score = 0.0
        
        # Find best strategy (most wins)
        strategy_wins = signals.filter(outcome='win').values('strategy').annotate(
            count=Count('id')
        ).order_by('-count').first()
        best_strategy = strategy_wins['strategy'] if strategy_wins else ''
        
        # Find best session
        session_wins = signals.filter(outcome='win').values('session').annotate(
            count=Count('id')
        ).order_by('-count').first()
        best_session = session_wins['session'] if session_wins else ''
        
        # Create or update cache entry
        cache_entry, created = DailyPerformanceCache.objects.update_or_create(
            user=user,
            date=target_date,
            defaults={
                'total_signals': total_signals,
                'allowed_signals': allowed_signals,
                'rejected_signals': rejected_signals,
                'win_count': win_count,
                'loss_count': loss_count,
                'breakeven_count': breakeven_count,
                'total_pips': total_pips,
                'avg_ai_score': avg_ai_score,
                'best_strategy': best_strategy,
                'best_session': best_session,
            }
        )
        
        action = "Created" if created else "Updated"
        self.stdout.write(
            f"  {action} cache: {total_signals} signals, "
            f"{win_count}W/{loss_count}L, "
            f"{total_pips} pips"
        )
