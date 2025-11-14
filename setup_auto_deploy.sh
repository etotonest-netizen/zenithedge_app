#!/bin/bash
# Setup Git Post-Receive Hook for Auto-Deployment
# Run this once on your server to enable automatic deployments

echo "🔧 Setting up Git auto-deployment for ZenithEdge..."
echo ""

REPO_DIR="/home/equabish/zenithedge_app"
DEPLOY_DIR="/home/equabish/etotonest.com"

# Step 1: Make the deploy script executable
echo "1️⃣ Making deploy script executable..."
chmod +x $REPO_DIR/deploy.sh

# Step 2: Create a cron job for auto-pull every 5 minutes
echo "2️⃣ Setting up cron job for auto-deployment..."

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "zenithedge_app/deploy.sh"; then
    echo "   ⚠️  Cron job already exists. Skipping..."
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/equabish/zenithedge_app/deploy.sh >> /home/equabish/etotonest.com/logs/deploy.log 2>&1") | crontab -
    echo "   ✅ Cron job created! Will check for updates every 5 minutes."
fi

# Step 3: Create logs directory if it doesn't exist
echo "3️⃣ Creating logs directory..."
mkdir -p $DEPLOY_DIR/logs

# Step 4: Run first deployment
echo "4️⃣ Running initial deployment..."
$REPO_DIR/deploy.sh

echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "📋 What happens now:"
echo "   1. Every 5 minutes, the server checks GitHub for updates"
echo "   2. If updates found, automatically:"
echo "      - Pulls latest code"
echo "      - Syncs to $DEPLOY_DIR"
echo "      - Runs migrations"
echo "      - Collects static files"
echo "      - Restarts the application"
echo ""
echo "📝 Deployment logs: $DEPLOY_DIR/logs/deploy.log"
echo "🔧 Manual deploy: $REPO_DIR/deploy.sh"
echo ""
echo "🚀 Now when you push to GitHub, changes will appear on etotonest.com within 5 minutes!"
