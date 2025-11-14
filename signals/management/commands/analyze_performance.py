"""
Django management command to analyze strategy performance

This command simulates trade outcomes by analyzing past signals and calculating
performance metrics including win rate, risk-reward ratios, drawdown, and profitability.

Usage:
    python manage.py analyze_performance
    python manage.py analyze_performance --days 30
    python manage.py analyze_performance --strategy ZenithEdge
    python manage.py analyze_performance --user admin@zenithedge.com
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from decimal import Decimal
import random

from signals.models import Signal, StrategyPerformance
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Analyze strategy performance by simulating TP/SL outcomes from past signals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--strategy',
            type=str,
            help='Filter by specific strategy name'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by user email'
        )
        parser.add_argument(
            '--regime',
            type=str,
            choices=['Trend', 'Breakout', 'MeanReversion', 'Squeeze'],
            help='Filter by specific regime'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            help='Filter by specific symbol'
        )
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Use simulated outcomes (for demo/testing)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing performance records before analysis'
        )

    def handle(self, *args, **options):
        days = options['days']
        strategy_filter = options.get('strategy')
        user_email = options.get('user')
        regime_filter = options.get('regime')
        symbol_filter = options.get('symbol')
        simulate = options.get('simulate', False)
        clear = options.get('clear', False)

        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('  ZenithEdge Strategy Performance Analyzer'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('')

        # Clear existing records if requested
        if clear:
            count = StrategyPerformance.objects.all().count()
            StrategyPerformance.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing performance records'))
            self.stdout.write('')

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write(f'Analysis Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}')
        self.stdout.write(f'Days: {days}')
        self.stdout.write('')

        # Build query
        query = Q(received_at__gte=start_date) & Q(received_at__lte=end_date)
        
        if strategy_filter:
            query &= Q(strategy=strategy_filter)
        
        if user_email:
            try:
                user = CustomUser.objects.get(email=user_email)
                query &= Q(user=user)
            except CustomUser.DoesNotExist:
                raise CommandError(f'User with email "{user_email}" does not exist')
        
        if regime_filter:
            query &= Q(regime=regime_filter)
        
        if symbol_filter:
            query &= Q(symbol=symbol_filter)

        # Get signals
        signals = Signal.objects.filter(query).order_by('received_at')
        total_signals = signals.count()

        if total_signals == 0:
            self.stdout.write(self.style.WARNING('No signals found for the specified criteria'))
            return

        self.stdout.write(f'Found {total_signals} signals to analyze')
        self.stdout.write('')

        # Group signals by strategy characteristics
        strategy_groups = {}
        
        for signal in signals:
            # Create multiple grouping keys for different analysis levels
            keys = [
                # Overall strategy
                (signal.strategy, None, None, None),
                # Strategy + Regime
                (signal.strategy, signal.regime, None, None),
                # Strategy + Symbol
                (signal.strategy, None, signal.symbol, None),
                # Strategy + Timeframe
                (signal.strategy, None, None, signal.timeframe),
                # Strategy + Regime + Symbol
                (signal.strategy, signal.regime, signal.symbol, None),
                # Full granularity
                (signal.strategy, signal.regime, signal.symbol, signal.timeframe),
            ]
            
            for key in keys:
                if key not in strategy_groups:
                    strategy_groups[key] = []
                strategy_groups[key].append(signal)

        self.stdout.write(f'Created {len(strategy_groups)} performance groups')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Analyzing performance...'))
        self.stdout.write('')

        # Analyze each group
        created_count = 0
        updated_count = 0

        for key, group_signals in strategy_groups.items():
            strategy_name, regime, symbol, timeframe = key
            
            if len(group_signals) < 3:  # Skip groups with too few trades
                continue

            # Calculate performance metrics
            metrics = self._calculate_performance(group_signals, simulate)
            
            # Get or create performance record
            perf, created = StrategyPerformance.objects.get_or_create(
                strategy_name=strategy_name,
                regime=regime,
                symbol=symbol,
                timeframe=timeframe,
                user=group_signals[0].user,
                defaults={
                    'analysis_period_start': start_date,
                    'analysis_period_end': end_date,
                }
            )

            # Update metrics
            perf.total_trades = metrics['total_trades']
            perf.winning_trades = metrics['winning_trades']
            perf.losing_trades = metrics['losing_trades']
            perf.win_rate = metrics['win_rate']
            perf.avg_rr = metrics['avg_rr']
            perf.total_rr = metrics['total_rr']
            perf.max_drawdown = metrics['max_drawdown']
            perf.current_drawdown = metrics['current_drawdown']
            perf.total_pnl = metrics['total_pnl']
            perf.avg_win = metrics['avg_win']
            perf.avg_loss = metrics['avg_loss']
            perf.profit_factor = metrics['profit_factor']
            perf.avg_confidence = metrics['avg_confidence']
            perf.analysis_period_start = start_date
            perf.analysis_period_end = end_date
            perf.save()

            if created:
                created_count += 1
            else:
                updated_count += 1

            # Display progress
            group_name = self._format_group_name(strategy_name, regime, symbol, timeframe)
            status_icon = '✅' if perf.is_profitable else '⚠️'
            self.stdout.write(
                f'{status_icon} {group_name}: '
                f'{metrics["total_trades"]} trades, '
                f'WR: {metrics["win_rate"]:.1f}%, '
                f'RR: {metrics["avg_rr"]:.2f}, '
                f'PnL: {metrics["total_pnl"]}'
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Analysis Complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Created: {created_count} new performance records')
        self.stdout.write(f'Updated: {updated_count} existing performance records')
        self.stdout.write('')

        # Show top performers
        self._show_top_performers()

    def _calculate_performance(self, signals, simulate=False):
        """Calculate performance metrics for a group of signals"""
        total_trades = len(signals)
        winning_trades = 0
        losing_trades = 0
        total_rr = 0.0
        total_pnl = Decimal('0')
        total_wins_pnl = Decimal('0')
        total_losses_pnl = Decimal('0')
        max_equity = Decimal('10000')  # Starting equity
        current_equity = Decimal('10000')
        max_drawdown = 0.0
        current_drawdown = 0.0
        total_confidence = 0.0
        rr_values = []

        for signal in signals:
            # Simulate or calculate actual outcome
            if simulate or not hasattr(signal, 'actual_outcome'):
                # Simulate outcome based on confidence
                # Higher confidence = higher win probability
                win_probability = signal.confidence / 100.0
                # Add some realism - even high confidence trades can lose
                win_probability = min(win_probability * 0.85, 0.90)
                is_win = random.random() < win_probability
            else:
                # Use actual outcome if available (future enhancement)
                is_win = signal.actual_outcome == 'win'

            # Calculate risk and reward
            entry = float(signal.price) if signal.price else 0
            sl = float(signal.sl)
            tp = float(signal.tp)

            if entry == 0 or sl == 0 or tp == 0:
                continue

            # Calculate R values
            if signal.side == 'buy':
                risk = abs(entry - sl)
                reward = abs(tp - entry)
            else:  # sell
                risk = abs(sl - entry)
                reward = abs(entry - tp)

            if risk == 0:
                continue

            rr_ratio = reward / risk

            # Assume 1% risk per trade
            risk_amount = current_equity * Decimal('0.01')

            if is_win:
                winning_trades += 1
                pnl = risk_amount * Decimal(str(rr_ratio))
                total_wins_pnl += pnl
                total_rr += rr_ratio
                rr_values.append(rr_ratio)
            else:
                losing_trades += 1
                pnl = -risk_amount
                total_losses_pnl += abs(pnl)
                total_rr -= 1.0
                rr_values.append(-1.0)

            total_pnl += pnl
            current_equity += pnl

            # Track drawdown
            if current_equity > max_equity:
                max_equity = current_equity
                current_drawdown = 0.0
            else:
                current_drawdown = float((max_equity - current_equity) / max_equity * 100)
                max_drawdown = max(max_drawdown, current_drawdown)

            total_confidence += signal.confidence

        # Calculate averages
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0
        avg_win = total_wins_pnl / winning_trades if winning_trades > 0 else Decimal('0')
        avg_loss = total_losses_pnl / losing_trades if losing_trades > 0 else Decimal('0')
        profit_factor = float(total_wins_pnl / total_losses_pnl) if total_losses_pnl > 0 else 0.0
        avg_confidence = total_confidence / total_trades if total_trades > 0 else 0.0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_rr': avg_rr,
            'total_rr': total_rr,
            'max_drawdown': max_drawdown,
            'current_drawdown': current_drawdown,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_confidence': avg_confidence,
        }

    def _format_group_name(self, strategy, regime, symbol, timeframe):
        """Format a readable name for the performance group"""
        parts = [strategy]
        if regime:
            parts.append(regime)
        if symbol:
            parts.append(symbol)
        if timeframe:
            parts.append(timeframe)
        return ' / '.join(parts)

    def _show_top_performers(self):
        """Display top performing strategies"""
        top_strategies = StrategyPerformance.objects.filter(
            total_trades__gte=5
        ).order_by('-win_rate')[:5]

        if top_strategies.exists():
            self.stdout.write(self.style.SUCCESS('🏆 Top 5 Performers (by Win Rate):'))
            for i, perf in enumerate(top_strategies, 1):
                self.stdout.write(
                    f'{i}. {perf.strategy_name} '
                    f'({perf.regime or "All"}) - '
                    f'WR: {perf.win_rate:.1f}%, '
                    f'RR: {perf.avg_rr:.2f}, '
                    f'Trades: {perf.total_trades}'
                )
            self.stdout.write('')
