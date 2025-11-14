# ZenithEdge Performance Analytics Module

## Overview

The Performance Analytics module provides comprehensive strategy performance analysis with simulated trade outcomes, visual charts, and detailed metrics tracking.

## Features

### 1. StrategyPerformance Model
Tracks detailed performance metrics for each strategy including:
- **Trade Statistics**: Total trades, wins, losses, win rate
- **Risk-Reward Metrics**: Average RR ratio, total R-multiple
- **Profitability**: Total PnL, average win/loss, profit factor
- **Drawdown**: Maximum and current drawdown percentages
- **Confidence**: Average confidence score of signals
- **Granularity**: Track performance by strategy, regime, symbol, and timeframe combinations

### 2. analyze_performance Management Command
Analyzes past signals and simulates trade outcomes:
- **Outcome Simulation**: Uses confidence scores to simulate win/loss
- **Flexible Filtering**: Filter by days, strategy, user, regime, or symbol
- **Multiple Groupings**: Creates 21 different performance groups for comprehensive analysis
- **Risk Calculation**: Assumes 1% risk per trade with proper position sizing
- **Performance Score**: Calculates composite score (0-100) based on multiple metrics

### 3. Strategy Performance Dashboard
Visual analytics dashboard at `/signals/strategies/`:
- **4 Interactive Charts**: Win rate, RR ratios, profit factors, trade volume distribution
- **Top Performer Badge**: Highlights best strategy over past 30 days
- **Comprehensive Filters**: Strategy name, regime, symbol, timeframe, profitability, min trades
- **Sortable Table**: Sort by any metric (win rate, RR, profit factor, PnL, etc.)
- **Performance Scores**: Color-coded badges (excellent/good/fair/poor)
- **Role-Based Access**: Admins see all, traders see only their own

## Usage

###install Command to Analyze Performance

```bash
# Basic analysis (last 30 days with simulated outcomes)
python manage.py analyze_performance --simulate

# Custom time period
python manage.py analyze_performance --days 90 --simulate

# Filter by strategy
python manage.py analyze_performance --strategy ZenithEdge --simulate

# Filter by user
python manage.py analyze_performance --user admin@zenithedge.com --simulate

# Filter by regime
python manage.py analyze_performance --regime Trend --simulate

# Filter by symbol
python manage.py analyze_performance --symbol BTCUSD --simulate

# Clear existing records before analysis
python manage.py analyze_performance --clear --simulate

# Combine filters
python manage.py analyze_performance --days 60 --regime Breakout --symbol ETHUSD --simulate
```

### Command Options

| Option | Type | Description |
|--------|------|-------------|
| `--days` | Integer | Number of days to analyze (default: 30) |
| `--strategy` | String | Filter by specific strategy name |
| `--user` | String | Filter by user email |
| `--regime` | Choice | Filter by regime (Trend/Breakout/MeanReversion/Squeeze) |
| `--symbol` | String | Filter by specific symbol |
| `--simulate` | Flag | Use simulated outcomes (for demo/testing) |
| `--clear` | Flag | Clear existing performance records before analysis |

### Access the Dashboard

1. **Navigate to**: `http://127.0.0.1:8000/signals/strategies/`
2. **Login required**: Must be authenticated
3. **View options**:
   - Admins see all strategy performances
   - Traders see only their own

### Dashboard Features

#### Statistics Cards
- **Total Strategies**: Number of analyzed strategy combinations
- **Profitable Strategies**: Count and percentage of profitable strategies
- **Total Trades**: Aggregate trade count across all strategies
- **Average Win Rate**: Mean win rate across all strategies

#### Charts
1. **Win Rate Comparison**: Bar chart showing win rates
2. **Risk-Reward Ratios**: Visual comparison of average RR
3. **Profit Factor Analysis**: Profitability ratios
4. **Trade Volume Distribution**: Pie chart of trade distribution

#### Filters
- **Strategy Name**: Text search
- **Regime**: Trend, Breakout, MeanReversion, Squeeze, or All
- **Symbol**: Dropdown of available symbols
- **Timeframe**: Dropdown of available timeframes
- **Profitability**: All, Profitable Only, or Unprofitable Only
- **Min Trades**: Minimum number of trades required
- **Sort By**: Multiple sorting options (win rate, RR, profit factor, etc.)

