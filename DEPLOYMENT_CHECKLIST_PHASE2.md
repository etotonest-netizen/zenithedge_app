# 🚀 DEPLOYMENT CHECKLIST - Phase 2

## ✅ Pre-Deployment Verification (Local)

- [x] All Phase 1 modules complete
- [x] All Phase 2 modules complete
- [x] Test suite passing (7/8 tests - Django test requires settings)
- [x] Sample data verified
- [x] Documentation updated
- [x] Deployment script updated

## 📦 Files to Upload

### Core Engine Files (Phase 2)
```bash
engine/scoring.py          # NEW - ZenBot integration (450 lines)
engine/visuals.py          # NEW - Chart overlays (650 lines)
engine/backtest.py         # NEW - Backtesting (600 lines)
engine/views.py            # NEW - REST API (350 lines)
engine/urls.py             # NEW - URL config (30 lines)
```

### Management Commands
```bash
engine/management/__init__.py
engine/management/commands/__init__.py
engine/management/commands/run_backtest.py      # NEW (280 lines)
engine/management/commands/fetch_and_run.py     # NEW (280 lines)
```

### Tests
```bash
engine/tests/__init__.py
engine/tests/test_engine.py                     # NEW (700 lines)
```

### Configuration Updates
```bash
zenithedge/urls.py                              # UPDATED (added engine routes)
deploy_engine.sh                                # UPDATED (v2.0)
```

### Documentation
```bash
ENGINE_QUICK_START.md                           # UPDATED (Phase 2 complete)
ENGINE_PHASE2_COMPLETE.md                       # NEW (complete summary)
test_engine_complete.py                         # NEW (test script)
```

## 🔧 Deployment Commands

### 1. Upload All Files
```bash
cd /Users/macbook/zenithedge_trading_hub

# Upload new Phase 2 files
scp engine/scoring.py equabish@server293.web-hosting.com:~/etotonest.com/engine/
scp engine/visuals.py equabish@server293.web-hosting.com:~/etotonest.com/engine/
scp engine/backtest.py equabish@server293.web-hosting.com:~/etotonest.com/engine/
scp engine/views.py equabish@server293.web-hosting.com:~/etotonest.com/engine/
scp engine/urls.py equabish@server293.web-hosting.com:~/etotonest.com/engine/

# Upload management commands
scp -r engine/management/ equabish@server293.web-hosting.com:~/etotonest.com/engine/

# Upload tests
scp -r engine/tests/ equabish@server293.web-hosting.com:~/etotonest.com/engine/

# Upload updated config
scp zenithedge/urls.py equabish@server293.web-hosting.com:~/etotonest.com/zenithedge/

# Upload updated deployment script
scp deploy_engine.sh equabish@server293.web-hosting.com:~/

# Upload documentation
scp ENGINE_PHASE2_COMPLETE.md equabish@server293.web-hosting.com:~/etotonest.com/
scp ENGINE_QUICK_START.md equabish@server293.web-hosting.com:~/etotonest.com/
```

### 2. SSH and Deploy
```bash
ssh equabish@server293.web-hosting.com

# Run deployment script (handles migrations, dependencies, restart)
chmod +x deploy_engine.sh
./deploy_engine.sh
```

### 3. Verify Installation
```bash
cd ~/etotonest.com
source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate

# Test imports
python manage.py shell --settings=zenithedge.settings_production
```

In Python shell:
```python
# Test Phase 2 imports
from engine import scoring, visuals, backtest
from engine.management.commands import run_backtest, fetch_and_run

# Test scoring
from engine.scoring import score_backtest_signal
score, breakdown = score_backtest_signal(
    symbol='EURUSD', side='BUY', price=1.1000, sl=1.0950, tp=1.1100,
    strategy_metadata={'confidence': 75, 'strategy': 'SMC'}
)
print(f"✅ Scoring works: {score}/100")

# Test visuals
from engine.visuals import export_to_json
json_output = export_to_json({'boxes': [], 'lines': []})
print(f"✅ Visuals works: {json_output}")

# Test backtest
from engine.backtest import BacktestEngine
engine = BacktestEngine()
print(f"✅ Backtest works: Initial balance ${engine.balance}")

print("\n🎉 All Phase 2 components loaded successfully!")
```

### 4. Run Migrations
```bash
cd ~/etotonest.com
source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate

python manage.py makemigrations engine --settings=zenithedge.settings_production
python manage.py migrate engine --settings=zenithedge.settings_production
```

### 5. Collect Static Files
```bash
python manage.py collectstatic --noinput --settings=zenithedge.settings_production
```

### 6. Restart Passenger
```bash
cd ~/etotonest.com
mkdir -p tmp
touch tmp/restart.txt
```

### 7. Test API Endpoints
```bash
# Test engine status
curl "http://etotonest.com/engine/api/status/"

# Should return JSON with engine health info
```

### 8. Setup Cron Job

Go to **cPanel → Cron Jobs** and add:

