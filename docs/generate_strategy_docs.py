#!/usr/bin/env python3
"""
Strategy Documentation Generator

Automatically generates comprehensive markdown documentation for each trading strategy
based on historical performance data.

Usage:
    python docs/generate_strategy_docs.py

Output:
    Creates individual markdown files in docs/strategies/ for each strategy
"""

import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from signals.models import Signal, TradeJournalEntry


def generate_strategy_doc(strategy_name):
    """Generate documentation for a specific strategy"""
    
    # Get all signals for this strategy
    signals = Signal.objects.filter(strategy=strategy_name)
    total_signals = signals.count()
    
    if total_signals == 0:
        return None
    
    # Calculate win rate from journal entries
    journal_entries = TradeJournalEntry.objects.filter(strategy=strategy_name, outcome__isnull=False)
    total_trades = journal_entries.count()
    wins = journal_entries.filter(outcome='win').count()
    losses = journal_entries.filter(outcome='loss').count()
    breakevens = journal_entries.filter(outcome='breakeven').count()
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # Calculate total pips
    total_pips = journal_entries.aggregate(Sum('pips_result'))['pips_result__sum'] or Decimal('0')
    
    # Calculate average AI score
    avg_ai_score = signals.filter(ai_score__isnull=False).aggregate(
        Avg('ai_score__ai_score')
    )['ai_score__ai_score__avg'] or 0
    
    # Best timeframes
    timeframe_stats = signals.values('timeframe').annotate(
        count=Count('id')
    ).order_by('-count')[:3]
    
    # Best sessions
    session_stats = journal_entries.filter(outcome='win').values('session').annotate(
        count=Count('id')
    ).order_by('-count')[:3]
    
    # Best regimes
    regime_stats = journal_entries.filter(outcome='win').values('regime').annotate(
        count=Count('id')
    ).order_by('-count')[:3]
    
    # Sample winning trades
    sample_wins = journal_entries.filter(outcome='win').order_by('-pips_result')[:3]
    
    # Performance by symbol
    symbol_performance = journal_entries.values('symbol').annotate(
        total_trades=Count('id'),
        wins=Count('id', filter=Q(outcome='win')),
        total_pips=Sum('pips_result')
    ).order_by('-total_pips')[:5]
    
    # Generate markdown content
    doc = f"""# {strategy_name} Strategy

## Overview
- **Total Signals Generated**: {total_signals}
- **Total Trades Executed**: {total_trades}
- **Win Rate**: {win_rate:.1f}%
- **Total Pips**: {total_pips:+.1f}
- **Average AI Score**: {avg_ai_score:.1f}/100

## Performance Summary

### Win/Loss Breakdown
- ✅ **Wins**: {wins} ({wins/total_trades*100:.1f}% if total_trades > 0 else 0)
- ❌ **Losses**: {losses} ({losses/total_trades*100:.1f}% if total_trades > 0 else 0)
- ⏸️ **Breakevens**: {breakevens} ({breakevens/total_trades*100:.1f}% if total_trades > 0 else 0)

### Best Timeframes
"""
    
    for i, tf in enumerate(timeframe_stats, 1):
        doc += f"{i}. **{tf['timeframe']}** - {tf['count']} signals\n"
    
    doc += "\n### Best Trading Sessions\n"
    for i, session in enumerate(session_stats, 1):
        doc += f"{i}. **{session['session']}** - {session['count']} wins\n"
    
    doc += "\n### Best Market Regimes\n"
    for i, regime in enumerate(regime_stats, 1):
        doc += f"{i}. **{regime['regime']}** - {regime['count']} wins\n"
    
    doc += "\n## Top Performing Symbols\n\n"
    doc += "| Symbol | Trades | Wins | Win Rate | Total Pips |\n"
    doc += "|--------|--------|------|----------|------------|\n"
    
    for sym in symbol_performance:
        sym_win_rate = (sym['wins'] / sym['total_trades'] * 100) if sym['total_trades'] > 0 else 0
        doc += f"| {sym['symbol']} | {sym['total_trades']} | {sym['wins']} | {sym_win_rate:.1f}% | {sym['total_pips']:+.1f} |\n"
    
    doc += "\n## Sample Winning Trades\n\n"
    
    for i, trade in enumerate(sample_wins, 1):
        doc += f"""### Trade #{i}
- **Symbol**: {trade.symbol}
- **Side**: {trade.side.upper()}
- **Timeframe**: {trade.timeframe}
- **Session**: {trade.session}
- **Regime**: {trade.regime}
- **Pips**: {trade.pips_result:+.1f}
- **Decision**: {trade.decision}
- **Notes**: {trade.notes or 'N/A'}

"""
    
    doc += f"""## Strategy Insights

### Strengths
- Performs best during **{session_stats[0]['session']}** session
- Most effective in **{regime_stats[0]['regime']}** market conditions
- Highest signal count on **{timeframe_stats[0]['timeframe']}** timeframe

### Risk Considerations
- Always use proper risk management (1-2% per trade)
- Avoid trading during low liquidity periods
- Monitor prop challenge limits when using this strategy

### Recommended Setup
1. Use on **{timeframe_stats[0]['timeframe']}** or **{timeframe_stats[1]['timeframe'] if len(timeframe_stats) > 1 else timeframe_stats[0]['timeframe']}** timeframes
2. Trade during **{session_stats[0]['session']}** session for best results
3. Focus on **{regime_stats[0]['regime']}** market regime
4. Set minimum AI score threshold: **{avg_ai_score:.0f}+**

---
*Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*
*Data based on {total_trades} executed trades*
"""
    
    return doc


def main():
    """Main execution function"""
    print("🚀 ZenithEdge Strategy Documentation Generator")
    print("=" * 60)
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'strategies')
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all unique strategies
    strategies = Signal.objects.values_list('strategy', flat=True).distinct()
    
    print(f"\n📊 Found {len(strategies)} strategies\n")
    
    generated_count = 0
    
    for strategy in strategies:
        print(f"Processing: {strategy}...", end=" ")
        
        doc_content = generate_strategy_doc(strategy)
        
        if doc_content:
            # Save to file
            filename = f"{strategy.replace(' ', '_').lower()}.md"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            print(f"✅ Generated: {filename}")
            generated_count += 1
        else:
            print("⚠️ No data available")
    
    print(f"\n{'=' * 60}")
    print(f"✨ Successfully generated {generated_count} strategy documents")
    print(f"📁 Output directory: {output_dir}")
    print(f"\nUsage: Review generated docs to optimize your trading strategy selection!")


if __name__ == '__main__':
    main()