#### Performance Table Columns
- **Strategy**: Name with top performer badge if applicable
- **Regime**: Trading regime (if specific)
- **Symbol**: Trading symbol (if specific)
- **TF**: Timeframe (if specific)
- **Trades**: Total number of trades
- **Win Rate**: Percentage with visual progress bar
- **Avg RR**: Average risk-reward ratio
- **Profit Factor**: Gross profit / gross loss ratio
- **Max DD**: Maximum drawdown percentage
- **Total PnL**: Total profit/loss in currency
- **Score**: Composite performance score (0-100)
- **Updated**: Last analysis date

## Performance Metrics Explained

### Win Rate
```
Win Rate = (Winning Trades / Total Trades) × 100
```
- **Excellent**: ≥ 60%
- **Good**: 40-59%
- **Poor**: < 40%

### Average Risk-Reward Ratio
```
Avg RR = Sum of all R-multiples / Total Trades
```
- **Excellent**: ≥ 1.5
- **Good**: 1.0-1.49
- **Poor**: < 1.0

### Profit Factor
```
Profit Factor = Gross Profit / Gross Loss
```
- **Excellent**: ≥ 2.0
- **Good**: 1.0-1.99
- **Poor**: < 1.0

### Performance Score
```
Score = (Win Rate × 40%) + (RR Score × 30%) + (PF Score × 30%)
```
- **Excellent**: 70-100 (Green)
- **Good**: 50-69 (Blue)
- **Fair**: 30-49 (Orange)
- **Poor**: 0-29 (Red)

### Maximum Drawdown
```
Max DD = (Peak Equity - Trough Equity) / Peak Equity × 100
```
- **Excellent**: ≤ 10%
- **Acceptable**: 10-20%
- **High Risk**: > 20%

## Trade Simulation

### How It Works

1. **Confidence-Based Probability**:
   ```python
   win_probability = (signal.confidence / 100) × 0.85
   ```
   - Higher confidence → higher win probability
   - Capped at 90% to add realism

2. **Risk Calculation**:
   ```python
   risk_amount = current_equity × 0.01  # 1% risk per trade
   ```

3. **Outcome Simulation**:
   ```python
   if is_win:
       pnl = risk_amount × rr_ratio
   else:
       pnl = -risk_amount
   ```

4. **Equity Tracking**:
   - Updates equity after each trade
   - Tracks peak equity for drawdown calculation
   - Calculates running drawdown

### Example Calculation

**Signal Details**:
- Symbol: BTCUSD
- Entry: $45,000
- Stop Loss: $44,500
- Take Profit: $46,000
- Side: Buy
- Confidence: 85%

**Calculations**:
```
Risk = |45000 - 44500| = $500
Reward = |46000 - 45000| = $1000
RR Ratio = 1000 / 500 = 2.0

Win Probability = 0.85 × 0.85 = 72.25%
Random Draw: 0.45 < 0.7225 = WIN

Starting Equity: $10,000
Risk Amount: $10,000 × 0.01 = $100
PnL = $100 × 2.0 = $200
New Equity: $10,200
```

## Database Schema

### StrategyPerformance Model

```python
class StrategyPerformance(models.Model):
    # Identification
    strategy_name = CharField(max_length=100)
    regime = CharField(choices=REGIME_CHOICES, null=True)
    symbol = CharField(max_length=20, null=True)
    timeframe = CharField(max_length=10, null=True)
    
    # Trade Stats
    total_trades = IntegerField()
    winning_trades = IntegerField()
    losing_trades = IntegerField()
    win_rate = FloatField()  # 0-100%
    
    # Risk-Reward
    avg_rr = FloatField()
    total_rr = FloatField()  # Cumulative R-multiple
    
    # Profitability
    total_pnl = DecimalField()
    avg_win = DecimalField()
    avg_loss = DecimalField()
    profit_factor = FloatField()
    
    # Drawdown
    max_drawdown = FloatField()  # Percentage
    current_drawdown = FloatField()
    
    # Other
    avg_confidence = FloatField()
    analysis_period_start = DateTimeField()
    analysis_period_end = DateTimeField()
    last_updated = DateTimeField(auto_now=True)
    user = ForeignKey(CustomUser)
```

### Unique Constraint
```python
unique_together = [
    ['strategy_name', 'regime', 'symbol', 'timeframe', 'user']
]
```

## API Integration

### Webhook URL
The webhook URL has been updated to:
```
http://127.0.0.1:8000/signals/api/webhook/
```

**Note**: The URL path changed from `/api/signals/webhook/` to `/signals/api/webhook/` to accommodate the new routing structure.

