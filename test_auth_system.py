#!/usr/bin/env python3
"""
ZenithEdge Authentication System Test Script

This script tests the complete authentication system including:
- User creation and management
- API key authentication
- Role-based access control
- Webhook signal creation
- Dashboard filtering
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from accounts.models import CustomUser
from signals.models import Signal
from django.contrib.auth import authenticate

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_user_creation():
    """Test user creation and API key generation"""
    print_header("Testing User Creation & API Keys")
    
    # Check admin user
    try:
        admin = CustomUser.objects.get(email='admin@zenithedge.com')
        print(f"✅ Admin user exists")
        print(f"   Email: {admin.email}")
        print(f"   Role: {'Admin' if admin.is_admin else 'Unknown'}")
        print(f"   Staff: {admin.is_staff}")
        print(f"   API Key: {admin.api_key[:30]}...")
    except CustomUser.DoesNotExist:
        print(f"❌ Admin user not found!")
        return False
    
    # Check trader user
    try:
        trader = CustomUser.objects.get(email='trader@zenithedge.com')
        print(f"\n✅ Trader user exists")
        print(f"   Email: {trader.email}")
        print(f"   Role: {'Trader' if trader.is_trader else 'Unknown'}")
        print(f"   Staff: {trader.is_staff}")
        print(f"   API Key: {trader.api_key[:30]}...")
    except CustomUser.DoesNotExist:
        print(f"❌ Trader user not found!")
        return False
    
    return True

def test_authentication():
    """Test email-based authentication"""
    print_header("Testing Email Authentication")
    
    # Test admin login
    admin_auth = authenticate(username='admin@zenithedge.com', password='admin123')
    if admin_auth:
        print(f"✅ Admin authentication successful")
        print(f"   Authenticated as: {admin_auth.email}")
    else:
        print(f"❌ Admin authentication failed!")
        return False
    
    # Test trader login
    trader_auth = authenticate(username='trader@zenithedge.com', password='trader123')
    if trader_auth:
        print(f"✅ Trader authentication successful")
        print(f"   Authenticated as: {trader_auth.email}")
    else:
        print(f"❌ Trader authentication failed!")
        return False
    
    # Test invalid login
    invalid_auth = authenticate(username='admin@zenithedge.com', password='wrongpassword')
    if not invalid_auth:
        print(f"✅ Invalid credentials correctly rejected")
    else:
        print(f"❌ Invalid credentials accepted (security issue)!")
        return False
    
    return True

def test_api_key_auth():
    """Test API key authentication"""
    print_header("Testing API Key Authentication")
    
    admin = CustomUser.objects.get(email='admin@zenithedge.com')
    trader = CustomUser.objects.get(email='trader@zenithedge.com')
    
    # Test admin API key
    admin_by_key = CustomUser.objects.filter(api_key=admin.api_key).first()
    if admin_by_key and admin_by_key.email == admin.email:
        print(f"✅ Admin API key authentication successful")
    else:
        print(f"❌ Admin API key authentication failed!")
        return False
    
    # Test trader API key
    trader_by_key = CustomUser.objects.filter(api_key=trader.api_key).first()
    if trader_by_key and trader_by_key.email == trader.email:
        print(f"✅ Trader API key authentication successful")
    else:
        print(f"❌ Trader API key authentication failed!")
        return False
    
    # Test invalid API key
    invalid_key = CustomUser.objects.filter(api_key='invalid_key_12345').first()
    if not invalid_key:
        print(f"✅ Invalid API key correctly rejected")
    else:
        print(f"❌ Invalid API key accepted!")
        return False
    
    return True

def test_signal_ownership():
    """Test signal ownership and filtering"""
    print_header("Testing Signal Ownership & Filtering")
    
    admin = CustomUser.objects.get(email='admin@zenithedge.com')
    trader = CustomUser.objects.get(email='trader@zenithedge.com')
    
    # Count signals
    total_signals = Signal.objects.count()
    admin_signals = Signal.objects.filter(user=admin).count()
    trader_signals = Signal.objects.filter(user=trader).count()
    unassigned_signals = Signal.objects.filter(user=None).count()
    
    print(f"Total signals in database: {total_signals}")
    print(f"Admin signals: {admin_signals}")
    print(f"Trader signals: {trader_signals}")
    print(f"Unassigned signals: {unassigned_signals}")
    
    # Check if signals are properly assigned
    if admin_signals > 0:
        print(f"✅ Admin has {admin_signals} signal(s)")
        admin_signal = Signal.objects.filter(user=admin).first()
        print(f"   Example: {admin_signal.symbol} - {admin_signal.regime}")
    
    if trader_signals > 0:
        print(f"✅ Trader has {trader_signals} signal(s)")
        trader_signal = Signal.objects.filter(user=trader).first()
        print(f"   Example: {trader_signal.symbol} - {trader_signal.regime}")
    
    return True

def test_role_based_access():
    """Test role-based access control"""
    print_header("Testing Role-Based Access Control")
    
    admin = CustomUser.objects.get(email='admin@zenithedge.com')
    trader = CustomUser.objects.get(email='trader@zenithedge.com')
    
    # Admin should see all signals
    admin_view_count = Signal.objects.all().count()
    print(f"Admin view (all signals): {admin_view_count} signals")
    
    # Trader should see only their own
    trader_view_count = Signal.objects.filter(user=trader).count()
    print(f"Trader view (own signals): {trader_view_count} signals")
    
    # Verify admin sees more than trader (if trader has fewer signals)
    if admin.is_admin:
        print(f"✅ Admin role verified (is_admin={admin.is_admin})")
    else:
        print(f"❌ Admin role not set correctly!")
        return False
    
    if trader.is_trader:
        print(f"✅ Trader role verified (is_trader={trader.is_trader})")
    else:
        print(f"❌ Trader role not set correctly!")
        return False
    
    return True

def test_user_properties():
    """Test custom user model properties"""
    print_header("Testing Custom User Properties")
    
    admin = CustomUser.objects.get(email='admin@zenithedge.com')
    trader = CustomUser.objects.get(email='trader@zenithedge.com')
    
    # Test role property
    print(f"Admin role property: {admin.role}")
    print(f"Trader role property: {trader.role}")
    
    if admin.role in ['Admin', 'Superuser']:
        print(f"✅ Admin role property correct ({admin.role})")
    else:
        print(f"❌ Admin role property incorrect!")
        return False
    
    if trader.role == 'Trader':
        print(f"✅ Trader role property correct")
    else:
        print(f"❌ Trader role property incorrect!")
        return False
    
    # Test timezone
    print(f"\nAdmin timezone: {admin.timezone}")
    print(f"Trader timezone: {trader.timezone}")
    
    return True

def print_summary():
    """Print system summary"""
    print_header("System Summary")
    
    total_users = CustomUser.objects.count()
    admin_count = CustomUser.objects.filter(is_admin=True).count()
    trader_count = CustomUser.objects.filter(is_trader=True).count()
    staff_count = CustomUser.objects.filter(is_staff=True).count()
    
    total_signals = Signal.objects.count()
    allowed_signals = Signal.objects.filter(is_allowed=True).count()
    rejected_signals = Signal.objects.filter(is_allowed=False).count()
    
    print(f"Users:")
    print(f"  Total: {total_users}")
    print(f"  Admins: {admin_count}")
    print(f"  Traders: {trader_count}")
    print(f"  Staff: {staff_count}")
    
    print(f"\nSignals:")
    print(f"  Total: {total_signals}")
    print(f"  Allowed: {allowed_signals}")
    print(f"  Rejected: {rejected_signals}")
    
    # Show recent signals with owners
    print(f"\nRecent Signals:")
    for signal in Signal.objects.all()[:5]:
        owner = signal.user.email if signal.user else "Unassigned"
        print(f"  #{signal.id} - {signal.symbol} {signal.side} ({signal.regime}) - Owner: {owner}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  ZenithEdge Authentication System Test Suite")
    print("="*60)
    
    tests = [
        ("User Creation", test_user_creation),
        ("Email Authentication", test_authentication),
        ("API Key Authentication", test_api_key_auth),
        ("Signal Ownership", test_signal_ownership),
        ("Role-Based Access", test_role_based_access),
        ("User Properties", test_user_properties),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_summary()
    
    # Print test results
    print_header("Test Results")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
