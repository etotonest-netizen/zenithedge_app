# Dynamic Backtesting System

## Overview
The Dynamic Backtesting System allows users to test trading strategies against historical signal data, analyze performance metrics, and visualize results through interactive charts.

## Features

### 1. **Configurable Backtest Parameters**
- **Strategy Filter**: Test specific strategies or all strategies
- **Symbol Filter**: Focus on specific currency pairs/instruments
- **Timeframe Filter**: Test across different timeframes (M5, M15, H1, H4, D1)
- **Date Range**: Select custom start and end dates for backtest period
- **AI Score Filter**: Set minimum AI score threshold (e.g., only test signals with score ≥ 70)
- **News Filter**: Option to ignore signals blocked by news filters

### 2. **Comprehensive Performance Metrics**
- **Total Trades**: Number of trades executed in backtest period
- **Win Rate**: Percentage of winning trades
- **Average R:R Ratio**: Mean risk/reward ratio across all trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Max Drawdown**: Maximum peak-to-trough decline in equity
- **Total P&L**: Net profit/loss in pips/points
- **Final Equity**: Ending capital after all trades

### 3. **Visual Analytics**
- **Equity Curve Chart**: Line chart showing account balance over time
- **Win/Loss Distribution**: Bar chart showing daily/session-based wins and losses
- Interactive Chart.js visualizations with hover tooltips

### 4. **Trade Details Table**
- Complete list of all trades in backtest
- Per-trade information:
  - Entry date/time
  - Symbol and side (BUY/SELL)
  - Entry, Stop Loss, Take Profit prices
  - R:R ratio
  - Outcome (WIN/LOSS/BREAKEVEN)
  - P&L and running equity
  - AI Score
- **Replay Link**: Direct link to trade replay view for each signal

### 5. **Persistence & Export**
- **Save Backtests**: Mark important backtests for future reference
- **Custom Naming**: Give descriptive names to saved backtests
- **CSV Export**: Download complete trade data for external analysis
- **Backtest History**: View and compare all saved backtests

## Usage

### Running a Backtest

1. **Navigate to Backtest Page**
   ```
   Dashboard → Backtest (navigation menu)
   Or direct URL: /backtest/
   ```

2. **Configure Parameters**
   - Select strategy (required)
   - Optionally filter by symbol, timeframe
   - Set date range (defaults to all available data)
   - Set minimum AI score if desired
   - Check "Ignore news-blocked signals" if needed

3. **Run Backtest**
   - Click "Run Backtest" button
   - System executes backtest simulation
   - Redirects to results page automatically

4. **Analyze Results**
   - Review performance summary statistics
   - Examine equity curve for drawdowns
   - Check win/loss distribution
   - Review individual trade details
   - Use Replay links to review specific trades

5. **Save or Export**
   - Click "Save" to bookmark this backtest
   - Add custom name for easy reference
   - Click "Export CSV" to download trade data

### Viewing Saved Backtests

```
/backtest/saved/
```

- Lists all saved backtests
- Shows key metrics (trades, win rate, profit factor)
- Click "View" to see full results
- Download or delete backtests as needed

## Technical Implementation

### Data Flow

1. **Query Construction**
   ```python
   # User selects: Strategy="Trend", Symbol="EURUSD", Start=2024-01-01, End=2024-12-31
   query = Q(user=request.user, strategy__icontains="Trend", symbol__icontains="EURUSD")
   query &= Q(received_at__gte=start_date, received_at__lte=end_date)
   signals = Signal.objects.filter(query).select_related('ai_score', 'evaluation')
   ```

2. **Trade Outcome Determination**
   - **Priority 1**: TradeJournalEntry.outcome (green/red/breakeven)
   - **Priority 2**: Signal.status (hit_tp/hit_sl)
   - **Priority 3**: SignalEvaluation.passed (blocked signals → loss)
   - **Fallback**: Random 50/50 simulation

3. **Statistics Calculation**
   ```python
   # Win Rate
   win_rate = (winning_trades / total_trades) * 100
   
   # Profit Factor
   profit_factor = total_profit / total_loss
   
   # Max Drawdown
   drawdown = ((peak_equity - current_equity) / peak_equity) * 100
   max_drawdown = max(all_drawdowns)
   
   # Average R:R
   avg_rr = sum(rr_ratios) / len(rr_ratios)
   ```

4. **Equity Simulation**
   - Starting capital: $10,000
   - Risk per trade: 1% of current equity
   - P&L calculation: risk_amount * RR_ratio (for wins) or -risk_amount (for losses)
   - Running equity tracked for curve visualization

### Models

