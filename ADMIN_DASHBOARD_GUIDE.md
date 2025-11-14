# Admin Dashboard Guide

## Overview

The **Admin Dashboard** is a comprehensive control panel that centralizes all system management functions, providing staff members with a unified interface to monitor, analyze, and manage the entire ZenithEdge Trading Hub.

## Access

- **URL**: `http://127.0.0.1:8000/admin-dashboard/`
- **Requirements**: Staff member status (`is_staff=True`)
- **Navigation**: 
  - From main dashboard: User dropdown → "Admin Dashboard"
  - Alert banner on main dashboard (for staff users)
  - Direct URL access

## Features

### 1. Main Dashboard
**URL**: `/admin-dashboard/`

**System Health Monitor**:
- Database status
- API status
- Storage status
- Cache status

**Statistics Panels**:

**User Statistics**:
- Total users
- Active users (7 days)
- New users today/this week
- Staff members
- Verified users

**Signal Performance**:
- Total signals
- Active signals
- Signals today
- Win rate
- Total P&L
- Winning/losing signals

**Module Overview**:
- Trading strategies
- Trading sessions
- Risk blocks today
- Journal entries
- ZenithMentor stats (apprentices, simulations, badges)
- PropCoach stats (challenges, passed)
- ZenBot conversations
- News articles & sentiment
- Support tickets

**Recent Activity**:
- Latest 10 signals
- Latest 10 users
- Latest 5 support tickets
- Top 5 performing strategies

### 2. User Management
**URL**: `/admin-dashboard/users/`

**Features**:
- View all registered users
- Filter by: All / Staff / Active / Inactive
- Search by email or name
- User details:
  - Email
  - Status (Active/Inactive)
  - Role (Superuser/Staff/User)
  - Join date
  - Last login
- Quick actions:
  - Edit user (links to Django admin)
  - Delete user (links to Django admin)

**Statistics**:
- Total users
- Users displayed
- Staff members
- Active today

### 3. System Settings
**URL**: `/admin-dashboard/settings/`

**General Settings**:
- Site name
- Maintenance mode toggle
- User registration enable/disable

**Trading Settings**:
- Max signals per day
- Risk control enable/disable

**Notification Settings**:
- Email notifications toggle

**Quick Links to Django Admin**:
- Manage Signals
- Manage Strategies
- Risk Controls
- Manage Users

### 4. System Analytics
**URL**: `/admin-dashboard/analytics/`

**Time Range Filters**:
- 7 days
- 30 days
- 90 days

**Charts** (using Chart.js):
1. **User Growth Chart** (Line chart)
   - New user registrations over time
   
2. **Signal Volume Chart** (Bar chart)
   - Signal creation volume over time
   
3. **Trading Performance Chart** (Multi-line chart)
   - Wins vs Losses over time
   - Daily P&L trends

## Sidebar Navigation

**Dashboard Section**:
- Dashboard
- User Management
- Analytics
- System Settings

**Module Management**:
- Signals (Django admin)
- Strategies (Django admin)
- Sessions (Django admin)
- Risk Control (Django admin)
- ZenithMentor (Django admin)
- PropCoach (Django admin)
- ZenBot (Django admin)
- ZenNews (Django admin)
- Support (Django admin)

**System**:
- Django Admin
- Main Dashboard (back to signals dashboard)
- Logout

## Design Features

- **Dark theme** with gradient background
- **Glassmorphism** effects (backdrop blur)
- **Hover animations** on stat cards
- **Color-coded metrics**:
  - Primary (green): User stats, apprentices
  - Info (blue): Active items, scenarios
  - Warning (orange): Pending items, challenges
  - Danger (red): Risk blocks, open tickets
  - Success (light green): Completed items
  
- **Responsive layout** (Bootstrap 5.3.0)
- **Bootstrap Icons** for visual elements
- **Inter font** for modern typography

## Quick Actions Bar

Located at the top of the main dashboard:
- Add User
- Create Signal
- New Strategy
- Settings

## Statistics Summary

The dashboard provides **real-time statistics** across:
- 4 user metrics
- 4 signal performance metrics
- 12 module metrics (strategies, sessions, risk, etc.)
- 4 ZenithMentor metrics
- 4 PropCoach/Bot/News metrics
- 4 support metrics

## Integration with Django Admin

The admin dashboard **complements** (not replaces) the Django admin:
- Quick navigation to specific Django admin pages
- Provides overview and analytics
- Django admin for detailed CRUD operations
- Admin dashboard for monitoring and insights

## Technical Implementation

