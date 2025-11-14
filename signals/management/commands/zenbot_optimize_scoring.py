"""
Management command to optimize scoring weights based on recent performance.
Usage: python manage.py zenbot_optimize_scoring [options]
"""
from django.core.management.base import BaseCommand
from signals.models import ScoringWeights
from bot.score_engine import update_weights_from_journal
import datetime


class Command(BaseCommand):
    help = 'Optimize AI scoring weights based on recent trading performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--window-days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--learning-rate',
            type=float,
            default=0.1,
            help='Weight adjustment rate 0-1 (default: 0.1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show proposed changes without applying them'
        )
    
    def handle(self, *args, **options):
        window_days = options['window_days']
        learning_rate = options['learning_rate']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🔬 Analyzing last {window_days} days of trading performance..."
            )
        )
        
        # Run optimization
        result = update_weights_from_journal(
            window_days=window_days,
            learning_rate=learning_rate
        )
        
        if result['status'] == 'insufficient_data':
            self.stdout.write(
                self.style.WARNING(f"\n⚠️ {result['message']}")
            )
            self.stdout.write(
                "   Need more completed signals to optimize weights."
            )
            return
        
        if result['status'] == 'error':
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error: {result.get('message', 'Unknown error')}")
            )
            return
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Analysis complete: {result['analyzed_signals']} signals, "
                f"{result['win_rate']:.1%} win rate\n"
            )
        )
        
        self.stdout.write("📊 Factor Correlations:")
        for factor, corr in result['correlations'].items():
            arrow = "📈" if corr > 0 else "📉" if corr < 0 else "➡️"
            self.stdout.write(f"   {arrow} {factor}: {corr:+.4f}")
        
        self.stdout.write("\n⚖️ Proposed Weight Changes:")
        for key in result['new_weights']:
            old = result['old_weights'].get(key, 0)
            new = result['new_weights'][key]
            change = new - old
            arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            self.stdout.write(
                f"   {arrow} {key}: {old:.2%} → {new:.2%} ({change:+.2%})"
            )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n🔒 DRY RUN - No changes were saved')
            )
            return
        
        # Confirm before applying
        confirm = input("\n Apply these weights? [y/N]: ")
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING('Aborted'))
            return
        
        # Create new version
        new_version = f"v{datetime.datetime.now().strftime('%Y%m%d-%H%M')}"
        
        ScoringWeights.objects.create(
            version=new_version,
            weights=result['new_weights'],
            is_active=True,
            notes=(
                f"Auto-optimized from {result['analyzed_signals']} signals "
                f"with {result['win_rate']:.1%} win rate (window={window_days}d, lr={learning_rate})"
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ New weights activated: {new_version}"
            )
        )
        self.stdout.write(
            "   Future signals will be scored with the updated weights."
        )
        self.stdout.write(
            "   Run 'zenbot_recompute_scores --all' to rescore existing signals."
        )
