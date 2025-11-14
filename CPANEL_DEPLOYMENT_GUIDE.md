# ZenithEdge cPanel Deployment Guide

## Complete Step-by-Step Guide for Production Deployment on z.equatorfoods.org

This guide covers deploying the entire ZenithEdge Django system on Namecheap cPanel shared hosting with live TradingView webhook integration.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Step 1: Prepare Files Locally](#step-1-prepare-files-locally)
4. [Step 2: Upload Files to cPanel](#step-2-upload-files-to-cpanel)
5. [Step 3: Create MySQL Database](#step-3-create-mysql-database)
6. [Step 4: Configure Python Application](#step-4-configure-python-application)
7. [Step 5: Install Dependencies](#step-5-install-dependencies)
8. [Step 6: Configure Environment Variables](#step-6-configure-environment-variables)
9. [Step 7: Run Database Migrations](#step-7-run-database-migrations)
10. [Step 8: Collect Static Files](#step-8-collect-static-files)
11. [Step 9: Create Superuser](#step-9-create-superuser)
12. [Step 10: Configure Webhook](#step-10-configure-webhook)
13. [Step 11: Setup Cron Job](#step-11-setup-cron-job)
14. [Step 12: Test the System](#step-12-test-the-system)
15. [Troubleshooting](#troubleshooting)
16. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### What You Need:
- ✅ Namecheap cPanel access for z.equatorfoods.org
- ✅ SSH access (or Terminal in cPanel)
- ✅ Python 3.9+ support on hosting
- ✅ MySQL database access
- ✅ TradingView account (for webhook testing)
- ✅ Local copy of ZenithEdge project

### Hosting Requirements:
- Python 3.9 or higher
- MySQL 5.7 or higher
- At least 1GB disk space
- Support for Passenger WSGI
- Cron job capability
- SSL certificate (AutoSSL recommended)

---

## Pre-Deployment Checklist

Before uploading files, complete these tasks locally:

### 1. Generate Secret Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
**Save this key** - you'll need it for environment variables.

### 2. Generate Webhook Token
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
**Save this token** - you'll need it for TradingView webhook configuration.

### 3. Verify Files Exist
```bash
# Check these critical files exist:
- passenger_wsgi.py
- zenithedge/settings_production.py
- signals/tradingview_webhook.py
- signals/management/commands/process_signals.py
- signals/migrations/0009_add_webhook_tracking_fields.py
- requirements.txt
```

### 4. Test Locally
```bash
# Set environment variable to use production settings
export DJANGO_SETTINGS_MODULE=zenithedge.settings_production
export DEBUG=False
export DJANGO_SECRET_KEY="your-generated-secret-key"
export DB_NAME=test_db
export DB_USER=test_user
export DB_PASSWORD=test_pass
export WEBHOOK_TOKEN="your-generated-token"

# Run checks
python manage.py check --deploy
```

---

## Step 1: Prepare Files Locally

### 1.1 Create Deployment Archive
```bash
cd /path/to/zenithedge_trading_hub

# Exclude unnecessary files
tar -czf zenithedge_deploy.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='db.sqlite3' \
  --exclude='venv' \
  --exclude='staticfiles' \
  --exclude='logs/*.log' \
  --exclude='.env' \
  --exclude='*.swp' \
  --exclude='.DS_Store' \
  .
```

### 1.2 Verify Archive Contents
```bash
tar -tzf zenithedge_deploy.tar.gz | head -20
```

Should see:
- passenger_wsgi.py
- manage.py
- requirements.txt
- zenithedge/
- signals/
- etc.

---

## Step 2: Upload Files to cPanel

### Option A: Using cPanel File Manager

1. **Login to cPanel** at https://server.equatorfoods.org:2083
2. Navigate to **File Manager**
3. Go to home directory (usually `/home/username/`)
4. Create directory: **Click "New Folder"** → Name it `zenithedge_trading_hub`
5. Enter the `zenithedge_trading_hub` directory
6. **Upload** the `zenithedge_deploy.tar.gz` file
7. Select the file → **Extract**
8. Delete the .tar.gz file after extraction

### Option B: Using SSH/SFTP

```bash
# Using SCP
scp zenithedge_deploy.tar.gz username@z.equatorfoods.org:~/

# SSH into server
ssh username@z.equatorfoods.org

# Extract files
cd ~
mkdir -p zenithedge_trading_hub
cd zenithedge_trading_hub
tar -xzf ../zenithedge_deploy.tar.gz
rm ../zenithedge_deploy.tar.gz
```

### 2.1 Verify Upload
```bash
ls -la
# Should see:
# passenger_wsgi.py
# manage.py
# requirements.txt
# zenithedge/
# signals/
# etc.
```

---

## Step 3: Create MySQL Database

### 3.1 Access MySQL Database Wizard

1. In cPanel, go to **MySQL® Database Wizard**
2. Or go to **MySQL® Databases** for manual setup

### 3.2 Create Database

**Step 1: Create Database**
- Database Name: `zenithedge_db` (cPanel will prefix with username)
- Click **Next Step**

**Step 2: Create Database User**
- Username: `zenithedge_user`
- Password: Generate strong password (save it!)
- Click **Create User**

**Step 3: Grant Privileges**
- Check **ALL PRIVILEGES**
- Click **Next Step**

### 3.3 Record Database Credentials

```plaintext
Database Name: username_zenithedge_db
Database User: username_zenithedge_user
Database Password: [your-generated-password]
Database Host: localhost
Database Port: 3306
```

**IMPORTANT:** Save these credentials securely!

---

## Step 4: Configure Python Application

### 4.1 Access Setup Python App

1. In cPanel, search for **"Setup Python App"** or **"Python"**
2. Click **Setup Python App** or **Create Application**

### 4.2 Create New Application

**Fill in these details:**

| Field | Value |
|-------|-------|
| **Python version** | 3.9.x or higher (latest available) |
| **Application root** | `/home/username/zenithedge_trading_hub` |
| **Application URL** | `z.equatorfoods.org` or `/` (root domain) |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |
| **Passenger log file** | `logs/passenger.log` |

### 4.3 Configure Passenger

The `passenger_wsgi.py` file automatically handles:
- ✅ Project root detection
- ✅ Python path configuration
- ✅ Settings module detection
- ✅ Error handling with helpful error pages

**No manual Passenger configuration needed!**

---

## Step 5: Install Dependencies

### 5.1 Access Terminal

Option A: **cPanel Terminal** (if available)
Option B: **SSH** to the server

### 5.2 Navigate to Project
```bash
cd ~/zenithedge_trading_hub
```

### 5.3 Activate Virtual Environment

cPanel creates a virtual environment automatically. Activate it:

```bash
# cPanel typically creates venv at this path:
source /home/username/virtualenv/zenithedge_trading_hub/3.9/bin/activate

# Or find it with:
find ~ -name "activate" | grep zenithedge
```

### 5.4 Install Requirements

```bash
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This may take 5-10 minutes
# Note: Uses PyMySQL (pure Python) instead of mysqlclient (requires compilation)
```

**If you see "Failed to build mysqlclient":**
- ✅ **This is expected and already handled!**
- The requirements.txt uses **PyMySQL** instead - a pure Python MySQL driver
- PyMySQL works perfectly on shared hosting (no compilation needed)
- Continue with the next step

### 5.5 Verify Installation

```bash
pip list | grep -i django
# Should show: Django 4.2.7

pip list | grep -i pymysql
# Should show: PyMySQL 1.1.0


python -c "import django; print(django.VERSION)"
# Should show: (4, 2, 7, 'final', 0)
```

---

## Step 6: Configure Environment Variables

### 6.1 Method A: Using cPanel Python App Interface

1. Go to **Setup Python App** in cPanel
2. Click **Edit** on your zenithedge_trading_hub app
3. Scroll to **Environment variables** section
4. Add these variables one by one:

### Required Environment Variables:

```plaintext
DJANGO_SETTINGS_MODULE=zenithedge.settings_production

DJANGO_SECRET_KEY=[paste your generated secret key]

DB_NAME=username_zenithedge_db
DB_USER=username_zenithedge_user
DB_PASSWORD=[your database password]
DB_HOST=localhost
DB_PORT=3306

WEBHOOK_TOKEN=[paste your generated webhook token]

DEBUG=False
ALLOWED_HOSTS=z.equatorfoods.org,www.z.equatorfoods.org
```

### Optional Environment Variables:

```plaintext
WEBHOOK_RATE_LIMIT=10
EMAIL_HOST=mail.equatorfoods.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@z.equatorfoods.org
```

### 6.2 Method B: Using .env File (Backup Method)

If cPanel doesn't support environment variables directly:

```bash
cd ~/zenithedge_trading_hub

cat > .env << 'EOF'
DJANGO_SETTINGS_MODULE=zenithedge.settings_production
DJANGO_SECRET_KEY=your-generated-secret-key-here
DB_NAME=username_zenithedge_db
DB_USER=username_zenithedge_user
DB_PASSWORD=your-database-password-here
DB_HOST=localhost
DB_PORT=3306
WEBHOOK_TOKEN=your-generated-webhook-token-here
DEBUG=False
EOF

# Secure the file
chmod 600 .env
```

### 6.3 Verify Environment

```bash
# Test that settings load correctly
python manage.py check --settings=zenithedge.settings_production

# Should show:
# System check identified no issues (0 silenced).
```

---

## Step 7: Run Database Migrations

### 7.1 Create Logs Directory

```bash
cd ~/zenithedge_trading_hub
mkdir -p logs
chmod 755 logs
```

### 7.2 Run Migrations

```bash
# Make sure virtual environment is activated
source /home/username/virtualenv/zenithedge_trading_hub/3.9/bin/activate

# Run migrations
python manage.py migrate --settings=zenithedge.settings_production

# Expected output:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   Applying accounts.0001_initial... OK
#   Applying signals.0001_initial... OK
#   ... (many more migrations)
#   Applying signals.0009_add_webhook_tracking_fields... OK
```

### 7.3 Verify Database

```bash
# Check tables were created
python manage.py dbshell --settings=zenithedge.settings_production

# In MySQL prompt:
SHOW TABLES;
# Should show 50+ tables

# Check signals table has new fields
DESCRIBE signals_signal;
# Should show raw_data, source_ip, user_agent, status fields

# Exit MySQL
exit
```

---

## Step 8: Collect Static Files

### 8.1 Create Public Directory

```bash
cd ~/zenithedge_trading_hub
mkdir -p public/static
chmod 755 public
chmod 755 public/static
```

### 8.2 Collect Static Files

```bash
python manage.py collectstatic --noinput --settings=zenithedge.settings_production

# Output:
# Copying '...'
# ... (many files)
# 542 static files copied to '/home/username/zenithedge_trading_hub/public/static'.
```

### 8.3 Configure Static File Serving in cPanel

1. Go to **File Manager**
2. Navigate to `public_html` (or your domain's document root)
3. Create symbolic link or setup redirect to `/home/username/zenithedge_trading_hub/public/static`

**Alternative:** Let Passenger serve static files (automatic if configured correctly)

---

## Step 9: Create Superuser

### 9.1 Create Admin Account

```bash
python manage.py createsuperuser --settings=zenithedge.settings_production

# Prompts:
Email: admin@equatorfoods.org
Password: [enter secure password]
Password (again): [repeat password]

# Output:
# Superuser created successfully.
```

### 9.2 Create API Key for Testing

```bash
python manage.py shell --settings=zenithedge.settings_production
```

```python
from accounts.models import CustomUser
import secrets

# Get your superuser
user = CustomUser.objects.get(email='admin@equatorfoods.org')

# Generate API key
api_key = secrets.token_urlsafe(32)
user.api_key = api_key
user.save()

print(f"API Key: {api_key}")
# Save this API key for testing!

exit()
```

---

## Step 10: Configure Webhook

### 10.1 Verify Webhook Endpoint is Accessible

```bash
curl -I https://z.equatorfoods.org/api/signals/webhook/health/

# Expected response:
# HTTP/2 200
# content-type: application/json
# {"status": "healthy", "service": "ZenithEdge TradingView Webhook", ...}
```

### 10.2 Test Webhook with Token

```bash
# Replace YOUR_TOKEN with your WEBHOOK_TOKEN value
curl -X POST "https://z.equatorfoods.org/api/signals/webhook/test/?token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0850,
    "tp": 1.0950,
    "confidence": 85.5,
    "strategy": "ZenithEdge",
    "regime": "Trending"
  }'

# Expected response:
# {"status": "success", "message": "Test webhook received successfully", ...}
```

### 10.3 Test Full Webhook (Creates Signal)

```bash
curl -X POST "https://z.equatorfoods.org/api/signals/webhook/?token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0850,
    "tp": 1.0950,
    "confidence": 85.5,
    "strategy": "ZenithEdge",
    "regime": "Trending",
    "price": 1.0900
  }'

# Expected response:
# {"status": "success", "signal_id": 1, "message": "Signal received and queued for processing", ...}
```

### 10.4 Check Webhook Logs

```bash
tail -f ~/zenithedge_trading_hub/logs/webhook.log

# Should show:
# INFO ============================================================
# INFO 📡 WEBHOOK REQUEST RECEIVED
# INFO IP: [your IP]
# INFO ✅ Token validated
# INFO ✅ Signal saved: ID=1
```

---

## Step 11: Setup Cron Job

### 11.1 Access Cron Jobs in cPanel

1. Go to **Advanced** → **Cron Jobs**
2. Or search for "Cron Jobs" in cPanel

### 11.2 Add Cron Job for Signal Processing

**Settings:**
- **Minute:** `*/5` (every 5 minutes)
- **Hour:** `*` (every hour)
- **Day:** `*` (every day)
- **Month:** `*` (every month)
- **Weekday:** `*` (every weekday)

**Command:**
```bash
cd /home/username/zenithedge_trading_hub && /home/username/virtualenv/zenithedge_trading_hub/3.9/bin/python manage.py process_signals --settings=zenithedge.settings_production >> logs/cron.log 2>&1
```

**Alternative (if path is different):**
```bash
cd ~/zenithedge_trading_hub && source ~/virtualenv/zenithedge_trading_hub/3.9/bin/activate && python manage.py process_signals >> logs/cron.log 2>&1
```

### 11.3 Test Cron Job Manually

```bash
cd ~/zenithedge_trading_hub
source ~/virtualenv/zenithedge_trading_hub/3.9/bin/activate
python manage.py process_signals --settings=zenithedge.settings_production

# Output:
# ======================================================================
# 🔄 SIGNAL PROCESSING STARTED
# Timestamp: 2025-11-13T18:00:00+00:00
# ======================================================================
# 📊 Found 1 pending signals to process
# ...
```

### 11.4 Monitor Cron Logs

```bash
tail -f ~/zenithedge_trading_hub/logs/cron.log
```

---

## Step 12: Test the System

### 12.1 Restart Passenger Application

**In cPanel:**
1. Go to **Setup Python App**
2. Find your `zenithedge_trading_hub` app
3. Click **Restart** button
4. Wait for "Application restarted successfully" message

**Via SSH:**
```bash
touch ~/zenithedge_trading_hub/passenger_wsgi.py
# Or
touch ~/zenithedge_trading_hub/tmp/restart.txt
```

### 12.2 Access Admin Panel

1. Open browser: https://z.equatorfoods.org/admin/
2. Login with superuser credentials
3. Verify you can see:
   - ✅ Signals
   - ✅ Users
   - ✅ All apps loaded

### 12.3 Access Dashboard

1. Navigate to: https://z.equatorfoods.org/signals/dashboard/
2. Should see dashboard (may need to login first)
3. Verify UI loads correctly

### 12.4 Test TradingView Webhook

**Setup TradingView Alert:**

1. Go to TradingView.com
2. Create an alert on any chart
3. In Alert setup:
   - **Webhook URL:** `https://z.equatorfoods.org/api/signals/webhook/?token=YOUR_WEBHOOK_TOKEN`
   - **Message:** 
   ```json
   {
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "side": "buy",
     "sl": {{low}},
     "tp": {{high}},
     "confidence": 85.0,
     "strategy": "ZenithEdge",
     "regime": "Trending",
     "price": {{close}}
   }
   ```

4. **Test the alert** - should trigger webhook
5. **Check logs:**
   ```bash
   tail -20 ~/zenithedge_trading_hub/logs/webhook.log
   ```

6. **Check database:**
   ```bash
   python manage.py shell --settings=zenithedge.settings_production
   ```
   ```python
   from signals.models import Signal
   Signal.objects.count()  # Should be > 0
   Signal.objects.latest('received_at')  # See latest signal
   ```

### 12.5 Verify Signal Processing

```bash
# Manually trigger processing
python manage.py process_signals --settings=zenithedge.settings_production

# Check signal status
python manage.py shell --settings=zenithedge.settings_production
```
```python
from signals.models import Signal
signal = Signal.objects.latest('received_at')
print(f"Status: {signal.status}")  # Should be 'processed'
print(f"AI Score: {signal.raw_data.get('ai_score')}")
```

---

## Troubleshooting

### Issue: Application Won't Start

**Symptoms:**
- 500 Internal Server Error
- "Application failed to start"

**Solutions:**

1. **Check Passenger error log:**
   ```bash
   tail -50 ~/zenithedge_trading_hub/logs/passenger.log
   ```

2. **Check Python syntax:**
   ```bash
   python -m py_compile passenger_wsgi.py
   python -m py_compile zenithedge/settings_production.py
   ```

3. **Verify settings module:**
   ```bash
   python -c "import zenithedge.settings_production; print('OK')"
   ```

4. **Check environment variables:**
   ```bash
   python manage.py check --settings=zenithedge.settings_production
   ```

### Issue: Database Connection Errors

**Symptoms:**
- "Can't connect to MySQL server"
- "Access denied for user"

**Solutions:**

1. **Verify database credentials:**
   ```bash
   mysql -h localhost -u username_zenithedge_user -p username_zenithedge_db
   # Enter password when prompted
   ```

2. **Check environment variables are set:**
   ```bash
   echo $DB_NAME
   echo $DB_USER
   # Should show your database name and user
   ```

3. **Test MySQL connection in Python:**
   ```python
   import MySQLdb
   db = MySQLdb.connect(
       host='localhost',
       user='username_zenithedge_user',
       passwd='your-password',
       db='username_zenithedge_db'
   )
   print("Connected!")
   ```

### Issue: Webhook Returns 403 Forbidden

**Symptoms:**
- TradingView webhook fails
- curl returns `{"status": "error", "message": "Invalid token"}`

**Solutions:**

1. **Verify token is set:**
   ```bash
   echo $WEBHOOK_TOKEN
   ```

2. **Check token in settings:**
   ```bash
   python manage.py shell --settings=zenithedge.settings_production
   ```
   ```python
   from django.conf import settings
   print(f"Token set: {bool(settings.WEBHOOK_TOKEN)}")
   ```

3. **Test with correct token:**
   ```bash
   curl -X POST "https://z.equatorfoods.org/api/signals/webhook/test/?token=YOUR_ACTUAL_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### Issue: Static Files Not Loading

**Symptoms:**
- Dashboard shows no CSS/images
- 404 errors in browser console

**Solutions:**

1. **Re-run collectstatic:**
   ```bash
   python manage.py collectstatic --clear --noinput --settings=zenithedge.settings_production
   ```

2. **Check file permissions:**
   ```bash
   chmod -R 755 public/static
   ```

3. **Verify STATIC_ROOT:**
   ```bash
   python manage.py shell --settings=zenithedge.settings_production
   ```
   ```python
   from django.conf import settings
   print(settings.STATIC_ROOT)
   # Should be: /home/username/zenithedge_trading_hub/public/static
   ```

### Issue: Cron Job Not Running

**Symptoms:**
- Signals stay in 'pending' status
- No entries in cron.log

**Solutions:**

1. **Check cron job is set:**
   ```bash
   crontab -l | grep zenithedge
   ```

2. **Test command manually:**
   ```bash
   cd ~/zenithedge_trading_hub && python manage.py process_signals >> logs/cron_test.log 2>&1
   cat logs/cron_test.log
   ```

3. **Check Python path in cron:**
   ```bash
   which python
   # Use this path in cron command
   ```

4. **Add logging to cron:**
   ```bash
   */5 * * * * echo "Cron running at $(date)" >> ~/cron_debug.log && cd ~/zenithedge_trading_hub && python manage.py process_signals >> logs/cron.log 2>&1
   ```

---

## Monitoring & Maintenance

### Daily Checks

```bash
# Check webhook logs
tail -20 ~/zenithedge_trading_hub/logs/webhook.log

# Check error logs
tail -20 ~/zenithedge_trading_hub/logs/error.log

# Check signal count
python manage.py shell --settings=zenithedge.settings_production
```
```python
from signals.models import Signal
from django.utils import timezone
from datetime import timedelta

# Signals today
today = timezone.now().date()
today_count = Signal.objects.filter(received_at__date=today).count()
print(f"Signals today: {today_count}")

# Pending signals
pending = Signal.objects.filter(status='pending').count()
print(f"Pending: {pending}")

# Processing errors
failed = Signal.objects.filter(status='failed').count()
print(f"Failed: {failed}")
```

### Weekly Maintenance

```bash
# Rotate logs
cd ~/zenithedge_trading_hub/logs
for log in *.log; do
  if [ -f "$log" ]; then
    mv "$log" "$log.$(date +%Y%m%d)"
    gzip "$log.$(date +%Y%m%d)"
  fi
done

# Clean old logs (keep last 30 days)
find logs/ -name "*.log.*.gz" -mtime +30 -delete
```

### Performance Monitoring

```bash
# Database size
python manage.py shell --settings=zenithedge.settings_production
```
```python
from signals.models import Signal, MarketInsight
print(f"Total signals: {Signal.objects.count()}")
print(f"Total insights: {MarketInsight.objects.count()}")

# Check for old data
from datetime import timedelta
from django.utils import timezone
old_date = timezone.now() - timedelta(days=90)
old_signals = Signal.objects.filter(received_at__lt=old_date).count()
print(f"Signals older than 90 days: {old_signals}")
```

### Backup Strategy

```bash
# Backup database
mysqldump -u username_zenithedge_user -p username_zenithedge_db > backup_$(date +%Y%m%d).sql
gzip backup_$(date +%Y%m%d).sql

# Backup files
cd ~
tar -czf zenithedge_backup_$(date +%Y%m%d).tar.gz zenithedge_trading_hub/

# Download backups via SFTP or store in cPanel backups
```

---

## Quick Reference Commands

### Restart Application
```bash
touch ~/zenithedge_trading_hub/passenger_wsgi.py
```

### View Recent Logs
```bash
tail -f ~/zenithedge_trading_hub/logs/webhook.log
tail -f ~/zenithedge_trading_hub/logs/zenithedge.log
tail -f ~/zenithedge_trading_hub/logs/error.log
```

### Check Signal Status
```bash
cd ~/zenithedge_trading_hub
python manage.py shell --settings=zenithedge.settings_production
```
```python
from signals.models import Signal
Signal.objects.filter(status='pending').count()
Signal.objects.filter(status='processed').count()
Signal.objects.latest('received_at')
```

### Manual Signal Processing
```bash
cd ~/zenithedge_trading_hub
python manage.py process_signals --settings=zenithedge.settings_production
```

### Test Webhook
```bash
curl -X POST "https://z.equatorfoods.org/api/signals/webhook/?token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","timeframe":"1H","side":"buy","sl":1.0850,"tp":1.0950,"confidence":85.5,"strategy":"ZenithEdge","regime":"Trending","price":1.0900}'
```

---

## Success Checklist

After completing all steps, verify:

- ✅ Application accessible at https://z.equatorfoods.org
- ✅ Admin panel works: https://z.equatorfoods.org/admin/
- ✅ Dashboard loads: https://z.equatorfoods.org/signals/dashboard/
- ✅ Webhook health check returns 200: https://z.equatorfoods.org/api/signals/webhook/health/
- ✅ Test webhook succeeds with token
- ✅ Signals appear in database after webhook POST
- ✅ Cron job processes signals every 5 minutes
- ✅ Logs show activity in webhook.log and cron.log
- ✅ No errors in error.log
- ✅ SSL certificate active (HTTPS working)

---

## Support & Resources

### Documentation
- Django Docs: https://docs.djangoproject.com/en/4.2/
- Passenger Docs: https://www.phusionpassenger.com/docs/
- TradingView Webhooks: https://www.tradingview.com/support/solutions/43000529348/

### Logs Location
- Application: `~/zenithedge_trading_hub/logs/zenithedge.log`
- Webhook: `~/zenithedge_trading_hub/logs/webhook.log`
- Passenger: `~/zenithedge_trading_hub/logs/passenger.log`
- Cron: `~/zenithedge_trading_hub/logs/cron.log`
- Errors: `~/zenithedge_trading_hub/logs/error.log`

### cPanel Resources
- Python App Setup: cPanel → Software → Setup Python App
- MySQL Databases: cPanel → Databases → MySQL® Databases
- Cron Jobs: cPanel → Advanced → Cron Jobs
- File Manager: cPanel → Files → File Manager
- Terminal: cPanel → Advanced → Terminal

---

## Deployment Complete! 🎉

Your ZenithEdge system is now live on z.equatorfoods.org with:
- ✅ Secure webhook endpoint at /api/signals/webhook/
- ✅ Token-based authentication
- ✅ MySQL database storage
- ✅ Automatic signal processing via cron
- ✅ Full AI pipeline integration
- ✅ Real-time dashboard
- ✅ Production-ready logging

**Next Steps:**
1. Configure your TradingView indicators to send webhooks
2. Monitor logs for incoming signals
3. Review dashboard for signal insights
4. Setup regular backups
5. Monitor performance and optimize as needed

**Happy Trading! 📈**
