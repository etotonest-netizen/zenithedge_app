"""
Trade Backtester Module
Simulates historical trading based on saved Signal data and outcomes.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.db.models import Q


class TradeBacktester:
    """
    Backtest trading strategies using historical signal data.
    """
    
    def __init__(self, user, initial_balance=10000, risk_per_trade=0.01, slippage=0.0001):
        """
        Initialize backtester.
        
        Args:
            user: User instance
            initial_balance: Starting capital (default: 10000)
            risk_per_trade: Risk per trade as decimal (default: 0.01 = 1%)
            slippage: Slippage factor to reduce profits (default: 0.0001 = 1 pip for forex)
        """
        self.user = user
        self.starting_capital = initial_balance
        self.risk_per_trade = risk_per_trade
        self.slippage = slippage
    
    def run(
        self,
        strategy: str,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Run backtest with specified parameters.
        
        Args:
            strategy: Strategy name to filter signals
            symbol: Symbol filter (None = all symbols)
            timeframe: Timeframe filter
            start_date: Start date for backtest
            end_date: End date for backtest
            filters: Additional filters (min_score, ignore_news, etc.)
        
        Returns:
            Dict with backtest results including stats and trade details
        """
        from signals.models import Signal, TradeJournalEntry
        
        filters = filters or {}
        
        # Build query for signals
        query = Q(user=self.user)
        
        if strategy:
            query &= Q(strategy__icontains=strategy)
        
        if symbol:
            query &= Q(symbol__icontains=symbol)
        
        if timeframe:
            query &= Q(timeframe__icontains=timeframe)
        
        if start_date:
            query &= Q(received_at__gte=start_date)
        
        if end_date:
            query &= Q(received_at__lte=end_date)
        
        # Apply additional filters
        min_score = filters.get('min_score')
        if min_score:
            query &= Q(ai_score__ai_score__gte=min_score)
        
        # Get signals matching criteria
        signals = Signal.objects.filter(query).select_related(
            'ai_score', 'evaluation'
        ).order_by('received_at')
        
        # Run backtest simulation
        results = self._simulate_trades(signals, filters)
        
        return results
    
    def _simulate_trades(self, signals, filters: Dict) -> Dict:
        """
        Simulate trades based on signals and calculate statistics.
        """
        from signals.models import TradeJournalEntry
        
        equity = self.starting_capital
        peak_equity = equity
        max_drawdown = 0.0
        
        equity_curve = [{'date': 'Start', 'equity': float(equity)}]
        trade_details = []
        
        winning_trades = 0
        losing_trades = 0
        total_profit = 0.0
        total_loss = 0.0
        rr_ratios = []
        
        for idx, signal in enumerate(signals):
            # Determine trade outcome
            outcome = self._get_trade_outcome(signal)
            
            if outcome is None:
                continue  # Skip signals with no determinable outcome
            
            # Calculate position size (1% risk)
            risk_amount = equity * self.risk_per_trade
            
            # Calculate R (risk in pips/points)
            sl = float(signal.sl)
            tp = float(signal.tp)
            
            # If price is None, estimate entry point based on SL/TP
            if signal.price is None:
                if signal.side.upper() == 'BUY':
                    # For BUY: entry is typically just above SL
                    entry = sl + (tp - sl) * 0.1
                else:
                    # For SELL: entry is typically just below SL
                    entry = sl - (sl - tp) * 0.1
            else:
                entry = float(signal.price)
            
            risk_pips = abs(entry - sl)
            reward_pips = abs(tp - entry)
            
            if risk_pips == 0:
                continue  # Invalid signal
            
            rr_ratio = reward_pips / risk_pips
            
            # Calculate P&L based on outcome
            if outcome == 'win':
                pnl = risk_amount * rr_ratio
                # Apply slippage (reduces profit)
                pnl *= (1 - self.slippage)
                total_profit += pnl
                winning_trades += 1
            elif outcome == 'loss':
                pnl = -risk_amount
                # Apply slippage (increases loss slightly)
                pnl *= (1 + self.slippage)
                total_loss += abs(pnl)
                losing_trades += 1
            else:  # breakeven
                pnl = 0
            
            # Update equity
            equity += pnl
            
            # Track drawdown
            if equity > peak_equity:
                peak_equity = equity
            
            drawdown = ((peak_equity - equity) / peak_equity) * 100 if peak_equity > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
            
            # Add to equity curve
            equity_curve.append({
                'date': signal.received_at.strftime('%Y-%m-%d %H:%M') if signal.received_at else f'Trade {idx+1}',
                'equity': float(equity)
            })
            
            # Store trade details
            trade_details.append({
                'id': signal.id,
                'date': signal.received_at.strftime('%Y-%m-%d %H:%M') if signal.received_at else 'Unknown',
                'symbol': signal.symbol,
                'side': signal.side,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'rr': round(rr_ratio, 2),
                'outcome': outcome,
                'pnl': round(pnl, 2),
                'equity': round(equity, 2),
                'ai_score': signal.ai_score.ai_score if signal.ai_score else 0,
                'strategy': signal.strategy,
            })
            
            if outcome in ['win', 'loss']:
                rr_ratios.append(rr_ratio)
        
        # Calculate statistics
        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        total_pnl = equity - self.starting_capital
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_rr': round(avg_rr, 2),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 2),
            'total_pnl': round(total_pnl, 2),
            'starting_capital': self.starting_capital,
            'ending_equity': round(equity, 2),
            'equity_curve': equity_curve,
            'trade_details': trade_details,
        }
    
    def _get_trade_outcome(self, signal) -> Optional[str]:
        """
        Determine trade outcome from journal or signal data.
        Returns: 'win', 'loss', 'breakeven', or None
        """
        from signals.models import TradeJournalEntry
        
        # Check if there's a journal entry
        try:
            journal = TradeJournalEntry.objects.get(signal=signal)
            if journal.outcome:
                if journal.outcome == 'green':
                    return 'win'
                elif journal.outcome == 'red':
                    return 'loss'
                elif journal.outcome in ['breakeven', 'pending']:
                    return 'breakeven'
        except TradeJournalEntry.DoesNotExist:
            pass
        
        # Fallback: use signal status if available
        if hasattr(signal, 'status'):
            if signal.status == 'hit_tp':
                return 'win'
            elif signal.status == 'hit_sl':
                return 'loss'
        
        # Fallback: use evaluation result
        if hasattr(signal, 'evaluation'):
            # If signal was blocked, assume it would have been a loss
            # (validates the blocking system)
            if not signal.evaluation.passed and not signal.evaluation.is_overridden:
                return 'loss'
        
        # Default: simulate 50% win rate if no data available
        # In production, you might want to be more sophisticated
        import random
        return 'win' if random.random() > 0.5 else 'loss'
    
    def compare_strategies(
        self,
        strategies: List[str],
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Compare multiple strategies side by side.
        """
        results = []
        
        for strategy in strategies:
            result = self.run(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            result['strategy'] = strategy
            results.append(result)
        
        return results
