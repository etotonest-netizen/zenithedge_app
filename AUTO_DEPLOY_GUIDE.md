# 🚀 Git Auto-Deployment Setup Guide

This guide sets up automatic deployment from GitHub to your production server.

## 📋 What This Does

When you push code to GitHub, your server will:
1. **Auto-detect** changes every 5 minutes
2. **Pull** latest code from GitHub
3. **Sync** files to `/home/equabish/etotonest.com`
4. **Run** migrations automatically
5. **Restart** the application
6. **Log** everything for debugging

## 🎯 One-Time Setup (On Your Server)

### Step 1: Commit and push the deployment scripts

```bash
# On your local machine
git add deploy.sh setup_auto_deploy.sh
git commit -m "Add auto-deployment scripts"
git push origin main
```

### Step 2: Setup on server

```bash
# SSH into your server
ssh equabish@server293.web-hosting.com

# Navigate to the cloned repo
cd ~/zenithedge_app

# Pull the deployment scripts
git pull origin main

# Run the setup (one time only)
bash setup_auto_deploy.sh
```

## ✅ After Setup

### Your Workflow Becomes:

**Local Development:**
```bash
# 1. Make your changes in VS Code
# 2. Commit and push
git add .
git commit -m "Your changes"
git push origin main

# 3. Wait 5 minutes (or run manual deploy on server)
# 4. Changes are LIVE! ✨
```

**Manual Deploy (if you can't wait 5 minutes):**
```bash
# SSH into server
cd ~/zenithedge_app
bash deploy.sh
```

## 📊 Monitoring

**Check deployment logs:**
```bash
tail -f ~/etotonest.com/logs/deploy.log
```

**Check last deployment:**
```bash
tail -20 ~/etotonest.com/logs/deploy.log
```

**Check cron jobs:**
```bash
crontab -l
```

## 🔧 How It Works

```
┌─────────────────┐
│  Local VS Code  │
│  (Your laptop)  │
└────────┬────────┘
         │ git push
         ▼
┌─────────────────┐
│     GitHub      │
│  (Repository)   │
└────────┬────────┘
         │ Every 5 min
         ▼
┌─────────────────┐
│ Server Cron Job │
│ checks for new  │
│ commits         │
└────────┬────────┘
         │ git pull
         ▼
┌─────────────────┐
│ zenithedge_app/ │
│ (Git clone)     │
└────────┬────────┘
         │ rsync
         ▼
┌─────────────────┐
│ etotonest.com/  │
│ (Production)    │
└─────────────────┘
```

## 🎨 Directory Structure

```
/home/equabish/
├── zenithedge_app/          ← Git repository (read-only, syncs from GitHub)
│   ├── .git/
│   ├── deploy.sh            ← Deployment script
│   └── ... (all your code)
│
└── etotonest.com/           ← Production directory (updated by deploy.sh)
    ├── engine/
    ├── signals/
    ├── manage.py
    ├── passenger_wsgi.py
    └── logs/
        └── deploy.log       ← Deployment history
```

## 🚨 Important Notes

1. **Never edit files directly in `etotonest.com/`** - they will be overwritten!
2. **All changes must be made locally and pushed to GitHub**
3. **Database and media files are preserved** (not synced from git)
4. **Environment files (.env) are excluded** from sync

## 🔥 Quick Commands

```bash
# Force immediate deployment
ssh equabish@server293 "cd ~/zenithedge_app && bash deploy.sh"

# Check if cron is working
ssh equabish@server293 "tail ~/etotonest.com/logs/deploy.log"

# Remove auto-deployment
ssh equabish@server293 "crontab -l | grep -v deploy.sh | crontab -"
```

## 🎯 Result

**Before:**
- ❌ Copy files via cPanel File Manager
- ❌ Extract tar.gz manually
- ❌ Restart app manually
- ❌ Prone to errors

**After:**
- ✅ Just `git push` from VS Code
- ✅ Auto-deploys within 5 minutes
- ✅ Auto-restarts application
- ✅ Full deployment logs
- ✅ Zero manual work!

---

**🎊 You now have professional CI/CD deployment!**
