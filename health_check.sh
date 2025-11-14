#!/bin/bash
echo "🔍 ZenithEdge System Health Check"
echo "=================================="
echo ""

# Check server
echo "🌐 Server Status:"
if ps aux | grep -q "[m]anage.py runserver"; then
    echo "✅ Django server is running"
    SERVER_PID=$(ps aux | grep "[m]anage.py runserver" | awk '{print $2}' | head -1)
    echo "   PID: $SERVER_PID"
else
    echo "❌ Django server is NOT running"
fi
echo ""

# Check database
echo "📊 Database Status:"
if [ -f "db.sqlite3" ]; then
    DB_SIZE=$(ls -lh db.sqlite3 | awk '{print $5}')
    echo "✅ Database exists (Size: $DB_SIZE)"
else
    echo "❌ Database not found"
fi
echo ""

# Check users
echo "👤 Users:"
python3 -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings'); django.setup(); from accounts.models import CustomUser; print(f'   Total: {CustomUser.objects.count()}'); print(f'   Admins: {CustomUser.objects.filter(is_admin=True).count()}'); print(f'   Traders: {CustomUser.objects.filter(is_trader=True).count()}')"
echo ""

# Check signals
echo "📡 Signals:"
python3 -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings'); django.setup(); from signals.models import Signal; print(f'   Total: {Signal.objects.count()}'); print(f'   Allowed: {Signal.objects.filter(is_allowed=True).count()}'); print(f'   Rejected: {Signal.objects.filter(is_allowed=False).count()}')"
echo ""

# Check endpoints
echo "🔗 Endpoint Tests:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/)
if [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Home (redirect to login): $HTTP_CODE"
else
    echo "❌ Home endpoint issue: $HTTP_CODE"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/accounts/login/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Login page accessible: $HTTP_CODE"
else
    echo "❌ Login page issue: $HTTP_CODE"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/admin/)
if [ "$HTTP_CODE" = "302" ]; then
    echo "✅ Admin (redirect to login): $HTTP_CODE"
else
    echo "❌ Admin endpoint issue: $HTTP_CODE"
fi
echo ""

# Run tests
echo "🧪 Running Test Suite:"
python3 test_auth_system.py 2>&1 | grep "Results:"
echo ""

echo "=================================="
echo "✅ Health Check Complete!"