**Files Created**:
```
admin_dashboard/
├── __init__.py
├── apps.py
├── models.py (empty - uses existing models)
├── admin.py (empty - custom interface)
├── urls.py
├── views.py (4 views)
└── templates/
    └── admin_dashboard/
        ├── dashboard.html
        ├── user_management.html
        ├── settings.html
        └── analytics.html
```

**Views**:
1. `admin_dashboard()` - Main dashboard with all statistics
2. `user_management()` - User listing and filtering
3. `system_settings()` - Configuration interface
4. `system_analytics()` - Time-series charts

**Security**:
- All views protected with `@staff_member_required` decorator
- Only accessible to staff members
- Inherits Django's authentication system

**Dependencies**:
- Django 4.2.7
- Bootstrap 5.3.0
- Bootstrap Icons 1.10.5
- Chart.js 4.4.0
- Inter font (Google Fonts)

## Models Used (from other apps)

**accounts**:
- `CustomUser`

**signals**:
- `Signal`
- `StrategyPerformance`
- `SessionRule`
- `RiskControl`
- `TradeJournalEntry`

**bot**:
- `BotConversation`

**propcoach** (optional):
- `PropChallenge`
- `FirmTemplate`

**zenithmentor** (optional):
- `ApprenticeProfile`
- `Scenario`
- `SimulationRun`
- `SkillBadge`

**zennews** (optional):
- `NewsArticle`
- `MarketSentiment`

**support** (optional):
- `SupportTicket`

## Usage Scenarios

### Scenario 1: Daily Monitoring
1. Login as staff user
2. Navigate to Admin Dashboard
3. Check system health indicators
4. Review signal performance (win rate, P&L)
5. Check for risk blocks
6. Review open support tickets

### Scenario 2: User Management
1. Go to User Management section
2. Filter by "Active" users
3. Search for specific user by email
4. Click "Edit" to modify user details
5. Check last login times

### Scenario 3: Performance Analysis
1. Navigate to Analytics section
2. Select 30-day time range
3. Review user growth chart
4. Analyze signal volume trends
5. Check win/loss performance over time

### Scenario 4: System Configuration
1. Go to System Settings
2. Adjust max signals per day
3. Toggle risk control
4. Enable/disable user registration
5. Save settings

## Best Practices

1. **Regular Monitoring**: Check dashboard daily for:
   - System health issues
   - Unusual signal patterns
   - Open support tickets
   - Risk control triggers

2. **User Management**: 
   - Weekly review of new users
   - Monthly cleanup of inactive accounts
   - Monitor staff member activity

3. **Performance Tracking**:
   - Weekly review of strategy performance
   - Monthly P&L analysis
   - Identify underperforming strategies

4. **Security**:
   - Regularly review staff access
   - Monitor login patterns
   - Check for suspicious activity

## Future Enhancements

**Potential additions**:
- [ ] Real-time WebSocket updates
- [ ] Export reports to PDF/Excel
- [ ] Email notifications for critical events
- [ ] Advanced filtering and sorting
- [ ] Pagination for large datasets
- [ ] Custom dashboard widgets
- [ ] Role-based permissions (admin vs moderator)
- [ ] Audit log viewer
- [ ] System backup/restore interface
- [ ] Database optimization tools

## Troubleshooting

**Issue**: "Permission Denied"
- **Solution**: Ensure user has `is_staff=True` set in Django admin

**Issue**: "Module stats showing 0"
- **Solution**: Optional modules (PropCoach, ZenithMentor) need to be installed and populated

**Issue**: "Charts not displaying"
- **Solution**: Ensure Chart.js CDN is accessible, check browser console for errors

**Issue**: "Slow loading"
- **Solution**: Database optimization needed, add indexes to frequently queried fields

## Configuration

**URLs Configuration** (`zenithedge/urls.py`):
```python
path('admin-dashboard/', include('admin_dashboard.urls')),
```

**Settings** (`zenithedge/settings.py`):
```python
INSTALLED_APPS = [
    ...
    'admin_dashboard',
]
```

**Navigation Added**:
- Main dashboard user dropdown
- Alert banner for staff users

## Support

For issues or questions:
1. Check Django admin logs
2. Review server logs (`/tmp/django_server.log`)
3. Verify staff permissions
4. Check database connectivity

## Summary

The Admin Dashboard provides a **centralized, modern interface** for managing the entire ZenithEdge Trading Hub. It combines:
- Real-time statistics
- User management
- System analytics
- Configuration tools
- Quick access to Django admin

All while maintaining security, performance, and ease of use.
