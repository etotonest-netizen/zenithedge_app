#!/usr/bin/env python
"""Comprehensive Engine Deployment Verification"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

print("=" * 60)
print("ENGINE DEPLOYMENT VERIFICATION")
print("=" * 60)
print()

# 1. Check models
print("1️⃣  MODELS CHECK")
try:
    from engine.models import MarketBar, BacktestRun, BacktestTrade
    print("   ✅ MarketBar imported")
    print("   ✅ BacktestRun imported")
    print("   ✅ BacktestTrade imported")
    
    # Check related_name
    from accounts.models import CustomUser
    if hasattr(CustomUser, 'engine_backtest_runs'):
        print("   ✅ Correct related_name (engine_backtest_runs)")
    else:
        print("   ⚠️  Related name issue detected")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    sys.exit(1)

print()

# 2. Check database tables
print("2️⃣  DATABASE TABLES CHECK")
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
            print(f"   ❌ {table} NOT FOUND")
    
    print(f"   📊 Total engine tables: {len(tables)}")
except Exception as e:
    print(f"   ❌ Database check failed: {e}")

print()

# 3. Check views
print("3️⃣  VIEWS CHECK")
try:
    import engine.views as views
    view_functions = [name for name in dir(views) if not name.startswith('_')]
    print(f"   ✅ engine.views imported")
    print(f"   📋 Found {len(view_functions)} items")
    
    # Check for key views
    key_views = ['backtest_dashboard', 'run_backtest_view', 'backtest_detail']
    for view in key_views:
        if hasattr(views, view):
            print(f"   ✅ {view}")
        else:
            print(f"   ⚠️  {view} not found")
except Exception as e:
    print(f"   ⚠️  Views check: {e}")

print()

# 4. Check URLs
print("4️⃣  URL CONFIGURATION CHECK")
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    
    # Check if engine URLs are registered
    engine_patterns = [p for p in resolver.url_patterns if 'engine' in str(p.pattern)]
    if engine_patterns:
        print(f"   ✅ Engine URLs registered ({len(engine_patterns)} patterns)")
    else:
        print("   ⚠️  Engine URLs not found in main urlpatterns")
except Exception as e:
    print(f"   ⚠️  URL check: {e}")

print()

# 5. Check management commands
print("5️⃣  MANAGEMENT COMMANDS CHECK")
try:
    from django.core.management import get_commands
    commands = get_commands()
    
    engine_commands = ['run_backtest', 'fetch_and_run']
    for cmd in engine_commands:
        if cmd in commands:
            print(f"   ✅ {cmd}")
        else:
            print(f"   ⚠️  {cmd} not found")
except Exception as e:
    print(f"   ⚠️  Commands check: {e}")

print()

# 6. Check file structure
print("6️⃣  FILE STRUCTURE CHECK")
import os
engine_files = [
    'engine/models.py',
    'engine/views.py',
    'engine/urls.py',
    'engine/scoring.py',
    'engine/visuals.py',
    'engine/backtest.py',
    'engine/management/commands/run_backtest.py',
    'engine/management/commands/fetch_and_run.py',
]

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for file_path in engine_files:
    full_path = os.path.join(base_dir, file_path)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"   ✅ {file_path} ({size} bytes)")
    else:
        print(f"   ❌ {file_path} MISSING")

print()
print("=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
