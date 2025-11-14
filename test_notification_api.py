#!/usr/bin/env python3
"""
Test script for notification bell API endpoint
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from autopsy.models import MarketInsight
from autopsy.views import recent_insights_api
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test request
factory = RequestFactory()
request = factory.get('/autopsy/api/recent-insights/')

# Get or create a test user
user, created = User.objects.get_or_create(email='test@example.com', defaults={'is_active': True})
request.user = user
request.session = {}

print("=" * 60)
print("NOTIFICATION API TEST")
print("=" * 60)

# Check if we have any insights
total_insights = MarketInsight.objects.count()
print(f"\n📊 Total insights in database: {total_insights}")

if total_insights > 0:
    # Get recent insights
    recent = MarketInsight.objects.order_by('-created_at')[:5]
    print(f"\n🔍 Most recent insights:")
    for insight in recent:
        time_diff = timezone.now() - insight.created_at
        if time_diff.seconds < 60:
            time_ago = 'Just now'
        elif time_diff.seconds < 3600:
            time_ago = f'{time_diff.seconds // 60}m ago'
        else:
            hours = time_diff.seconds // 3600
            if hours > 24:
                time_ago = f'{time_diff.days}d ago'
            else:
                time_ago = f'{hours}h ago'
        
        print(f"   • ID {insight.id}: {insight.symbol} {insight.timeframe} - Score: {insight.insight_index}/100 ({time_ago})")

# Test the API endpoint
print("\n🔔 Testing notification API endpoint...")
response = recent_insights_api(request)

# Parse response
import json
data = json.loads(response.content)

print(f"\n✅ API Response:")
print(f"   Status: {data.get('status')}")
print(f"   Count: {data.get('count')}")

if data.get('insights'):
    print(f"\n📬 Notification Items:")
    for notification in data['insights']:
        read_status = '📖 Read' if notification['read'] else '🆕 Unread'
        print(f"   • {notification['symbol']} {notification['timeframe']} - {notification['insight_index']}/100 ({notification['time_ago']}) [{read_status}]")
else:
    print("\n   No notifications to display")

print("\n" + "=" * 60)
print("✅ Test completed successfully!")
print("=" * 60)
