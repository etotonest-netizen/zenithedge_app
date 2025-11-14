# ZenithEdge Trading Engine - Quick Start Guide (PHASE 2 COMPLETE)

## ✅ Status: 100% Complete - Production Ready!

**What's Included:**
- ✅ All 10 strategy detectors (SMC, ICT, Trend, Breakout, etc.)
- ✅ Technical indicators library (20+ indicators)
- ✅ ZenBot scoring integration
- ✅ Visual overlays generation (boxes, labels, arrows)
- ✅ Backtesting engine with metrics
- ✅ Real-time processing pipeline (cron-ready)
- ✅ REST API endpoints
- ✅ Comprehensive test suite
- ✅ Complete documentation

## 🚀 Quick Deployment (5 Minutes)

### Step 1: Local Setup & Testing

```bash
cd /Users/macbook/zenithedge_trading_hub

# Run migrations
python manage.py makemigrations engine
python manage.py migrate engine

# Test SMC detector with sample data
python manage.py shell
```

In Python shell:
```python
import pandas as pd
from engine.smc import detect_smc
from engine.strategies import detect_all_strategies

# Load sample data
df = pd.read_csv('adapters/sample_data/eurusd_1h.csv', 
                 parse_dates=['timestamp'], 
                 index_col='timestamp')

# Test SMC detection
signals = detect_smc(df, 'EURUSD', '1H')
print(f"✅ Detected {len(signals)} SMC signals")

# Test all strategies
all_signals = detect_all_strategies(df, 'EURUSD', '1H')
print(f"✅ Detected {len(all_signals)} total signals from all strategies")

# Show first signal
if signals:
    signal = signals[0]
    print(f"\nSample Signal:")
    print(f"  Side: {signal['side']}")
    print(f"  Price: {signal['price']}")
    print(f"  SL: {signal['stop_loss']}, TP: {signal['take_profit']}")
    print(f"  Confidence: {signal['confidence']}%")
    print(f"  Type: {signal['signal_type']}")
```

### Step 2: Upload to Server

```bash
# Make deploy script executable
chmod +x deploy_engine.sh

# Upload files to server
scp -r engine/ equabish@server293.web-hosting.com:~/etotonest.com/
scp -r adapters/ equabish@server293.web-hosting.com:~/etotonest.com/
scp zenithedge/settings.py equabish@server293.web-hosting.com:~/etotonest.com/zenithedge/
scp deploy_engine.sh equabish@server293.web-hosting.com:~/
```

### Step 3: Run Deployment Script on Server

```bash
# SSH into server
ssh equabish@server293.web-hosting.com

# Run deployment script
chmod +x deploy_engine.sh
./deploy_engine.sh
```

The script will:
- ✅ Backup existing project
- ✅ Create directory structure
- ✅ Install dependencies (pandas, numpy, yfinance, scikit-learn, xgboost)
- ✅ Run migrations
- ✅ Collect static files
- ✅ Test imports
- ✅ Restart Passenger

### Step 4: Setup Cron Job

1. Go to **cPanel → Cron Jobs**
2. Add this cron job (every 5 minutes):

```
*/5 * * * * cd /home/equabish/etotonest.com && /home/equabish/virtualenv/etotonest.com/3.11/bin/python manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1
```

**Note:** The `fetch_and_run` command is complete and ready to use ✅

### Step 5: Test Everything

```bash
# On server, activate venv
cd ~/etotonest.com
source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate

# Test engine
python manage.py shell --settings=zenithedge.settings_production
```

In shell:
```python
from engine.smc import detect_smc
from engine.models import MarketBar
import pandas as pd

# Test with sample data
df = pd.read_csv('adapters/sample_data/eurusd_1h.csv', 
                 parse_dates=['timestamp'])
df = df.set_index('timestamp')

signals = detect_smc(df, 'EURUSD', '1H')
print(f"✅ Engine working! Detected {len(signals)} signals")

# Check database tables
print(f"\nMarketBar count: {MarketBar.objects.count()}")
```

---

## 📊 What's Been Built (Phase 1)

### ✅ Core Components Completed

1. **Engine App** (`engine/`)
   - Models: `MarketBar`, `BacktestRun`, `BacktestTrade`
   - Admin interfaces for all models
   - Full Django app structure

2. **Technical Indicators** (`engine/indicators.py`)
   - ATR, SMA, EMA, RSI, Stdev
   - Bollinger Bands, Keltner Channels
   - ADX, VWAP, Pivot Points
   - Market Structure analysis
   - All vectorized with pandas/numpy

3. **SMC Detector** (`engine/smc.py`)
   - Swing High/Low detection
   - Break of Structure (BOS) & Change of Character (CHoCH)
   - Order Block discovery with strength scoring
   - Fair Value Gaps (FVG) detection
   - Liquidity sweeps and stop hunts
   - Premium/Discount zone calculation
   - Complete signal metadata generation

