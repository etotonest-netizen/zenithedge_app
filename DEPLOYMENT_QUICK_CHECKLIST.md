# 🚀 Quick Deployment Checklist - Live Server

**Date:** November 14, 2025  
**Target:** etotonest.com (cPanel server)  
**Package Ready:** zenithedge_phase2_deployment.tar.gz (67KB)

---

## ✅ Pre-Deployment Checklist

- [ ] I have SSH access to server
- [ ] I have FTP/File Manager access (alternative to SSH)
- [ ] I know my server details:
  - Username: equabish
  - Host: etotonest.com
  - Path: /home/equabish/etotonest.com
- [ ] I have created a backup (or will do in Step 1)
- [ ] The deployment package is ready: zenithedge_phase2_deployment.tar.gz

---

## 📋 Deployment Steps (Choose Method A or B)

### Method A: SSH Upload (Recommended - Faster)

#### Step 1: Backup Current System on Server
```bash
# Connect to server
ssh equabish@etotonest.com

# Create backup
cd /home/equabish/etotonest.com
mkdir -p backups
tar -czf backups/backup_$(date +%Y%m%d_%H%M%S).tar.gz engine/ adapters/ zenithedge/urls.py
ls -lh backups/
exit
```

#### Step 2: Upload Package from Local Machine
```bash
# Run from your Mac terminal (in the zenithedge_trading_hub directory)
scp zenithedge_phase2_deployment.tar.gz equabish@etotonest.com:/home/equabish/etotonest.com/
```

#### Step 3: Extract on Server
```bash
# SSH back in
ssh equabish@etotonest.com

# Extract files
cd /home/equabish/etotonest.com
tar -xzf zenithedge_phase2_deployment.tar.gz
echo "✅ Files extracted"
ls -la engine/
```

#### Step 4: Run Migrations
```bash
# Activate virtual environment
source virtualenv/etotonest.com/3.11/bin/activate

# Run migrations
python manage.py makemigrations engine
python manage.py migrate engine
python manage.py migrate
```

#### Step 5: Restart Application
```bash
# Method 1: Touch wsgi file
touch passenger_wsgi.py

# Method 2: Or restart from cPanel Python App interface
echo "✅ Restart the Python app from cPanel if touch didn't work"
```

#### Step 6: Verify
```bash
# Test imports
python manage.py shell -c "from engine.backtest import BacktestEngine; print('✅ Backtest imported')"

# Check models
python manage.py shell -c "from engine.models import MarketBar; print('✅ Models OK')"

# List management commands
python manage.py --help | grep -E '(run_backtest|fetch_and_run)'
```

---

### Method B: File Manager Upload (If No SSH)

#### Step 1: Login to cPanel
- Go to: https://etotonest.com:2083
- Login with your credentials

#### Step 2: Navigate to File Manager
- Click "File Manager"
- Navigate to: /home/equabish/etotonest.com

#### Step 3: Create Backup
- Select folders: engine/, adapters/
- Click "Compress"
- Save as: backup_20251114.tar.gz in backups/ folder

#### Step 4: Upload Package
- Click "Upload"
- Select: zenithedge_phase2_deployment.tar.gz from your Mac
- Wait for upload to complete

#### Step 5: Extract Package
- Right-click on zenithedge_phase2_deployment.tar.gz
- Click "Extract"
- Extract to: /home/equabish/etotonest.com
- Confirm overwrite when asked

#### Step 6: Restart Python App
- Go to cPanel home
- Click "Setup Python App"
- Find your etotonest.com app
- Click "Restart"

#### Step 7: Run Migrations (Terminal in cPanel)
- In cPanel, click "Terminal"
- Run these commands:
```bash
cd /home/equabish/etotonest.com
source virtualenv/etotonest.com/3.11/bin/activate
python manage.py makemigrations engine
python manage.py migrate engine
python manage.py migrate
```

---

## 🧪 Post-Deployment Testing

### Test 1: Check Admin Interface
Visit: https://etotonest.com/admin/engine/
- [ ] Can see "Market bars" section
- [ ] Can see "Backtest runs" section
- [ ] Can see "Backtest trades" section

### Test 2: Test Management Commands
```bash
ssh equabish@etotonest.com
cd /home/equabish/etotonest.com
source virtualenv/etotonest.com/3.11/bin/activate
python manage.py run_backtest --help
python manage.py fetch_and_run --help
```

### Test 3: Test API Endpoints (if applicable)
Visit: https://etotonest.com/engine/api/status/?token=YOUR_TOKEN
- Should return JSON with system status

### Test 4: Check Logs
```bash
tail -f logs/zenithedge.log
# Look for any errors after restart
```

---

## 🔄 Optional: Setup Cron Jobs (Real-Time Data)

### In cPanel -> Cron Jobs:

**Frequency:** */5 * * * * (Every 5 minutes)

**Command:**
```bash
cd /home/equabish/etotonest.com && source virtualenv/etotonest.com/3.11/bin/activate && python manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1
```

This will automatically fetch market data and generate signals every 5 minutes.

---

## ⚠️ Troubleshooting

### If import errors occur:
```bash
# Reinstall requirements if needed
pip install -r requirements.txt
```

### If migrations fail:
```bash
# Check migration status
python manage.py showmigrations engine

# Try running individually
python manage.py migrate engine 0001 --fake
python manage.py migrate engine
```

### If app won't restart:
- Check error logs: tail -f logs/zenithedge.log
- Check passenger log: tail -f logs/passenger.log
- Verify Python path in cPanel Python App settings

### If permissions issues:
```bash
# Fix permissions
chmod -R 755 engine/
chmod -R 755 adapters/
```

---

## 📊 Success Criteria

After deployment, you should have:
- ✅ No error messages in logs
- ✅ Admin interface showing new engine sections
- ✅ Management commands available (run_backtest, fetch_and_run)
- ✅ API endpoints responding (if tested)
- ✅ Migrations applied successfully

---

## 🎉 You're Live!

Once all checks pass, your ZenithEdge Phase 2 is live on production!

**What's New in Phase 2:**
- ✅ All 10 strategy detectors (SMC, ICT, Trend, Breakout, etc.)
- ✅ Scoring integration with ZenBot
- ✅ Visual overlay generation
- ✅ Complete backtesting engine
- ✅ Real-time data pipeline (fetch_and_run)
- ✅ REST API endpoints
- ✅ 50+ test cases

**Documentation:**
- ENGINE_README.md - Complete reference
- ENGINE_QUICK_START.md - Quick start guide
- ENGINE_PHASE2_COMPLETE.md - Feature overview

**Future Enhancement:**
- ZenBrain orchestration system (see ZENBRAIN_ARCHITECTURE.md)
- Implement after gathering 1 month of user feedback

---

## 📞 Need Help?

If you encounter issues:
1. Check logs first: tail -f logs/zenithedge.log
2. Verify migrations: python manage.py showmigrations
3. Test imports: python manage.py shell
4. Review ENGINE_README.md troubleshooting section

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Status:** ⬜ In Progress  ⬜ Complete  ⬜ Issues Found
