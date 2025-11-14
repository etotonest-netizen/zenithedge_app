#!/bin/bash
# Step-by-Step Deployment Guide for Live Server
# Date: November 14, 2025
# Purpose: Deploy ZenithEdge Phase 2 to production

echo "=================================================="
echo "ZenithEdge Phase 2 - Live Server Deployment Guide"
echo "=================================================="
echo ""
echo "⚠️  IMPORTANT: This guide assumes you have:"
echo "   1. SSH access to your server"
echo "   2. Your server details (host, username, path)"
echo "   3. Created backup of current system"
echo ""

# Server details (UPDATE THESE)
SERVER_USER="equabish"
SERVER_HOST="etotonest.com"
SERVER_PATH="/home/equabish/etotonest.com"

echo "Current Configuration:"
echo "  Server: $SERVER_USER@$SERVER_HOST"
echo "  Path: $SERVER_PATH"
echo ""

# ============================================================
# STEP 1: BACKUP CURRENT PRODUCTION
# ============================================================
echo "STEP 1: Backup Current Production"
echo "=================================================="
echo ""
echo "Before uploading anything, let's backup the live server:"
echo ""
echo "SSH Command to run on server:"
echo "  ssh $SERVER_USER@$SERVER_HOST"
echo ""
echo "Once connected, run these commands:"
echo ""
echo "  cd $SERVER_PATH"
echo "  mkdir -p backups"
echo "  tar -czf backups/backup_\$(date +%Y%m%d_%H%M%S).tar.gz engine/ adapters/ zenithedge/urls.py"
echo "  ls -lh backups/"
echo ""
echo "✅ After backup completes, press Enter to continue..."
read

# ============================================================
# STEP 2: UPLOAD DEPLOYMENT PACKAGE
# ============================================================
echo ""
echo "STEP 2: Upload Deployment Package"
echo "=================================================="
echo ""
echo "Now let's upload the new files to server:"
echo ""
echo "Command to run from your local machine:"
echo ""
echo "  scp zenithedge_phase2_deployment.tar.gz $SERVER_USER@$SERVER_HOST:$SERVER_PATH/"
echo ""
echo "This will upload the 67KB package to your server."
echo ""
echo "Copy and paste this command into a new terminal window:"
echo "---"
echo "scp zenithedge_phase2_deployment.tar.gz $SERVER_USER@$SERVER_HOST:$SERVER_PATH/"
echo "---"
echo ""
echo "✅ After upload completes, press Enter to continue..."
read

# ============================================================
# STEP 3: EXTRACT ON SERVER
# ============================================================
echo ""
echo "STEP 3: Extract Files on Server"
echo "=================================================="
echo ""
echo "SSH back into your server and extract the files:"
echo ""
echo "Commands to run on server:"
echo ""
echo "  ssh $SERVER_USER@$SERVER_HOST"
echo "  cd $SERVER_PATH"
echo "  tar -xzf zenithedge_phase2_deployment.tar.gz"
echo "  echo '✅ Files extracted'"
echo "  ls -la engine/"
echo ""
echo "This will overwrite old files with new Phase 2 files."
echo ""
echo "✅ After extraction completes, press Enter to continue..."
read

# ============================================================
# STEP 4: RUN MIGRATIONS
# ============================================================
echo ""
echo "STEP 4: Run Database Migrations"
echo "=================================================="
echo ""
echo "Still on the server, activate virtual environment and run migrations:"
echo ""
echo "Commands to run on server:"
echo ""
echo "  cd $SERVER_PATH"
echo "  source virtualenv/etotonest.com/3.11/bin/activate"
echo "  python manage.py makemigrations engine"
echo "  python manage.py migrate engine"
echo "  python manage.py migrate"
echo ""
echo "✅ After migrations complete, press Enter to continue..."
read

# ============================================================
# STEP 5: COLLECT STATIC FILES
# ============================================================
echo ""
echo "STEP 5: Collect Static Files (if needed)"
echo "=================================================="
echo ""
echo "If you have static files, collect them:"
echo ""
echo "Commands to run on server:"
echo ""
echo "  python manage.py collectstatic --noinput"
echo ""
echo "✅ Press Enter to continue..."
read

# ============================================================
# STEP 6: RESTART APPLICATION
# ============================================================
echo ""
echo "STEP 6: Restart Application"
echo "=================================================="
echo ""
echo "For cPanel Python app, touch the wsgi file to reload:"
echo ""
echo "Commands to run on server:"
echo ""
echo "  touch passenger_wsgi.py"
echo "  echo '✅ Application restarted'"
echo ""
echo "Or restart from cPanel -> Python App -> Restart"
echo ""
echo "✅ After restart, press Enter to continue..."
read

# ============================================================
# STEP 7: VERIFY DEPLOYMENT
# ============================================================
echo ""
echo "STEP 7: Verify Deployment"
echo "=================================================="
echo ""
echo "Test the deployment by running these checks on server:"
echo ""
echo "1. Test imports:"
echo "   python manage.py shell -c \"from engine.backtest import BacktestEngine; print('✅ Backtest imported')\""
echo ""
echo "2. Check models:"
echo "   python manage.py shell -c \"from engine.models import MarketBar; print(f'MarketBar count: {MarketBar.objects.count()}')\""
echo ""
echo "3. Test management command:"
echo "   python manage.py --help | grep -E '(run_backtest|fetch_and_run)'"
echo ""
echo "4. Check admin:"
echo "   Visit: https://etotonest.com/admin/engine/"
echo ""
echo "✅ After verification, press Enter to continue..."
read

# ============================================================
# STEP 8: SETUP CRON JOBS (OPTIONAL)
# ============================================================
echo ""
echo "STEP 8: Setup Cron Jobs (Optional - For Real-Time Data)"
echo "=================================================="
echo ""
echo "If you want real-time market data processing, add this cron job:"
echo ""
echo "In cPanel -> Cron Jobs, add:"
echo ""
echo "*/5 * * * * cd $SERVER_PATH && source virtualenv/etotonest.com/3.11/bin/activate && python manage.py fetch_and_run --settings=zenithedge.settings_production >> logs/engine_cron.log 2>&1"
echo ""
echo "This runs every 5 minutes to fetch market data and generate signals."
echo ""
echo "✅ Press Enter when done..."
read

# ============================================================
# COMPLETE
# ============================================================
echo ""
echo "=================================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Your ZenithEdge Phase 2 is now live!"
echo ""
echo "📊 Next Steps:"
echo "  1. Test API endpoints (see ENGINE_QUICK_START.md)"
echo "  2. Monitor logs for 24 hours"
echo "  3. Test backtest command: python manage.py run_backtest --help"
echo "  4. Test real-time pipeline (if cron setup)"
echo ""
echo "📚 Documentation:"
echo "  - ENGINE_README.md - Complete reference"
echo "  - ENGINE_QUICK_START.md - Quick testing guide"
echo "  - ENGINE_PHASE2_COMPLETE.md - Feature summary"
echo ""
echo "🧠 Future Enhancement:"
echo "  - Review ZENBRAIN_ARCHITECTURE.md when ready"
echo "  - Consider implementing after 1 month of user feedback"
echo ""
echo "=================================================="
echo "System Status: ✅ PRODUCTION READY"
echo "=================================================="