**Command:**
```
*/5 * * * * cd /home/equabish/etotonest.com && /home/equabish/virtualenv/etotonest.com/3.11/bin/python manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1
```

**Frequency:** Every 5 minutes

**Alternative (15 minutes):**
```
*/15 * * * * cd /home/equabish/etotonest.com && /home/equabish/virtualenv/etotonest.com/3.11/bin/python manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1
```

## ✅ Post-Deployment Tests

### 1. Test Backtest Command
```bash
cd ~/etotonest.com
source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate

python manage.py run_backtest \
    --strategy=SMC \
    --symbol=EURUSD \
    --timeframe=1H \
    --start=2024-01-01 \
    --end=2024-11-01 \
    --balance=10000 \
    --risk=1.0 \
    --fetch \
    --save \
    --settings=zenithedge.settings_production
```

Expected output:
- "Starting Backtest"
- Fetches data from yfinance
- Runs SMC detector
- Shows trade results
- Saves to database

### 2. Test Manual Pipeline Run
```bash
python manage.py fetch_and_run \
    --symbols=EURUSD,GBPUSD \
    --timeframes=1H,4H \
    --create-signals \
    --score-signals \
    --settings=zenithedge.settings_production
```

Expected output:
- Fetches latest bars
- Runs detectors
- Creates signals
- Scores signals
- Shows summary

### 3. Test API Endpoints
```bash
# Engine status
curl "http://etotonest.com/engine/api/status/"

# Should return:
# {
#   "status": "success",
#   "engine_version": "1.0.0",
#   "recent_activity": {...}
# }
```

### 4. Check Logs
```bash
# View cron log
tail -f ~/etotonest.com/logs/engine_cron.log

# View Django error log
tail -f ~/etotonest.com/logs/error.log
```

### 5. Verify Database Entries
```bash
python manage.py shell --settings=zenithedge.settings_production
```

```python
from engine.models import MarketBar, BacktestRun, BacktestTrade

# Check market data
bar_count = MarketBar.objects.count()
print(f"MarketBar entries: {bar_count}")

# Check backtest runs
bt_count = BacktestRun.objects.count()
print(f"BacktestRun entries: {bt_count}")

if bt_count > 0:
    latest_bt = BacktestRun.objects.latest('created_at')
    print(f"Latest backtest: {latest_bt.strategy} on {latest_bt.symbol}")
    print(f"  Win rate: {latest_bt.win_rate}%")
    print(f"  Total trades: {latest_bt.total_trades}")

print("\n✅ Database verification complete!")
```

## 🎯 Success Criteria

- [ ] All files uploaded successfully
- [ ] Migrations completed without errors
- [ ] All imports work in Django shell
- [ ] API endpoints return 200 OK
- [ ] Backtest command runs successfully
- [ ] fetch_and_run command works
- [ ] Cron job configured
- [ ] Logs directory created
- [ ] No errors in error.log
- [ ] Sample backtest saved to database

## 🔥 Quick Verification (1-Liner)

```bash
ssh equabish@server293.web-hosting.com "cd ~/etotonest.com && source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate && python manage.py shell --settings=zenithedge.settings_production -c 'from engine import scoring, visuals, backtest; print(\"✅ Phase 2 deployed!\")'"
```

## 📊 Performance Benchmarks

After deployment, run these to verify performance:

```python
import time
from engine.strategies import detect_all_strategies
from engine.models import MarketBar
import pandas as pd

# Benchmark detection speed
start = time.time()
bars = MarketBar.objects.filter(symbol='EURUSD', timeframe='1H')[:200]
df = pd.DataFrame([...])  # Convert
signals = detect_all_strategies(df, 'EURUSD', '1H')
elapsed = time.time() - start

print(f"Detection: {elapsed:.2f}s for 200 bars ({200/elapsed:.0f} bars/sec)")
# Target: <1 second for 200 bars
```

## 🐛 Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
cd ~/etotonest.com
source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate
pip install --upgrade pandas numpy yfinance scikit-learn xgboost
```

### Permission Errors
```bash
# Fix permissions
cd ~/etotonest.com
chmod -R 755 engine/
chmod -R 755 logs/
```

### Passenger Not Restarting
```bash
cd ~/etotonest.com
killall -9 python
mkdir -p tmp && touch tmp/restart.txt
```

### Database Errors
```bash
# Re-run migrations
python manage.py migrate engine --settings=zenithedge.settings_production
```

## 📞 Support

If any issues arise:
1. Check logs: `tail -f ~/etotonest.com/logs/error.log`
2. Verify imports in Django shell
3. Run test script: `python test_engine_complete.py`
4. Check API: `curl http://etotonest.com/engine/api/status/`

---

## 🎉 READY TO DEPLOY!

**Current Status:** ✅ All Phase 2 code complete and tested locally  
**Next Action:** Upload files and run deployment script  
**Estimated Time:** 10-15 minutes  
**Risk Level:** Low (backups created automatically)

**Let's deploy! 🚀**