## Admin Interface

Access performance records in Django admin:
1. Navigate to `http://127.0.0.1:8000/admin/`
2. Go to "Signals" → "Strategy Performances"
3. Features:
   - Filter by regime, symbol, timeframe, user
   - Search by strategy name or symbol
   - Sort by any metric
   - View detailed fieldsets
   - Role-based filtering (traders see only their own)

## Examples

### Example 1: Weekly Analysis

```bash
# Analyze last 7 days with simulated outcomes
python manage.py analyze_performance --days 7 --simulate

# View results in dashboard
# Navigate to http://127.0.0.1:8000/signals/strategies/
# Apply filter: Min Trades = 2
```

### Example 2: Strategy Comparison

```bash
# Analyze Trend regime
python manage.py analyze_performance --regime Trend --simulate

# Analyze Breakout regime
python manage.py analyze_performance --regime Breakout --simulate

# View dashboard and compare:
# - Win rates between regimes
# - Average RR ratios
# - Profit factors
```

### Example 3: Symbol-Specific Analysis

```bash
# Analyze BTCUSD performance
python manage.py analyze_performance --symbol BTCUSD --simulate

# View dashboard filtered by BTCUSD
# Check: Win rate, drawdown, profitability
```

### Example 4: Fresh Analysis

```bash
# Clear all existing data and re-analyze
python manage.py analyze_performance --clear --days 90 --simulate
```

## Performance Groupings

The analyzer creates multiple performance groups automatically:

1. **Overall Strategy**: `(ZenithEdge, None, None, None)`
2. **Strategy + Regime**: `(ZenithEdge, Trend, None, None)`
3. **Strategy + Symbol**: `(ZenithEdge, None, BTCUSD, None)`
4. **Strategy + Timeframe**: `(ZenithEdge, None, None, 1H)`
5. **Strategy + Regime + Symbol**: `(ZenithEdge, Trend, BTCUSD, None)`
6. **Full Granularity**: `(ZenithEdge, Trend, BTCUSD, 1H)`

This allows analysis at different levels of detail.

## Troubleshooting

### "No signals found"
- Check date range with `--days` parameter
- Verify signals exist in database
- Check filters (regime, symbol, strategy)

### "No performance data available"
- Run the analyze_performance command first
- Use `--simulate` flag for demo data
- Ensure minimum trade requirements are met

### Charts not displaying
- Clear browser cache
- Check browser console for JavaScript errors
- Verify Chart.js is loading from CDN

### Wrong data showing
- Clear existing performance records: `--clear`
- Re-run analysis with correct filters
- Check user role (traders see only their own)

## Future Enhancements

### Planned Features
1. **Real OHLCV Integration**: Replace simulation with actual market data
2. **Advanced Metrics**: Sharpe ratio, Sortino ratio, Calmar ratio
3. **Equity Curve Charts**: Visual equity progression over time
4. **Monte Carlo Simulation**: Risk analysis and confidence intervals
5. **Export Functionality**: CSV/Excel export of performance data
6. **Comparison Mode**: Side-by-side strategy comparison
7. **Time-Based Analysis**: Performance by time of day, day of week
8. **Regime Detection**: Automatic market regime identification
9. **Backtesting Integration**: Link to full backtesting engine
10. **Performance Alerts**: Email/SMS notifications for top performers

### Enhancement Ideas
- Rolling statistics (30/60/90 day windows)
- Strategy correlation matrix
- Risk-adjusted returns
- Win/loss streak analysis
- Trade distribution histograms
- Heatmaps for symbol/timeframe performance

## Best Practices

1. **Regular Analysis**: Run weekly to track performance trends
2. **Minimum Trades**: Use min_trades filter to avoid statistical noise
3. **Multiple Timeframes**: Analyze different periods (7/30/90 days)
4. **Compare Regimes**: Identify which market conditions work best
5. **Monitor Drawdown**: Keep max drawdown below 20%
6. **Track Confidence**: Correlate confidence scores with outcomes
7. **Document Changes**: Note strategy modifications and their impact

## Support

For issues or questions:
1. Check Django logs for errors
2. Run with `--help` flag for command options
3. Review admin panel for data verification
4. Test with `--simulate` flag first
5. Verify role permissions for dashboard access

## Version History

**v1.0.0** - Initial Release
- StrategyPerformance model
- analyze_performance command
- Strategy performance dashboard
- Chart.js visualizations
- Role-based access control
- Comprehensive filtering
- Top performer badge