4. **All 10 Strategy Detectors** (`engine/strategies.py`)
   - ✅ **SMC** - Smart Money Concepts
   - ✅ **ICT** - Inner Circle Trader (killzones, wick rejections)
   - ✅ **Trend** - MA crossovers, ADX confirmation
   - ✅ **Breakout** - Donchian channels, volume spikes
   - ✅ **MeanReversion** - RSI + Bollinger extremes
   - ✅ **Squeeze** - BB inside KC volatility expansion
   - ✅ **Scalping** - RSI-3, fast EMA (1m/5m only)
   - ✅ **VWAP** - Reclaims and breakdowns
   - ✅ **SupplyDemand** - Displacement candles, zones
   - ✅ **MultiTF** - Higher timeframe alignment

5. **Data Adapters** (`adapters/`)
   - `tv_historical.py` - Fetch from yfinance (free!)
   - Sample data: `eurusd_1h.csv`
   - Automatic symbol normalization
   - Timeframe conversion
   - CSV save/load functions

6. **Documentation**
   - `ENGINE_README.md` - Complete documentation
   - `deploy_engine.sh` - Automated deployment script
   - This Quick Start Guide

---

## 🎯 Usage Examples

### Example 1: Test SMC Detection

```python
from engine.smc import detect_smc
import pandas as pd

# Your DataFrame with OHLCV data
df = pd.DataFrame({
    'timestamp': [...],
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})
df = df.set_index('timestamp')

# Detect SMC signals
signals = detect_smc(df, symbol='EURUSD', timeframe='1H')

# Process signals
for signal in signals:
    print(f"Signal: {signal['side']} @ {signal['price']}")
    print(f"  Type: {signal['signal_type']}")
    print(f"  Structure: {signal['market_structure']}")
    print(f"  Confidence: {signal['confidence']}%")
```

### Example 2: Run All Strategies

```python
from engine.strategies import detect_all_strategies

# Run all 10 detectors
all_signals = detect_all_strategies(df, 'EURUSD', '1H')

# Group by strategy
from collections import defaultdict
by_strategy = defaultdict(list)

for signal in all_signals:
    by_strategy[signal['strategy']].append(signal)

# Show counts
for strategy, signals in by_strategy.items():
    print(f"{strategy}: {len(signals)} signals")
```

### Example 3: Fetch Live Data

```python
from adapters.tv_historical import fetch_historical_data
from datetime import datetime, timedelta

# Fetch last 30 days of 1H data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

df = fetch_historical_data(
    symbol='EURUSD',
    timeframe='1H',
    start=start_date,
    end=end_date
)

print(f"Fetched {len(df)} bars")
```

### Example 4: Store Market Data in Database

```python
from engine.models import MarketBar
from adapters.tv_historical import fetch_historical_data

# Fetch data
df = fetch_historical_data('EURUSD', '1H')

# Store in database
for _, row in df.iterrows():
    MarketBar.objects.update_or_create(
        symbol='EURUSD',
        timeframe='1H',
        timestamp=row['timestamp'],
        defaults={
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        }
    )

print(f"Stored {len(df)} bars in database")
```

---

## 🔧 Troubleshooting

### Import Errors

```bash
# Make sure engine is in INSTALLED_APPS
python manage.py check

# If pandas/numpy missing:
pip install pandas numpy yfinance
```

### No Signals Detected

```python
# Check if DataFrame has enough data
print(f"DataFrame length: {len(df)}")
# Need at least 50 bars for most strategies

# Check indicator calculation
from engine.indicators import calculate_all_indicators
df = calculate_all_indicators(df)
print(df.tail())
```

### Database Migration Issues

```bash
# Reset engine migrations (CAUTION: deletes data)
python manage.py migrate engine zero
python manage.py migrate engine
```

---

## 📱 Access Points

Once deployed, access these URLs:

- **Admin**: http://etotonest.com/admin/engine/
- **Quick Entry**: http://etotonest.com/signals/quick-entry/
- **Main Dashboard**: http://etotonest.com/signals/dashboard/

**API Endpoints** (COMPLETE ✅):
- `/engine/api/visuals/latest/?symbol=EURUSD&token=YOUR_TOKEN` - Latest signal visuals
- `/engine/api/visuals/<signal_id>/?token=YOUR_TOKEN` - Specific signal visuals
- `/engine/api/visuals/backtest/<id>/?token=YOUR_TOKEN` - Backtest equity curve
- `/engine/api/status/?token=YOUR_TOKEN` - Engine health check
- `POST /engine/api/detect/` - Trigger manual detection

---

## 🎓 Learning the System

### Strategy Confidence Levels

