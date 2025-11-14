# 🎨 AutopsyLoop Dashboard Guide

## Quick Access

**Dashboard URL**: http://localhost:8000/autopsy/

**Prerequisites**: You must be logged in to access the dashboard.

---

## 📊 Dashboard Features

### 1. Overview Statistics

The dashboard displays key metrics at the top:

- **Total Audits**: Number of audits in the selected time period
- **Signals Available**: Total signals in the database
- **OHLCV Candles**: Total market data points available
- **Recent Jobs**: Number of batch analysis jobs

**Filter by Time Period**:
```
http://localhost:8000/autopsy/?days=7   # Last 7 days (default)
http://localhost:8000/autopsy/?days=30  # Last 30 days
http://localhost:8000/autopsy/?days=1   # Last 24 hours
```

---

### 2. Outcome Distribution

Visual breakdown of audit outcomes:
- ✅ **SUCCEEDED**: Trade hit target profit
- ❌ **FAILED**: Trade hit stop loss
- ⚪ **NEUTRAL**: Trade stayed flat

**Progress bars** show the percentage of each outcome type.

---

### 3. Top Failure Causes (RCA)

Table showing the most common root causes for failed trades:

| Cause | Description |
|-------|-------------|
| **Detector Mis-identification** | Pattern couldn't be re-verified |
| **News Shock** | Major news event caused volatility |
| **Regime Drift** | Market regime changed |
| **Volatility Spike** | Unusual price movement |
| **Model Error** | Prediction confidence mismatch |
| **Spread/Slippage** | High execution costs |
| **False Positive** | Pattern type has high fail rate |

**Columns**:
- **Count**: Number of times this cause was identified
- **Avg Confidence**: Average confidence score (0-100%)

---

### 4. Strategy Performance Table

Top 10 strategies ranked by total audits:

**Columns**:
- **Strategy**: Name of trading strategy (click to see details)
- **Total**: Total audits for this strategy
- **Success Rate**: Percentage of successful trades
- **Avg P&L**: Average profit/loss percentage
- **Avg Drawdown**: Average maximum adverse move in pips

**Color Coding**:
- 🟢 Green P&L = Profitable
- 🔴 Red P&L = Loss

**Click Strategy Name** to see detailed breakdown.

---

### 5. Recent Audits Table

