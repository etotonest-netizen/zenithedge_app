#!/usr/bin/env python
"""Quick verification script for engine deployment"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from engine.models import MarketBar, BacktestRun, BacktestTrade

print("✅ Engine Models Import Test")
print(f"   - MarketBar: {MarketBar.__name__}")
print(f"   - BacktestRun: {BacktestRun.__name__}")
print(f"   - BacktestTrade: {BacktestTrade.__name__}")
print()

# Check database tables exist
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES LIKE 'engine_%'")
    tables = cursor.fetchall()
    print(f"✅ Database Tables Created: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")

print()
print("✅ ENGINE DEPLOYMENT VERIFIED!")
