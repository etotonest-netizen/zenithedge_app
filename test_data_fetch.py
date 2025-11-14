#!/usr/bin/env python
"""Test data fetching for engine"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from adapters.tv_historical import fetch_historical_data
from datetime import datetime, timedelta
import pandas as pd

print("=" * 60)
print("DATA FETCHING TEST")
print("=" * 60)
print()

# Test 1: Check yfinance installation
print("1️⃣  Checking yfinance installation...")
try:
    import yfinance as yf
    print(f"   ✅ yfinance version: {yf.__version__}")
except ImportError:
    print("   ❌ yfinance not installed")
    print("   Run: pip install yfinance")
    exit(1)

print()

# Test 2: Try different symbol formats
print("2️⃣  Testing symbol formats...")
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

symbols_to_test = [
    ('EURUSD=X', 'Yahoo Finance Forex format'),
    ('EURUSD', 'Direct format'),
    ('BTC-USD', 'Crypto format'),
]

for symbol, description in symbols_to_test:
    print(f"\n   Testing {symbol} ({description})...")
    try:
        df = fetch_historical_data(symbol, '1H', start_date, end_date)
        if df is not None and not df.empty:
            print(f"   ✅ Success! Got {len(df)} bars")
            print(f"   Latest: {df.tail(1)}")
            break
        else:
            print(f"   ⚠️  No data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