#### BacktestRun
```python
class BacktestRun(models.Model):
    user = ForeignKey(User)
    strategy = CharField(max_length=100)
    symbol = CharField(max_length=20, blank=True)
    timeframe = CharField(max_length=10, blank=True)
    start_date = DateField()
    end_date = DateField()
    params = JSONField()  # Additional filters
    
    # Results
    total_trades = IntegerField()
    winning_trades = IntegerField()
    losing_trades = IntegerField()
    win_rate = FloatField()
    avg_rr = FloatField()
    max_drawdown = FloatField()
    profit_factor = FloatField()
    total_pnl = DecimalField()
    
    # Chart data
    equity_curve = JSONField()  # [{date, equity}, ...]
    trade_details = JSONField()  # [{date, symbol, side, ...}, ...]
    
    # Metadata
    is_saved = BooleanField()
    name = CharField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
```

### Views

- `backtest_form(request)` - Display backtest configuration form
- `backtest_run(request)` - Execute backtest and save results
- `backtest_results(request, backtest_id)` - Display results with charts
- `backtest_save(request, backtest_id)` - Mark backtest as saved
- `backtest_export_csv(request, backtest_id)` - Export trade data
- `backtest_list(request)` - List all saved backtests
- `backtest_delete(request, backtest_id)` - Delete a backtest

### URL Routes

```python
/backtest/                        # Main form
/backtest/run/                    # Execute backtest (POST)
/backtest/<id>/                   # View results
/backtest/<id>/save/              # Save backtest (POST)
/backtest/<id>/export/            # Export CSV
/backtest/saved/                  # List saved backtests
/backtest/<id>/delete/            # Delete backtest (POST/DELETE)
```

## Performance Interpretation

### Win Rate
- **≥ 70%**: Excellent (green badge)
- **55-70%**: Good (blue badge)
- **45-55%**: Average (yellow badge)
- **< 45%**: Poor (red badge)

### Profit Factor
- **≥ 2.0**: Excellent profitability
- **1.5-2.0**: Good profitability
- **1.0-1.5**: Breakeven to slight profit
- **< 1.0**: Losing strategy

### Max Drawdown
- **< 10%**: Excellent risk management
- **10-20%**: Acceptable drawdown
- **> 20%**: High risk, review strategy

### Average R:R Ratio
- **≥ 2.0**: Excellent risk/reward
- **1.5-2.0**: Good risk/reward
- **1.0-1.5**: Acceptable
- **< 1.0**: Poor risk/reward

## Best Practices

1. **Use Adequate Sample Size**
   - Minimum 30-50 trades for statistical significance
   - Longer date ranges provide more reliable results

2. **Apply Realistic Filters**
   - Use same filters you would in live trading
   - Don't over-optimize (curve fitting)

3. **Consider Market Conditions**
   - Bull vs bear markets
   - High vs low volatility periods
   - Different trading sessions (London, NY, Asian)

4. **Compare Strategies**
   - Run multiple backtests with different parameters
   - Compare win rates, profit factors, drawdowns
   - Identify best-performing strategy/symbol combinations

5. **Validate with Forward Testing**
   - Backtest results are historical
   - Always validate with paper trading before live deployment

## Limitations

1. **Outcome Data Quality**
   - Relies on TradeJournalEntry outcomes being recorded
   - Fallback logic may not reflect actual results
   - Manual journal entry recommended for accuracy

2. **Slippage & Fees**
   - Does not account for spread, commission, slippage
   - Real trading results may differ

3. **Execution Assumptions**
   - Assumes all signals are tradable
   - Assumes fills at exact entry/SL/TP prices

4. **Market Conditions**
   - Past performance doesn't guarantee future results
   - Market regime changes can invalidate backtest conclusions

## Future Enhancements

- [ ] Multi-strategy comparison view
- [ ] Monte Carlo simulation for risk analysis
- [ ] Optimization engine for parameter tuning
- [ ] Integration with broker APIs for realistic fills
- [ ] Walk-forward analysis
- [ ] ZenBot command `/backtest recommend` for best strategy
- [ ] Automated backtest scheduling (weekly/monthly reports)

## API Access (Future)

```python
# Programmatic backtest execution
from analytics.backtester import TradeBacktester

backtester = TradeBacktester(user=request.user)
results = backtester.run(
    strategy='Trend Following',
    symbol='EURUSD',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    filters={'min_score': 70}
)

print(f"Win Rate: {results['win_rate']}%")
print(f"Total P&L: ${results['total_pnl']}")
```

## Support

For issues or questions:
- Review this documentation
- Check Django admin for BacktestRun entries
- Examine console logs for errors
- Verify Signal data exists for selected date range

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Maintainer**: ZenithEdge Development Team
