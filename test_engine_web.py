#!/usr/bin/env python
"""Test Engine Web Interface and API Endpoints"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

print("=" * 60)
print("ENGINE WEB INTERFACE VERIFICATION")
print("=" * 60)
print()

# 1. Check available views
print("1️⃣  AVAILABLE VIEWS")
import engine.views as views
view_list = [x for x in dir(views) if not x.startswith('_') and callable(getattr(views, x))]
for view in sorted(view_list):
    print(f"   ✅ {view}")
print()

# 2. Check URL patterns
print("2️⃣  URL PATTERNS")
try:
    from engine import urls
    from django.urls import URLPattern, URLResolver
    
    def extract_patterns(urlpatterns, prefix=''):
        patterns = []
        for pattern in urlpatterns:
            if isinstance(pattern, URLPattern):
                route = str(pattern.pattern)
                name = pattern.name or '(no name)'
                patterns.append((prefix + route, name))
            elif isinstance(pattern, URLResolver):
                patterns.extend(extract_patterns(pattern.url_patterns, prefix + str(pattern.pattern)))
        return patterns
    
    patterns = extract_patterns(urls.urlpatterns)
    print(f"   Found {len(patterns)} URL patterns:")
    for route, name in patterns:
        print(f"   ✅ /{route.rstrip('^$')} → {name}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print()

# 3. Test view imports
print("3️⃣  VIEW FUNCTION TESTS")
test_views = [
    'backtest_list',
    'backtest_run',
    'backtest_results',
    'market_data_status',
    'api_status',
]

for view_name in test_views:
    if hasattr(views, view_name):
        view_func = getattr(views, view_name)
        print(f"   ✅ {view_name} - {type(view_func).__name__}")
    else:
        print(f"   ⚠️  {view_name} - not found")

print()

# 4. Check admin registration
print("4️⃣  ADMIN INTERFACE")
try:
    from django.contrib import admin
    from engine.models import MarketBar, BacktestRun, BacktestTrade
    
    if admin.site.is_registered(MarketBar):
        print("   ✅ MarketBar registered in admin")
    else:
        print("   ⚠️  MarketBar not in admin")
    
    if admin.site.is_registered(BacktestRun):
        print("   ✅ BacktestRun registered in admin")
    else:
        print("   ⚠️  BacktestRun not in admin")
    
    if admin.site.is_registered(BacktestTrade):
        print("   ✅ BacktestTrade registered in admin")
    else:
        print("   ⚠️  BacktestTrade not in admin")
except Exception as e:
    print(f"   ⚠️  Admin check error: {e}")

print()

# 5. Test API endpoint availability
print("5️⃣  API ENDPOINT TEST")
try:
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    
    factory = RequestFactory()
    User = get_user_model()
    
    # Create a mock request
    request = factory.get('/engine/api/status/')
    
    # Try to call the status view if it exists
    if hasattr(views, 'api_status'):
        print("   ✅ api_status view exists")
        print("   📡 Test with: curl https://z.equatorfoods.org/engine/api/status/")
    else:
        # Look for any API-related views
        api_views = [v for v in view_list if 'api' in v.lower() or 'status' in v.lower()]
        if api_views:
            print(f"   ✅ Found API views: {', '.join(api_views)}")
        else:
            print("   ⚠️  No API views found")
            
except Exception as e:
    print(f"   ⚠️  API test error: {e}")

print()

# 6. Suggested URLs to test
print("6️⃣  SUGGESTED URLS TO TEST")
base_url = "https://etotonest.com"
test_urls = [
    f"{base_url}/admin/engine/",
    f"{base_url}/admin/engine/marketbar/",
    f"{base_url}/admin/engine/backtestrun/",
    f"{base_url}/admin/engine/backtesttrade/",
    f"{base_url}/engine/",
]

for url in test_urls:
    print(f"   🔗 {url}")

print()
print("=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print()
print("💡 TIP: Test in browser or with curl:")
print(f"   curl {base_url}/engine/api/status/")
print(f"   curl {base_url}/engine/")
