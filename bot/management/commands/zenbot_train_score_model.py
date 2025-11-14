"""
Management command to train/optimize ZenBot scoring weights based on historical performance.
Uses recent trade journal data to identify which factors correlate with successful trades.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta
from collections import defaultdict

from signals.models import Signal, TradeScore, ScoringWeights
import logging

logger = logging.getLogger('zenbot')


class Command(BaseCommand):
    help = 'Train and optimize ZenBot scoring weights based on historical trade outcomes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--window-days',
            type=int,
            default=30,
            help='Number of days of historical data to analyze (default: 30)'
        )
        parser.add_argument(
            '--min-trades',
            type=int,
            default=20,
            help='Minimum number of trades required for training (default: 20)'
        )
        parser.add_argument(
            '--learning-rate',
            type=float,
            default=0.1,
            help='Learning rate for weight adjustments (0.0-1.0, default: 0.1)'
        )
        parser.add_argument(
            '--version',
            type=str,
            help='Version name for new weights (e.g., "v2.0-optimized")'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving'
        )

    def handle(self, *args, **options):
        window_days = options['window_days']
        min_trades = options['min_trades']
        learning_rate = options['learning_rate']
        version_name = options.get('version')
        dry_run = options['dry_run']
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"ZenBot Scoring Weight Training")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Window: {window_days} days")
        self.stdout.write(f"Minimum trades: {min_trades}")
        self.stdout.write(f"Learning rate: {learning_rate}")
        self.stdout.write(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        self.stdout.write(f"{'='*60}\n")
        
        # Get cutoff date
        cutoff = timezone.now() - timedelta(days=window_days)
        
        # Get signals with outcomes and scores
        signals = Signal.objects.filter(
            received_at__gte=cutoff,
            ai_score__isnull=False
        ).exclude(outcome='pending').select_related('ai_score')
        
        total_signals = signals.count()
        
        if total_signals < min_trades:
            self.stdout.write(self.style.ERROR(
                f"✗ Insufficient data: {total_signals} trades found, need at least {min_trades}"
            ))
            return
        
        self.stdout.write(f"✓ Found {total_signals} completed trades with AI scores\n")
        
        # Separate wins and losses
        winning_signals = signals.filter(outcome='win')
        losing_signals = signals.filter(outcome='loss')
        
        win_count = winning_signals.count()
        loss_count = losing_signals.count()
        
        if win_count == 0 or loss_count == 0:
            self.stdout.write(self.style.ERROR(
                "✗ Need both winning and losing trades to train"
            ))
            return
        
        win_rate = (win_count / total_signals) * 100
        self.stdout.write(f"Win Rate: {win_rate:.1f}% ({win_count}W / {loss_count}L)\n")
        
        # Analyze factor correlations
        self.stdout.write("Analyzing factor correlations...\n")
        
        factor_stats = self.analyze_factors(winning_signals, losing_signals)
        
        # Display factor analysis
        self.stdout.write(f"\n{'Factor':<25} {'Wins Avg':<12} {'Losses Avg':<12} {'Correlation':<12}")
        self.stdout.write(f"{'-'*65}")
        
        for factor, stats in factor_stats.items():
            corr_indicator = "📈" if stats['correlation'] > 0.05 else "📉" if stats['correlation'] < -0.05 else "➡️"
            self.stdout.write(
                f"{factor:<25} {stats['avg_win']:<12.3f} {stats['avg_loss']:<12.3f} "
                f"{corr_indicator} {stats['correlation']:+.3f}"
            )
        
        # Get current weights
        current_weights_obj = ScoringWeights.get_active_weights()
        current_weights = current_weights_obj.weights.copy()
        
        self.stdout.write(f"\n\nCurrent Weights (v{current_weights_obj.version}):")
        for key, value in current_weights.items():
            self.stdout.write(f"  {key:<25} {value:.3f}")
        
        # Calculate new weights
        new_weights = self.optimize_weights(
            current_weights, 
            factor_stats, 
            learning_rate
        )
        
        self.stdout.write(f"\n\nProposed New Weights:")
        for key, value in new_weights.items():
            old_val = current_weights.get(key, 0)
            change = value - old_val
            change_str = f"({change:+.3f})" if abs(change) > 0.001 else ""
            
            if abs(change) > 0.05:
                color = self.style.SUCCESS if change > 0 else self.style.WARNING
            else:
                color = lambda x: x
            
            self.stdout.write(color(f"  {key:<25} {value:.3f} {change_str}"))
        
        # Calculate expected improvement
        expected_improvement = self.estimate_improvement(factor_stats, current_weights, new_weights)
        self.stdout.write(f"\nEstimated Performance Improvement: {expected_improvement:+.1f}%")
        
        # Save new weights if not dry run
        if not dry_run:
            if not version_name:
                # Auto-generate version name
                version_num = float(current_weights_obj.version.replace('v', '').split('-')[0]) + 0.1
                version_name = f"v{version_num:.1f}-trained"
            
            new_weights_obj = ScoringWeights.objects.create(
                version=version_name,
                weights=new_weights,
                min_score_threshold=current_weights_obj.min_score_threshold,
                is_active=False,  # Don't auto-activate
                notes=f"Trained on {total_signals} trades from last {window_days} days. "
                      f"Win rate: {win_rate:.1f}%. Learning rate: {learning_rate}"
            )
            
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ New weights saved as version '{version_name}'"
            ))
            self.stdout.write(
                f"  To activate: Update ScoringWeights id={new_weights_obj.id} is_active=True"
            )
            self.stdout.write(
                f"  Or run: python manage.py shell"
            )
            self.stdout.write(
                f"  >>> from signals.models import ScoringWeights"
            )
            self.stdout.write(
                f"  >>> ScoringWeights.objects.get(id={new_weights_obj.id}).is_active = True"
            )
            self.stdout.write(
                f"  >>> ScoringWeights.objects.get(id={new_weights_obj.id}).save()"
            )
            
            logger.info(f"ZenBot weights trained: {version_name} | Win rate: {win_rate:.1f}%")
        else:
            self.stdout.write(self.style.WARNING(
                f"\n⚠ DRY RUN - No changes saved"
            ))
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("Training complete!")
        self.stdout.write(f"{'='*60}\n")

    def analyze_factors(self, winning_signals, losing_signals):
        """
        Analyze correlation between factors and outcomes.
        Returns dict with statistics for each factor.
        """
        factor_stats = {}
        
        # Map database fields to weight keys
        factor_mapping = {
            'confidence_factor': 'signal_confidence',
            'atr_safety_factor': 'atr_safety',
            'strategy_bias_factor': 'strategy_bias',
            'regime_fit_factor': 'regime_fit',
            'rolling_win_rate': 'rolling_win_rate',
        }
        
        for db_field, weight_key in factor_mapping.items():
            # Calculate averages for wins and losses
            wins_data = winning_signals.values_list(f'ai_score__{db_field}', flat=True)
            losses_data = losing_signals.values_list(f'ai_score__{db_field}', flat=True)
            
            avg_win = sum(wins_data) / len(wins_data) if wins_data else 0
            avg_loss = sum(losses_data) / len(losses_data) if losses_data else 0
            
            # Correlation: positive means factor predicts wins
            correlation = avg_win - avg_loss
            
            factor_stats[weight_key] = {
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'correlation': correlation
            }
        
        return factor_stats

    def optimize_weights(self, current_weights, factor_stats, learning_rate):
        """
        Adjust weights based on factor correlations.
        Increase weights for factors that correlate with wins.
        """
        new_weights = current_weights.copy()
        
        for factor, stats in factor_stats.items():
            if factor in new_weights:
                # Adjust weight based on correlation
                adjustment = stats['correlation'] * learning_rate
                new_weights[factor] = max(0.05, min(0.50, 
                    new_weights[factor] + adjustment
                ))
        
        # Normalize to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: v/total for k, v in new_weights.items()}
        
        return new_weights

    def estimate_improvement(self, factor_stats, old_weights, new_weights):
        """
        Estimate expected performance improvement based on correlation strength.
        """
        improvement = 0.0
        
        for factor, stats in factor_stats.items():
            if factor in old_weights and factor in new_weights:
                weight_change = new_weights[factor] - old_weights[factor]
                # Positive correlation + increased weight = improvement
                improvement += weight_change * stats['correlation'] * 100
        
        return improvement
