#!/usr/bin/env python3
"""Script to create SessionRule test data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from signals.models import SessionRule
from accounts.models import CustomUser

# Get admin user
admin_user = CustomUser.objects.get(email='admin@zenithedge.com')

# Create session rules
# Block Asia session
asia_rule, created = SessionRule.objects.get_or_create(
    user=admin_user,
    session='Asia',
    defaults={'is_blocked': True, 'weight': 1.0, 'notes': 'Blocking Asia session for testing'}
)
if created:
    print('✅ Created Asia session rule (BLOCKED)')
else:
    asia_rule.is_blocked = True
    asia_rule.save()
    print('✅ Updated Asia session rule (BLOCKED)')

# Set weight for London session
london_rule, created = SessionRule.objects.get_or_create(
    user=admin_user,
    session='London',
    defaults={'is_blocked': False, 'weight': 1.5, 'notes': 'Higher weight for London session'}
)
if created:
    print('✅ Created London session rule (Weight: 1.5)')
else:
    london_rule.weight = 1.5
    london_rule.is_blocked = False
    london_rule.save()
    print('✅ Updated London session rule (Weight: 1.5)')

# Normal weight for NY session
ny_rule, created = SessionRule.objects.get_or_create(
    user=admin_user,
    session='New York',
    defaults={'is_blocked': False, 'weight': 1.0, 'notes': 'Normal NY session'}
)
if created:
    print('✅ Created New York session rule (Weight: 1.0)')
else:
    ny_rule.weight = 1.0
    ny_rule.is_blocked = False
    ny_rule.save()
    print('✅ Updated New York session rule (Weight: 1.0)')

print('\n📋 Session Rules Summary:')
for rule in SessionRule.objects.filter(user=admin_user):
    status = 'BLOCKED' if rule.is_blocked else f'Weight: {rule.weight}'
    print(f'  {rule.session}: {status}')
