"""
Engine Backtesting Module
==========================
Replay-based backtesting for strategy validation.

Features:
- Replay mode: Step-by-step bar simulation
- Batch mode: Fast historical run
- Variable SL/TP, position sizing, commission
- Comprehensive metrics (P&L, drawdown, win rate, Sharpe, etc.)
- Trade-by-trade recording
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtesting engine for strategy validation.
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        risk_per_trade_pct: float = 1.0,
        commission_pct: float = 0.0,
        slippage_pips: float = 0.0,
        use_trailing_sl: bool = False,
        trailing_sl_pips: float = 0.0,
    ):
        """
        Initialize backtester.
        
        Args:
            initial_balance: Starting equity
            risk_per_trade_pct: Risk percentage per trade (1.0 = 1%)
            commission_pct: Commission as % of trade value
            slippage_pips: Slippage in pips per trade
            use_trailing_sl: Whether to use trailing stop loss
            trailing_sl_pips: Trailing stop distance in pips
        """
        self.initial_balance = initial_balance
        self.risk_per_trade_pct = risk_per_trade_pct
        self.commission_pct = commission_pct
        self.slippage_pips = slippage_pips
        self.use_trailing_sl = use_trailing_sl
        self.trailing_sl_pips = trailing_sl_pips
        
        # State tracking
        self.balance = initial_balance
        self.equity = initial_balance
        self.peak_equity = initial_balance
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        
        # Trade tracking
        self.trades = []
        self.open_position = None
        self.equity_curve = []
        
        logger.info(f"Initialized backtester: ${initial_balance} balance, "
                   f"{risk_per_trade_pct}% risk per trade")
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        strategy_detector,
        strategy_name: str,
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            df: DataFrame with OHLCV data (indexed by timestamp)
            symbol: Trading symbol
            timeframe: Timeframe string
            strategy_detector: Strategy detector instance
            strategy_name: Name of strategy
            
        Returns:
            Dict with backtest results
        """
        start_time = datetime.now()
        
        logger.info(f"Starting backtest: {strategy_name} on {symbol} {timeframe} "
                   f"({len(df)} bars)")
        
        # Reset state
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self.peak_equity = self.initial_balance
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.trades = []
        self.open_position = None
        self.equity_curve = []
        
        # Iterate through bars
        for i in range(100, len(df)):  # Start at bar 100 for indicator warmup
            current_bar = df.iloc[i]
            timestamp = df.index[i]
            
            # Get historical window for detection
            hist_window = df.iloc[:i+1]
            
            # Check for open position exit first
            if self.open_position:
                self._check_exit(current_bar, timestamp, symbol)
            
            # If no open position, check for new signals
            if not self.open_position:
                signals = strategy_detector.detect(hist_window, symbol, timeframe)
                
                if signals:
                    # Take the first signal (most recent)
                    signal = signals[0]
                    self._enter_trade(signal, current_bar, timestamp, symbol)
            
            # Update equity curve
            self.equity_curve.append({
                'timestamp': timestamp,
                'balance': self.balance,
                'equity': self.equity,
                'drawdown': self.current_drawdown,
            })
        
        # Close any remaining open position
        if self.open_position:
            self._force_close_position(df.iloc[-1], df.index[-1], symbol)
        
        # Calculate metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        metrics = self._calculate_metrics()
        
        logger.info(f"Backtest complete: {len(self.trades)} trades, "
                   f"{metrics['win_rate']:.1f}% win rate, "
                   f"${metrics['net_profit']:.2f} profit")
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'strategy': strategy_name,
            'start_date': df.index[0].date(),
            'end_date': df.index[-1].date(),
            'bars_processed': len(df),
            'execution_time_sec': execution_time,
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'metrics': metrics,
        }
    
    def _enter_trade(
        self,
        signal,
        current_bar: pd.Series,
        timestamp,
        symbol: str
    ):
        """Enter a new trade based on signal."""
        try:
            side = signal.side
            entry_price = signal.price
            sl_price = signal.sl
            tp_price = signal.tp
            
            # Calculate position size based on risk
            risk_amount = self.balance * (self.risk_per_trade_pct / 100.0)
            sl_distance = abs(entry_price - sl_price)
            
            if sl_distance == 0:
                logger.warning("SL distance is zero, skipping trade")
                return
            
            # Position size = Risk Amount / SL Distance
            # For forex, use standard lot calculation
            position_size = risk_amount / sl_distance
            
            # Apply slippage
            if side == 'BUY':
                actual_entry = entry_price + (self.slippage_pips * 0.0001)
            else:
                actual_entry = entry_price - (self.slippage_pips * 0.0001)
            
            # Calculate commission
            trade_value = position_size * actual_entry
            commission = trade_value * (self.commission_pct / 100.0)
            
            # Open position
            self.open_position = {
                'entry_time': timestamp,
                'entry_price': actual_entry,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'side': side,
                'position_size': position_size,
                'commission': commission,
                'signal_confidence': signal.confidence,
                'signal_metadata': {
                    'strategy': signal.strategy,
                    'regime': signal.regime,
                    'entry_reason': signal.entry_reason,
                },
                'max_favorable_excursion': 0.0,  # MAE
                'max_adverse_excursion': 0.0,    # MFE
            }
            
            # Deduct commission from balance
            self.balance -= commission
            
            logger.debug(f"Entered {side} position: {position_size:.2f} @ {actual_entry:.5f}, "
                        f"SL: {sl_price:.5f}, TP: {tp_price:.5f}")
            
        except Exception as e:
            logger.error(f"Failed to enter trade: {e}", exc_info=True)
    
    def _check_exit(self, current_bar: pd.Series, timestamp, symbol: str):
        """Check if current bar triggers an exit."""
        if not self.open_position:
            return
        
        pos = self.open_position
        side = pos['side']
        entry_price = pos['entry_price']
        sl_price = pos['sl_price']
        tp_price = pos['tp_price']
        
        current_high = current_bar['high']
        current_low = current_bar['low']
        current_close = current_bar['close']
        
        exit_price = None
        exit_reason = None
        
        if side == 'BUY':
            # Update MAE and MFE
            unrealized_pnl = (current_high - entry_price) * pos['position_size']
            pos['max_favorable_excursion'] = max(pos['max_favorable_excursion'], unrealized_pnl)
            
            unrealized_loss = (entry_price - current_low) * pos['position_size']
            pos['max_adverse_excursion'] = max(pos['max_adverse_excursion'], unrealized_loss)
            
            # Check SL hit
            if current_low <= sl_price:
                exit_price = sl_price
                exit_reason = 'stop_loss'
            # Check TP hit
            elif current_high >= tp_price:
                exit_price = tp_price
                exit_reason = 'take_profit'
        
        else:  # SELL
            # Update MAE and MFE
            unrealized_pnl = (entry_price - current_low) * pos['position_size']
            pos['max_favorable_excursion'] = max(pos['max_favorable_excursion'], unrealized_pnl)
            
            unrealized_loss = (current_high - entry_price) * pos['position_size']
            pos['max_adverse_excursion'] = max(pos['max_adverse_excursion'], unrealized_loss)
            
            # Check SL hit
            if current_high >= sl_price:
                exit_price = sl_price
                exit_reason = 'stop_loss'
            # Check TP hit
            elif current_low <= tp_price:
                exit_price = tp_price
                exit_reason = 'take_profit'
        
        # If exit triggered, close position
        if exit_price:
            self._close_position(exit_price, timestamp, exit_reason, symbol)
    
    def _close_position(self, exit_price: float, timestamp, reason: str, symbol: str):
        """Close the open position."""
        pos = self.open_position
        
        # Calculate P&L
        if pos['side'] == 'BUY':
            pnl = (exit_price - pos['entry_price']) * pos['position_size']
        else:
            pnl = (pos['entry_price'] - exit_price) * pos['position_size']
        
        # Apply slippage
        if pos['side'] == 'BUY':
            actual_exit = exit_price - (self.slippage_pips * 0.0001)
        else:
            actual_exit = exit_price + (self.slippage_pips * 0.0001)
        
        # Recalculate PnL with slippage
        if pos['side'] == 'BUY':
            pnl = (actual_exit - pos['entry_price']) * pos['position_size']
        else:
            pnl = (pos['entry_price'] - actual_exit) * pos['position_size']
        
        # Subtract exit commission
        exit_commission = pos['position_size'] * actual_exit * (self.commission_pct / 100.0)
        pnl -= exit_commission
        
        # Update balance
        self.balance += pnl
        
        # Record trade
        trade_record = {
            'entry_time': pos['entry_time'],
            'exit_time': timestamp,
            'side': pos['side'],
            'entry_price': pos['entry_price'],
            'exit_price': actual_exit,
            'sl_price': pos['sl_price'],
            'tp_price': pos['tp_price'],
            'position_size': pos['position_size'],
            'pnl': pnl,
            'pnl_pct': (pnl / self.initial_balance) * 100,
            'commission': pos['commission'] + exit_commission,
            'exit_reason': reason,
            'duration_bars': len(self.equity_curve) - len([t for t in self.trades]),
            'mae': pos['max_adverse_excursion'],
            'mfe': pos['max_favorable_excursion'],
            'signal_confidence': pos['signal_confidence'],
            'signal_metadata': pos['signal_metadata'],
        }
        
        self.trades.append(trade_record)
        
        # Update equity tracking
        self.equity = self.balance
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = ((self.peak_equity - self.equity) / self.peak_equity) * 100
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Clear position
        self.open_position = None
        
        logger.debug(f"Closed {pos['side']} position: PnL ${pnl:.2f} ({reason})")
    
    def _force_close_position(self, final_bar: pd.Series, timestamp, symbol: str):
        """Force close position at end of backtest."""
        exit_price = final_bar['close']
        self._close_position(exit_price, timestamp, 'backtest_end', symbol)
    
    def _calculate_metrics(self) -> Dict:
        """Calculate comprehensive backtest metrics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown_pct': 0.0,
                'net_profit': 0.0,
                'return_pct': 0.0,
            }
        
        # Basic stats
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        
        win_rate = (num_wins / total_trades) * 100 if total_trades > 0 else 0.0
        
        # P&L stats
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        
        avg_win = total_profit / num_wins if num_wins > 0 else 0.0
        avg_loss = total_loss / num_losses if num_losses > 0 else 0.0
        
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0
        
        net_profit = self.balance - self.initial_balance
        return_pct = (net_profit / self.initial_balance) * 100
        
        # Risk-adjusted returns
        returns = [t['pnl_pct'] for t in self.trades]
        avg_return = np.mean(returns) if returns else 0.0
        std_return = np.std(returns) if len(returns) > 1 else 0.0
        
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0
        
        # Consecutive stats
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for trade in self.trades:
            if trade['pnl'] > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        # Average trade duration
        durations = [t['duration_bars'] for t in self.trades]
        avg_duration_bars = np.mean(durations) if durations else 0.0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
        
        return {
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'largest_win': round(max((t['pnl'] for t in winning_trades), default=0), 2),
            'largest_loss': round(min((t['pnl'] for t in losing_trades), default=0), 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown_pct': round(self.max_drawdown, 2),
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'net_profit': round(net_profit, 2),
            'return_pct': round(return_pct, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'expectancy': round(expectancy, 2),
            'avg_trade_duration_bars': round(avg_duration_bars, 1),
        }
    
    def save_to_database(self, backtest_results: Dict, user=None):
        """
        Save backtest results to database.
        
        Args:
            backtest_results: Results dict from run_backtest()
            user: Optional user object
            
        Returns:
            BacktestRun instance
        """
        try:
            from engine.models import BacktestRun, BacktestTrade
            from django.utils import timezone
            
            metrics = backtest_results['metrics']
            
            # Create BacktestRun
            backtest_run = BacktestRun.objects.create(
                user=user,
                symbol=backtest_results['symbol'],
                timeframe=backtest_results['timeframe'],
                strategy=backtest_results['strategy'],
                start_date=backtest_results['start_date'],
                end_date=backtest_results['end_date'],
                initial_balance=backtest_results['initial_balance'],
                final_balance=backtest_results['final_balance'],
                total_trades=metrics['total_trades'],
                winning_trades=metrics['winning_trades'],
                losing_trades=metrics['losing_trades'],
                win_rate=Decimal(str(metrics['win_rate'])),
                profit_factor=Decimal(str(metrics['profit_factor'])),
                max_drawdown_pct=Decimal(str(metrics['max_drawdown_pct'])),
                sharpe_ratio=Decimal(str(metrics['sharpe_ratio'])),
                expectancy=Decimal(str(metrics['expectancy'])),
                execution_time_sec=backtest_results['execution_time_sec'],
            )
            
            # Create BacktestTrade entries
            for trade in backtest_results['trades']:
                BacktestTrade.objects.create(
                    backtest_run=backtest_run,
                    entry_time=trade['entry_time'],
                    exit_time=trade['exit_time'],
                    side=trade['side'],
                    entry_price=Decimal(str(trade['entry_price'])),
                    exit_price=Decimal(str(trade['exit_price'])),
                    sl_price=Decimal(str(trade['sl_price'])),
                    tp_price=Decimal(str(trade['tp_price'])),
                    position_size=Decimal(str(trade['position_size'])),
                    pnl=Decimal(str(trade['pnl'])),
                    mae=Decimal(str(trade['mae'])),
                    mfe=Decimal(str(trade['mfe'])),
                    exit_reason=trade['exit_reason'],
                )
            
            logger.info(f"Saved backtest run {backtest_run.id} to database: "
                       f"{metrics['total_trades']} trades")
            
            return backtest_run
            
        except Exception as e:
            logger.error(f"Failed to save backtest to database: {e}", exc_info=True)
            return None


# Convenience function for quick backtesting
def quick_backtest(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    strategy_name: str,
    **backtest_params
) -> Dict:
    """
    Quick backtest wrapper.
    
    Args:
        df: OHLCV DataFrame
        symbol: Symbol string
        timeframe: Timeframe string
        strategy_name: Strategy to test ('SMC', 'Trend', etc.)
        **backtest_params: Additional parameters for BacktestEngine
        
    Returns:
        Backtest results dict
    """
    from engine.strategies import STRATEGY_DETECTORS
    
    # Get strategy detector
    if strategy_name not in STRATEGY_DETECTORS:
        raise ValueError(f"Unknown strategy: {strategy_name}. "
                        f"Available: {list(STRATEGY_DETECTORS.keys())}")
    
    detector_class = STRATEGY_DETECTORS[strategy_name]
    detector = detector_class()
    
    # Create backtester
    engine = BacktestEngine(**backtest_params)
    
    # Run backtest
    results = engine.run_backtest(df, symbol, timeframe, detector, strategy_name)
    
    return results


if __name__ == '__main__':
    print("🧪 Backtesting Engine Module")
    print("Use quick_backtest() or BacktestEngine class for testing")
