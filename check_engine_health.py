#!/usr/bin/env python
"""
Engine Health Check & Auto-Fix Script
Run this after deployment to ensure everything works
"""

import os
import sys
import django

# Try production settings first, fallback to default
if os.path.exists('zenithedge/settings_production.py'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings_production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')

django.setup()

print("=" * 60)
print("🔧 ENGINE HEALTH CHECK & AUTO-FIX")
print("=" * 60)
print()

errors = []
warnings = []
fixes_applied = []

# 1. Check Models
print("1️⃣  Checking Models...")
try:
    from engine.models import MarketBar, BacktestRun, BacktestTrade
    print("   ✅ All models imported successfully")
    
    # Check related_name
    from accounts.models import CustomUser
    if hasattr(CustomUser, 'engine_backtest_runs'):
        print("   ✅ Correct related_name (engine_backtest_runs)")
    else:
        warnings.append("Related name might be incorrect")
except Exception as e:
    errors.append(f"Model import failed: {e}")
    print(f"   ❌ {e}")

print()

# 2. Check Database Tables
print("2️⃣  Checking Database Tables...")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE 'engine_%'")
        tables = [t[0] for t in cursor.fetchall()]
    
    expected = ['engine_backtest_run', 'engine_backtest_trade', 'engine_market_bar']
    for table in expected:
        if table in tables:
            print(f"   ✅ {table}")
        else:
            errors.append(f"Missing table: {table}")
            print(f"   ❌ {table} NOT FOUND")
except Exception as e:
    errors.append(f"Database check failed: {e}")

print()

# 3. Check Views & URLs
print("3️⃣  Checking Views & URLs...")
try:
    from engine import views
    if hasattr(views, 'engine_dashboard'):
        print("   ✅ engine_dashboard view exists")
    else:
        errors.append("engine_dashboard view not found")
    
    from engine import urls
    print(f"   ✅ engine/urls.py loaded ({len(urls.urlpatterns)} patterns)")
except Exception as e:
    errors.append(f"Views/URLs check failed: {e}")

print()

# 4. Check Dependencies
print("4️⃣  Checking Dependencies...")
required_packages = {
    'yfinance': 'For market data fetching',
    'pandas': 'For data processing',
    'numpy': 'For numerical computations',
}

for package, purpose in required_packages.items():
    try:
        __import__(package)
        print(f"   ✅ {package} - {purpose}")
    except ImportError:
        warnings.append(f"Missing package: {package}")
        print(f"   ⚠️  {package} NOT INSTALLED - {purpose}")
        print(f"      Install: pip install {package}")

print()

# 5. Check Templates
print("5️⃣  Checking Templates...")
import os
template_path = 'engine/templates/engine/dashboard.html'
if os.path.exists(template_path):
    size = os.path.getsize(template_path)
    print(f"   ✅ Dashboard template exists ({size} bytes)")
    if size < 1000:
        warnings.append("Dashboard template seems too small")
else:
    errors.append("Dashboard template not found")
    print("   ❌ Dashboard template NOT FOUND")

print()

# 6. Test API Endpoint
print("6️⃣  Testing API Endpoint...")
try:
    from django.test import RequestFactory
    factory = RequestFactory()
    request = factory.get('/engine/api/status/')
    
    response = views.get_engine_status(request)
    if response.status_code == 200:
        print("   ✅ API endpoint working")
    else:
        warnings.append(f"API returned status {response.status_code}")
except Exception as e:
    errors.append(f"API test failed: {e}")
    print(f"   ❌ {e}")

print()

# 7. Check Admin Registration
print("7️⃣  Checking Admin Registration...")
try:
    from django.contrib import admin
    from engine.models import MarketBar, BacktestRun, BacktestTrade
    
    registered = []
    if admin.site.is_registered(MarketBar):
        registered.append('MarketBar')
    if admin.site.is_registered(BacktestRun):
        registered.append('BacktestRun')
    if admin.site.is_registered(BacktestTrade):
        registered.append('BacktestTrade')
    
    if len(registered) == 3:
        print(f"   ✅ All models registered in admin")
    else:
        print(f"   ⚠️  Only {len(registered)}/3 models registered")
except Exception as e:
    warnings.append(f"Admin check failed: {e}")

print()

# SUMMARY
print("=" * 60)
print("📊 HEALTH CHECK SUMMARY")
print("=" * 60)
print()

if not errors and not warnings:
    print("✅ ALL CHECKS PASSED! Engine is healthy!")
    print()
    print("🚀 Ready to use:")
    print("   - Dashboard: /engine/")
    print("   - API: /engine/api/status/")
    print("   - Admin: /admin/engine/")
    sys.exit(0)

if errors:
    print(f"❌ ERRORS FOUND: {len(errors)}")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
    print()

if warnings:
    print(f"⚠️  WARNINGS: {len(warnings)}")
    for i, warning in enumerate(warnings, 1):
        print(f"   {i}. {warning}")
    print()

if errors:
    print("🔧 RUN THESE COMMANDS TO FIX:")
    print()
    if "Missing table" in str(errors):
        print("   python manage.py makemigrations engine")
        print("   python manage.py migrate engine")
    if "yfinance" in str(warnings):
        print("   pip install yfinance pandas numpy")
    print()
    sys.exit(1)
else:
    print("✅ No critical errors, but please review warnings above")
    sys.exit(0)