Latest 20 audits with:
- **ID**: Audit record number
- **Signal**: Original signal number (e.g., #78)
- **Symbol**: Trading pair (EURUSD, GBPUSD, etc.)
- **Strategy**: Strategy name (truncated)
- **Outcome**: Success/Failed/Neutral badge
- **P&L**: Profit/loss percentage
- **Horizon**: Evaluation timeframe (4H, 24H, etc.)
- **Created**: Time since audit was created

---

### 6. Recent Batch Jobs

Shows last 5 batch analysis runs:
- **Job ID**: Unique identifier
- **Status**: completed/failed/running
- **Total**: Number of signals analyzed
- **Successful/Failed**: Breakdown of analysis results
- **Created**: When the job started

---

## 🔗 Quick Links

At the bottom of the dashboard:

1. **📋 View All Audits in Admin** - Full audit admin interface
2. **🔍 View All RCA Records** - All root cause analyses
3. **📊 View OHLCV Data** - Market data management

---

## 📈 Strategy Detail Page

Click any strategy name to see detailed analysis.

**URL Format**: `http://localhost:8000/autopsy/strategy/<strategy_name>/`

**Example**: `http://localhost:8000/autopsy/strategy/BreakOfStructure_v2/`

### Features:

1. **Overall Stats**
   - Total audits
   - Success/failure/neutral counts
   - Overall success rate

2. **Average Metrics**
   - Average P&L
   - Average drawdown

3. **Failure Analysis**
   - Top RCA causes for this strategy
   - Confidence scores

4. **Performance by Symbol**
   - How strategy performs on different pairs
   - Success rate per symbol

5. **Performance by Timeframe**
   - Best/worst timeframes for this strategy

6. **Recent Audits**
   - Last 50 audits for this strategy

---

## 🎯 Using the Dashboard

### Scenario 1: Weekly Performance Review

```bash
1. Navigate to http://localhost:8000/autopsy/?days=7
2. Check "Outcome Distribution" - What's the overall success rate?
3. Review "Strategy Performance" - Which strategies are winning?
4. Check "Top Failure Causes" - What's breaking?
5. Click on best/worst strategy for deep dive
```

### Scenario 2: Strategy Debugging

```bash
1. Run autopsy: python manage.py run_autopsy --strategy "YourStrategy" --last-days 30 --skip-checks
2. Navigate to http://localhost:8000/autopsy/?days=30
3. Find your strategy in the performance table
4. Click strategy name for detailed view
5. Review failure causes and symbol performance
6. Identify patterns in failures
```

### Scenario 3: Data Coverage Check

```bash
1. Check "OHLCV Candles" stat at top
2. Click "📊 View OHLCV Data" link
3. Verify you have data for symbols you're trading
4. Generate more data if needed:
   python manage.py generate_test_ohlcv --symbol EURUSD --days 30 --skip-checks
```

### Scenario 4: Daily Monitoring

```bash
1. Navigate to http://localhost:8000/autopsy/?days=1
2. Check "Recent Audits" table
3. Review any failed trades
4. Click strategy name if pattern emerges
5. Take action based on RCA findings
```

---

## 🔧 Common Workflows

### Workflow 1: After Running Batch Analysis

```bash
# Step 1: Run analysis
python manage.py run_autopsy --last-days 7 --horizons 4H,24H --skip-checks

# Step 2: View results
Open: http://localhost:8000/autopsy/?days=7

# Step 3: Review key metrics
- What's the success rate?
- Which strategies need attention?
- What are the top failure causes?

# Step 4: Deep dive on specific strategy
Click strategy name → Review details → Take action
```

### Workflow 2: Identifying Degrading Strategies

```bash
# Check 7-day performance
http://localhost:8000/autopsy/?days=7

# Compare to 30-day performance
http://localhost:8000/autopsy/?days=30

# If 7-day success rate < 30-day success rate:
1. Click strategy name
2. Review recent failures
3. Check RCA causes
4. Adjust strategy or labeling rules
```

### Workflow 3: Optimizing Labeling Rules

```bash
# View admin labeling rules
http://localhost:8000/admin/autopsy/labelingrule/

# Check dashboard performance
http://localhost:8000/autopsy/

# If many "neutral" outcomes:
→ Labeling rules may be too strict
→ Adjust TP/SL thresholds

# If high failure rate:
→ Check RCA for patterns
→ May need strategy adjustments
```

---

## 📊 Interpreting Results

### Good Signs ✅

- **Success rate > 50%**: Strategy is profitable
- **Avg P&L > 0**: Overall profitability
- **Low drawdowns**: Good risk management
- **Diverse RCA causes**: No systemic issue

### Warning Signs ⚠️

- **Success rate 40-50%**: Marginal strategy
- **Avg P&L near 0**: Break-even
- **High drawdowns**: Risk management issues
- **One dominant RCA cause**: Systemic problem

### Red Flags 🚨

- **Success rate < 40%**: Strategy needs review
- **Avg P&L < 0**: Losing money
- **Detector mis-identification > 60%**: Pattern detection broken
- **High "false_positive" RCA**: Pattern not reliable

---

## 🎨 Color Coding Guide

### Outcome Badges

- 🟢 **Green (SUCCEEDED)**: Trade was profitable
- 🔴 **Red (FAILED)**: Trade hit stop loss
- ⚪ **Gray (NEUTRAL)**: Trade was flat

### P&L Display

- 🟢 **Green**: Positive P&L (profit)
- 🔴 **Red**: Negative P&L (loss)

### Job Status

- 🟢 **Green (COMPLETED)**: Job finished successfully
- 🔴 **Red (FAILED)**: Job encountered errors
- ⚪ **Gray (RUNNING)**: Job in progress

---

## 💡 Pro Tips

1. **Use Time Filters**: Compare different periods to spot trends
2. **Click Strategy Names**: Deep dive into problem strategies
3. **Monitor RCA Patterns**: If one cause dominates, investigate
4. **Check Recent Audits**: Spot issues quickly
5. **Use Admin Links**: For detailed editing and filtering
6. **Run Regular Analyses**: Daily or weekly batch jobs
7. **Export Data**: Use admin export for Excel analysis
8. **Track Changes**: Note improvements after strategy adjustments

---

## 🔗 Related Pages

- **Admin Audits**: http://localhost:8000/admin/autopsy/insightaudit/
- **Admin RCA**: http://localhost:8000/admin/autopsy/auditrca/
- **Admin Jobs**: http://localhost:8000/admin/autopsy/autopsyjob/
- **Admin Rules**: http://localhost:8000/admin/autopsy/labelingrule/
- **OHLCV Data**: http://localhost:8000/admin/marketdata/ohlcvcandle/

---

## 🚀 Next Steps

After reviewing the dashboard:

1. **If success rate is low**:
   - Review labeling rules
   - Check OHLCV data quality
   - Analyze RCA patterns
   - Consider strategy adjustments

2. **If success rate is good**:
   - Document what's working
   - Expand to more symbols
   - Increase position sizes (carefully)
   - Run more frequent analyses

3. **If data is missing**:
   - Generate more OHLCV data
   - Import real historical data
   - Connect to broker API

4. **For continuous improvement**:
   - Set up scheduled analyses
   - Monitor daily
   - Iterate on strategies
   - Track metrics over time

---

## 📞 Troubleshooting

**Dashboard not loading?**
- Check you're logged in
- Verify autopsy app is in INSTALLED_APPS
- Check URL is correct: http://localhost:8000/autopsy/

**No data showing?**
- Run autopsy analysis first: `python manage.py run_autopsy --last-days 7 --skip-checks`
- Check time filter (try ?days=30)
- Verify audits exist in admin

**Strategies not clickable?**
- Strategy detail page requires strategy name in URL
- Check strategy name doesn't have special characters
- Use admin interface as alternative

---

**Dashboard URL**: http://localhost:8000/autopsy/  
**Documentation**: `/Users/macbook/zenithedge_trading_hub/AUTOPSY_*.md`  
**Admin**: http://localhost:8000/admin/autopsy/

**Ready to analyze your trading performance!** 📊
