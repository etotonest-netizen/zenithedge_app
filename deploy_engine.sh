#!/bin/bash
#
# ZenithEdge Engine Deployment Script for cPanel (PHASE 2 COMPLETE)
# Deploys the complete trading engine to etotonest.com
# Includes: Scoring, Visuals, Backtesting, Pipeline, Tests
#

set -e  # Exit on error

echo "============================================"
echo "ZenithEdge Engine Deployment Script v2.0"
echo "PHASE 2: Complete Trading Platform"
echo "============================================"
echo ""

# Configuration
PROJECT_DIR="/home/equabish/etotonest.com"
VENV_DIR="/home/equabish/virtualenv/etotonest.com/3.11"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo "📂 Project Directory: $PROJECT_DIR"
echo "🐍 Python Environment: $VENV_DIR"
echo ""

# Step 1: Backup
echo "Step 1: Creating backup..."
BACKUP_DIR="$HOME/backups/zenithedge_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$PROJECT_DIR" "$BACKUP_DIR/"
echo "✅ Backup created at: $BACKUP_DIR"
echo ""

# Step 2: Upload engine files
echo "Step 2: Uploading engine files..."
cd "$PROJECT_DIR"

# Create engine directory if it doesn't exist
mkdir -p engine/migrations
mkdir -p engine/management/commands
mkdir -p engine/tests

# Create adapters directory
mkdir -p adapters/sample_data

echo "✅ Directory structure created"
echo ""

# Step 3: Install dependencies
echo "Step 3: Installing Python dependencies..."
source "$VENV_DIR/bin/activate"

$PIP install --upgrade pip
$PIP install pandas>=2.0.0
$PIP install numpy>=1.24.0
$PIP install yfinance>=0.2.28
$PIP install scikit-learn>=1.3.0
$PIP install xgboost>=1.7.0

echo "✅ Dependencies installed"
echo ""

# Step 4: Update settings
echo "Step 4: Updating Django settings..."

# Check if 'engine' is in INSTALLED_APPS
if ! grep -q "'engine'" "$PROJECT_DIR/zenithedge/settings.py"; then
    echo "Adding 'engine' to INSTALLED_APPS..."
    # This would need manual editing or a more sophisticated script
    echo "⚠️  MANUAL STEP REQUIRED: Add 'engine' to INSTALLED_APPS in zenithedge/settings.py"
else
    echo "✅ 'engine' already in INSTALLED_APPS"
fi
echo ""

# Step 5: Run migrations
echo "Step 5: Running database migrations..."
cd "$PROJECT_DIR"
$PYTHON manage.py makemigrations engine --settings=zenithedge.settings_production
$PYTHON manage.py migrate engine --settings=zenithedge.settings_production
echo "✅ Migrations completed"
echo ""

# Step 6: Collect static files
echo "Step 6: Collecting static files..."
$PYTHON manage.py collectstatic --noinput --settings=zenithedge.settings_production
echo "✅ Static files collected"
echo ""

# Step 7: Create logs directory
echo "Step 7: Setting up logs..."
mkdir -p "$PROJECT_DIR/logs"
touch "$PROJECT_DIR/logs/engine_cron.log"
touch "$PROJECT_DIR/logs/engine.log"
chmod 755 "$PROJECT_DIR/logs"
echo "✅ Log directories created"
echo ""

# Step 8: Test imports
echo "Step 8: Testing Python imports..."
$PYTHON << EOF
import sys
sys.path.insert(0, '$PROJECT_DIR')

try:
    from engine.models import MarketBar, BacktestRun, BacktestTrade
    print("✅ Models imported successfully")
    
    from engine.indicators import calculate_all_indicators
    print("✅ Indicators module imported successfully")
    
    from engine.smc import detect_smc
    print("✅ SMC module imported successfully")
    
    from engine.strategies import detect_all_strategies
    print("✅ Strategies module imported successfully")
    
    from adapters.tv_historical import fetch_historical_data
    print("✅ Adapters module imported successfully")
    
    print("\n🎉 All modules imported successfully!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
EOF
echo ""

# Step 9: Restart application
echo "Step 9: Restarting Passenger application..."
mkdir -p "$PROJECT_DIR/tmp"
touch "$PROJECT_DIR/tmp/restart.txt"
echo "✅ Application restart triggered"
echo ""

# Step 10: Setup cron job (display instructions)
echo "Step 10: Cron Job Setup Instructions"
echo "=========================================="
echo ""
echo "To setup the real-time processing cron job:"
echo "1. Go to cPanel → Cron Jobs"
echo "2. Add this cron job (runs every 5 minutes):"
echo ""
echo "*/5 * * * * cd $PROJECT_DIR && $PYTHON manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1"
echo ""
echo "Or for every minute (if allowed by hosting):"
echo "* * * * * cd $PROJECT_DIR && $PYTHON manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1"
echo ""
echo "=========================================="
echo ""

# Step 11: Verification
echo "Step 11: Running verification checks..."
echo ""

# Check database
echo "Checking database tables..."
$PYTHON manage.py dbshell --settings=zenithedge.settings_production << EOF
SELECT COUNT(*) as market_bars FROM engine_market_bar;
SELECT COUNT(*) as backtest_runs FROM engine_backtest_run;
SELECT COUNT(*) as backtest_trades FROM engine_backtest_trade;
EOF

echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "Next Steps:"
echo "1. Test the quick entry form: http://etotonest.com/signals/quick-entry/"
echo "2. Access Django admin: http://etotonest.com/admin/"
echo "3. Setup cron job as shown above"
echo "4. Monitor logs: tail -f $PROJECT_DIR/logs/engine_cron.log"
echo ""
echo "Test SMC Detection:"
echo "  cd $PROJECT_DIR"
echo "  $PYTHON manage.py shell --settings=zenithedge.settings_production"
echo "  >>> from engine.smc import detect_smc"
echo "  >>> import pandas as pd"
echo "  >>> df = pd.read_csv('adapters/sample_data/eurusd_1h.csv', parse_dates=['timestamp'], index_col='timestamp')"
echo "  >>> signals = detect_smc(df, 'EURUSD', '1H')"
echo "  >>> print(f'Detected {len(signals)} signals')"
echo ""
echo "Happy Trading! 🚀"
echo ""