- **90-100%**: Multiple confluence factors, strong structure
- **80-89%**: Good setup with confirmation
- **70-79%**: Valid setup, moderate confidence
- **60-69%**: Acceptable but watch closely
- **<60%**: Low confidence, avoid or very small position

### Market Regimes

- **trending**: Clear directional movement (ADX > 25)
- **ranging**: Price bouncing between levels
- **volatile**: High ATR, rapid price swings
- **quiet**: Low volume, tight ranges

### Signal Types (SMC)

- `ob_retest`: Order Block retest in premium/discount zone
- `fvg_fill`: Fair Value Gap being filled
- `bos_continuation`: Break of Structure confirmation
- `liquidity_sweep`: Stop hunt followed by reversal

---

## 💡 Pro Tips

1. **Start Small**: Test with 1-2 strategies first (SMC + Trend)
2. **Use Higher Timeframes**: 1H/4H/D more reliable than 1m/5m
3. **Confluence**: Look for signals from multiple strategies
4. **Premium/Discount**: SMC works best in discount (buy) or premium (sell) zones
5. **Market Hours**: ICT strategy respects session times (London/NY overlap best)
6. **Backtesting**: Always backtest before live trading

---

## 📞 Next Steps

1. ✅ Test locally with sample data
2. ✅ Deploy to server
3. ✅ Verify imports working
4. ✅ Build real-time fetcher (`fetch_and_run`)
5. ✅ Add scoring integration
6. ✅ Create visuals API
7. ✅ Build backtesting engine
8. ✅ Write comprehensive tests
9. 📋 Deploy Phase 2 to server (see DEPLOYMENT_CHECKLIST_PHASE2.md)
10. 📋 Set up cron jobs (instructions in ENGINE_README.md)

**Status**: 🎉 **100% COMPLETE** - Production ready! Ready for deployment.

---

## 🎯 Advanced Usage

### Run Backtest from Command Line

```bash
# Test SMC strategy on EURUSD
python manage.py run_backtest \
    --strategy=SMC \
    --symbol=EURUSD \
    --timeframe=1H \
    --start=2024-01-01 \
    --end=2024-11-01 \
    --balance=10000 \
    --risk=1.0 \
    --fetch \
    --save

# Test Trend Following
python manage.py run_backtest \
    --strategy=Trend \
    --symbol=GBPUSD \
    --timeframe=4H \
    --start=2024-01-01 \
    --end=2024-11-01 \
    --commission=0.1 \
    --slippage=1.0 \
    --save
```

### Manual Signal Detection

```bash
python manage.py shell
```

```python
from engine.strategies import detect_all_strategies
from engine.models import MarketBar
import pandas as pd

# Load recent data
bars = MarketBar.objects.filter(
    symbol='EURUSD',
    timeframe='1H'
).order_by('-timestamp')[:200]

df = pd.DataFrame([
    {
        'timestamp': bar.timestamp,
        'open': float(bar.open),
        'high': float(bar.high),
        'low': float(bar.low),
        'close': float(bar.close),
        'volume': float(bar.volume),
    }
    for bar in reversed(list(bars))
])
df.set_index('timestamp', inplace=True)

# Detect signals
signals = detect_all_strategies(df, 'EURUSD', '1H')
print(f"Detected {len(signals)} signals")

for signal in signals:
    print(f"\n{signal['strategy']}: {signal['side']} @ {signal['price']:.5f}")
    print(f"  Confidence: {signal['confidence']}%")
    print(f"  SL: {signal['sl']:.5f}, TP: {signal['tp']:.5f}")
```

### Access Visual Overlays API

```bash
# Get visuals for latest signal
curl "http://etotonest.com/engine/api/visuals/latest/?symbol=EURUSD&token=YOUR_TOKEN"

# Get visuals for specific signal
curl "http://etotonest.com/engine/api/visuals/123/"

# Get backtest visuals
curl "http://etotonest.com/engine/api/visuals/backtest/1/"

# Engine status
curl "http://etotonest.com/engine/api/status/"
```

### Score Signals Programmatically

```python
from engine.scoring import score_and_save
from signals.models import Signal

signal = Signal.objects.latest('id')

ai_score, trade_score = score_and_save(signal, {
    'confidence': 82,
    'strategy': 'SMC',
    'regime': 'Trending',
    'entry_reason': 'BOS + OB retest',
    'structure_tags': ['BOS', 'OB_retest', 'discount'],
})

print(f"AI Score: {ai_score}/100")
```

### Run Tests

```bash
# Run all engine tests
python manage.py test engine.tests

# Run specific test class
python manage.py test engine.tests.test_engine.SMCTestCase

# Run with verbose output
python manage.py test engine.tests -v 2
```

---

**Need Help?** Check `ENGINE_README.md` for detailed documentation.

**Happy Trading!** 🚀📈
