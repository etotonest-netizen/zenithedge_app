#!/bin/bash
# Auto-Deploy Script for ZenithEdge
# This script pulls latest changes from GitHub and deploys to production

echo "🚀 ZenithEdge Auto-Deploy Script"
echo "=================================="
echo ""

# Configuration
REPO_DIR="/home/equabish/zenithedge_app"
DEPLOY_DIR="/home/equabish/etotonest.com"
BRANCH="main"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd $REPO_DIR || exit 1

echo "📦 Fetching latest changes from GitHub..."
git fetch origin

# Check if there are updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$BRANCH)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo -e "${GREEN}📥 New changes detected! Pulling updates...${NC}"
    git pull origin $BRANCH
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Git pull failed! Please resolve conflicts manually.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}📍 Git is up to date. Syncing files anyway...${NC}"
fi

echo "🔄 Syncing files to production directory..."
# Exclude git files, deployment packages, and cache
rsync -av --delete \
    --exclude='.git' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='db.sqlite3' \
    --exclude='.env' \
    --exclude='logs/' \
    --exclude='staticfiles/' \
    --exclude='media/' \
    $REPO_DIR/ $DEPLOY_DIR/

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Rsync failed!${NC}"
    exit 1
fi

echo "🔧 Running migrations (if any)..."
cd $DEPLOY_DIR
source /home/equabish/virtualenv/etotonest.com/3.11/bin/activate
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "♻️  Restarting application..."
touch passenger_wsgi.py

echo ""
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "🌐 Application restarted at: https://etotonest.com"
echo ""
echo "📊 Deployment Summary:"
echo "   From: $LOCAL (old)"
echo "   To:   $REMOTE (new)"
echo ""
