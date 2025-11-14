# ZenithEdge - Quick Reference Guide

## 🌐 URLs & Endpoints

### Authentication
- **Login**: `http://127.0.0.1:8000/accounts/login/`
- **Register**: `http://127.0.0.1:8000/accounts/register/`
- **Profile**: `http://127.0.0.1:8000/accounts/profile/`
- **Logout**: `http://127.0.0.1:8000/accounts/logout/`

### Dashboards
- **Intelligence Console**: `http://127.0.0.1:8000/signals/insights/`
- **Legacy Dashboard**: `http://127.0.0.1:8000/signals/dashboard/`
- **Strategy Performance**: `http://127.0.0.1:8000/signals/strategies/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`

### API
- **Insights API**: `http://127.0.0.1:8000/api/insights/`
  - Method: GET
  - Authentication: Login required
  - Returns: Market insights with filtering and pagination
- **Webhook (TradingView)**: `http://127.0.0.1:8000/signals/api/webhook/`
  - Method: POST
  - Authentication: API Key (query param, header, or JSON body)
  - Content-Type: application/json

## 👤 Test Accounts

### Admin Account
```
Email: admin@zenithedge.com
Password: admin123
Role: Superuser/Admin
API Key: _yHwEIMeW5srLawBzhqWuup2ZwI9rOukOy2IxtFm3FeMlGUuojUgQSPPMGd_6Jrz
```

### Trader Account
```
Email: trader@zenithedge.com
Password: trader123
Role: Trader
API Key: 9yr3WnpyFoGA_w-c5b53G4KQffBYqHPzC8bNPdTRc4uz6v6JlKHliQPyAXpYmYvv
```

## 📡 Webhook Examples

### Using Query Parameter (Recommended for TradingView)
```bash
curl -X POST "http://127.0.0.1:8000/signals/api/webhook/?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSD",
    "timeframe": "1H",
    "side": "buy",
    "confidence": 85,
    "strategy": "ZenithEdge",
    "regime": "Trend",
    "price": 45000,
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

**Note**: The system now interprets "side" as market bias (buy=bullish, sell=bearish) and focuses on market intelligence rather than trade execution.

### Using HTTP Header
```bash
curl -X POST "http://127.0.0.1:8000/signals/api/webhook/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Using JSON Body
```bash
curl -X POST "http://127.0.0.1:8000/signals/api/webhook/" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "symbol": "BTCUSD",
    ...
  }'
```

## 🔧 Management Commands

### Run Server
```bash
cd /tmp/django_trading_webhook
python3 manage.py runserver
```

### Analyze Performance
```bash
# Basic analysis (last 30 days, simulated)
python3 manage.py analyze_performance --simulate

# Custom time period
python3 manage.py analyze_performance --days 90 --simulate

# Filter by regime
python3 manage.py analyze_performance --regime Trend --simulate

# Filter by symbol
python3 manage.py analyze_performance --symbol BTCUSD --simulate

# Clear and re-analyze
python3 manage.py analyze_performance --clear --simulate
```

### Run Tests
```bash
python3 test_auth_system.py
```

### Health Check
```bash
./health_check.sh
```

## 📊 Dashboard Features

### Signals Dashboard
- View all trading signals
- Filter by regime, strategy, side, symbol
- Real-time statistics
- Role-based filtering (admins see all, traders see own)

### Strategy Performance Dashboard
- Win rate comparison charts
- Risk-reward analysis
- Profit factor metrics
- Trade volume distribution
- Top performer badge (30-day best)
- Advanced filtering options

## 🎯 TradingView Integration

### Webhook URL Format
```
http://YOUR_SERVER_IP:8000/signals/api/webhook/?api_key=YOUR_API_KEY
```

### Alert Message (JSON) - For Trend Signals
```json
{
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "side": "buy",
  "sl": {{plot_0}},
  "tp": {{plot_1}},
  "confidence": {{plot_2}},
  "strategy": "ZenithEdge",
  "regime": "Trend",
  "price": {{close}},
  "timestamp": "{{time}}"
}
```

**Note:** 
- Change `"side"` to `"buy"` or `"sell"` manually for your indicator
- Change `"regime"` to match: "Trend", "Breakout", "MeanReversion", or "Squeeze"
- Use `{{plot_0}}` for Stop Loss, `{{plot_1}}` for Take Profit, `{{plot_2}}` for Confidence
- For strategies (not indicators), you can use `{{strategy.order.action}}` for side

## 🗄️ Database

### Check Data
```python
python3 manage.py shell

# Check users
from accounts.models import CustomUser
CustomUser.objects.all().values('email', 'is_admin', 'is_trader')

# Check signals
from signals.models import Signal
Signal.objects.all().count()
Signal.objects.filter(user__email='admin@zenithedge.com').count()

# Check performance
from signals.models import StrategyPerformance
StrategyPerformance.objects.all().values('strategy_name', 'win_rate', 'total_trades')
```

### Backup Database
```bash
# Backup all data
python3 manage.py dumpdata > backup_$(date +%Y%m%d).json

# Backup specific models
python3 manage.py dumpdata signals.Signal > signals_backup.json
python3 manage.py dumpdata accounts.CustomUser > users_backup.json
```

## 🚀 Quick Start

1. **Start Server**
   ```bash
   cd /tmp/django_trading_webhook
   python3 manage.py runserver
   ```

2. **Login to Dashboard**
   - Visit: http://127.0.0.1:8000/accounts/login/
   - Use admin or trader credentials

3. **View Your API Key**
   - Click "Profile" in navigation
   - Copy your API key

4. **Configure TradingView**
   - Add webhook URL with your API key
   - Use the JSON alert message format above

5. **Analyze Performance**
   ```bash
   python3 manage.py analyze_performance --simulate
   ```

6. **View Results**
   - Visit: http://127.0.0.1:8000/signals/strategies/

## 📖 Documentation Files

- `README.md` - Webhook API documentation
- `AUTH_GUIDE.md` - Authentication system guide
- `PERFORMANCE_ANALYTICS_GUIDE.md` - Performance analytics documentation
- `PROP_RULES_GUIDE.md` - Prop rules setup
- `DASHBOARD_GUIDE.md` - Dashboard customization
- `QUICK_START.md` - Quick start guide
- `DEPLOYMENT_STATUS_v2.md` - System status

## 🔍 Troubleshooting

### Server Not Responding
```bash
# Check if running
ps aux | grep "manage.py runserver"

# Restart
pkill -f "manage.py runserver"
cd /tmp/django_trading_webhook
python3 manage.py runserver
```

### Cannot Login
```bash
# Reset admin password
cd /tmp/django_trading_webhook
python3 -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings'); django.setup(); from accounts.models import CustomUser; u = CustomUser.objects.get(email='admin@zenithedge.com'); u.set_password('admin123'); u.save(); print('Password reset')"
```

### 404 Errors
**Common Issues:**
- Wrong URL path (check this guide)
- Server needs restart after URL changes
- Login required (redirects to login page)

**Correct URLs:**
- ✅ `http://127.0.0.1:8000/signals/dashboard/`
- ✅ `http://127.0.0.1:8000/signals/strategies/`
- ✅ `http://127.0.0.1:8000/signals/api/webhook/`
- ❌ `http://127.0.0.1:8000/api/signals/dashboard/` (OLD)

### Webhook Not Working
1. Check API key is correct
2. Verify URL: `/signals/api/webhook/`
3. Check Content-Type: `application/json`
4. Verify required fields are present
5. Check server logs for errors

## 💡 Tips

1. **Save Your API Key**: Copy from Profile page and store securely
2. **Test Webhook**: Use curl before TradingView integration
3. **Monitor Performance**: Run analyze_performance weekly
4. **Check Logs**: Watch terminal for error messages
5. **Use Filters**: Dashboard filters help find specific signals
6. **Role-Based**: Admins see all data, traders see only their own
7. **Backup Data**: Export important signals regularly

## 📱 Mobile Access

The dashboards are responsive and work on mobile devices:
- Use same URLs on mobile browser
- Login with your credentials
- All features available

## 🎓 Learning Resources

1. **Django Documentation**: https://docs.djangoproject.com/
2. **TradingView Webhooks**: https://www.tradingview.com/support/solutions/43000529348/
3. **Chart.js**: https://www.chartjs.org/docs/

## 🆘 Support Checklist

When reporting issues, include:
- [ ] Exact URL you're trying to access
- [ ] HTTP status code (404, 500, etc.)
- [ ] Browser console errors
- [ ] Server terminal output
- [ ] Django version: 4.2.7
- [ ] Python version: 3.9

## ✅ System Status

**Current Version**: v2.0 (with Performance Analytics)

**Features**:
- ✅ User Authentication
- ✅ Role-Based Access Control
- ✅ API Key Authentication
- ✅ Signal Dashboard
- ✅ Strategy Performance Analytics
- ✅ TradingView Webhook Integration
- ✅ Prop Rules Framework
- ✅ **Session-Based Trading Rules**
- ✅ **Risk Control / Loss Spiral Protection** ⭐ NEW
- ✅ Admin Panel

**Server**: Running on port 8000
**Database**: SQLite (11 signals, 2 users, 1 risk control, 3 session rules)
**Status**: Fully Operational 🟢

## 🕐 Session-Based Trading Rules

**Sessions (UTC):**
- 🟡 **Asia**: 00:00-07:59 (Tokyo, Sydney, Singapore)
- 🟢 **London**: 08:00-15:59 (London, Frankfurt, Zurich)
- 🔵 **New York**: 16:00-23:59 (New York, Chicago, Toronto)

**Features:**
- Auto-detect session from signal timestamp
- Per-user session blocking (block Asia, London, or NY)
- Session weight multipliers (0.0-10.0)
- Color-coded dashboard badges
- Automatic rejection of blocked sessions

**Current Setup (Admin):**
```
🟡 Asia:     � BLOCKED
�🟢 London:   ⚖️ Weight: 1.5
🔵 New York: ⚖️ Weight: 1.0
```

**Manage Session Rules:**
- Admin Panel: http://127.0.0.1:8000/admin/signals/sessionrule/
- Full Guide: `SESSION_RULES_GUIDE.md`

## 🛡️ Risk Control - Loss Spiral Protection

**Overview:**
Automatically halts trading when risk thresholds are exceeded to protect against emotional trading and loss spirals.

**Default Thresholds (Admin):**
```
Max Consecutive Losers:  3 (3 losses in a row → HALT)
Max Daily Trades:         10 (10 trades/day → HALT)
Max Red Signals:          5 (5 rejected/day → HALT)
```

**Current Status:** 🚫 **HALTED** (Consecutive loss limit reached 3/3)

**Features:**
- Auto-halt when limits exceeded
- Red warning banner on dashboard
- Manual reset required
- All signals blocked during halt

**Webhook Response (Halted):**
```json
{
  "status": "received",
  "signal_id": 125,
  "allowed": false,
  "reason": "risk_control: Trading halted: Consecutive loss limit reached (3/3)"
}
```

**Reset Trading Halt:**
1. Go to: http://127.0.0.1:8000/admin/signals/riskcontrol/
2. Select risk control → Actions → "Reset halt status"
3. Or edit and uncheck "is_halted"

**Mark Signals as Win/Loss:**
```python
# Via shell
from signals.models import Signal
signal = Signal.objects.get(id=123)
signal.outcome = 'win'  # or 'loss'
signal.save()
```

📖 **Full Documentation**: `RISK_CONTROL_GUIDE.md`

---

## 📝 Trade Journal System

### Overview
Smart trade journaling with analytics and AI-powered insights.

### Key URLs
- **Journal Dashboard**: `http://127.0.0.1:8000/signals/journal/`
- **API Summary**: `http://127.0.0.1:8000/signals/journal/api/summary/`
- **AI Review**: `http://127.0.0.1:8000/signals/journal/ai-review/` (POST)
- **Admin Panel**: `http://127.0.0.1:8000/admin/signals/tradejournalentry/`

### Quick Stats (Current)
- **Total Entries**: 5
- **Win Rate**: 75.0%
- **Total Pips**: +59.25
- **Avg R:R**: 1.0:1
- **Best Strategy**: ZenithEdge (75.0% WR)
- **Best Session**: Asia (75.0% WR)

### Decision Types
- `took` - Took the Trade
- `skipped` - Skipped the Trade
- `partial` - Partial Entry
- `early_exit` - Early Exit

### Outcome Types
- `win` - Win
- `loss` - Loss
- `breakeven` - Breakeven
- `pending` - Pending
- `scratch` - Scratch Trade

### Creating Entries via Shell
```python
from signals.models import TradeJournalEntry, Signal
from accounts.models import CustomUser
from decimal import Decimal

user = CustomUser.objects.get(email='admin@zenithedge.com')
signal = Signal.objects.filter(user=user).first()

entry = TradeJournalEntry.objects.create(
    user=user,
    signal=signal,
    decision='took',
    outcome='win',
    pips=Decimal('25.50'),
    duration_minutes=45,
    notes='Great setup! Followed the plan.'
)
```

### Get Journal Summary
```python
from signals.models import summarize_journal

summary = summarize_journal(user)
print(f"Win Rate: {summary['win_rate']}%")
print(f"Total Pips: {summary['total_pips']}")
print(f"Best Strategy: {summary['best_strategy']['name']}")
```

### Features
- ✅ Trade decision logging (took/skipped)
- ✅ Outcome tracking with pips
- ✅ Win rate & performance analytics
- ✅ Best strategy/session/regime identification
- ✅ Best trading hours analysis
- ✅ Advanced filtering (symbol, outcome, decision, session)
- ✅ AI-powered pattern analysis
- ✅ Integration with signals
- ✅ RESTful API endpoints

### Admin Actions
- Create/edit/delete journal entries
- Filter by decision, outcome, user
- Search by symbol, strategy, notes
- Role-based access (users see only their entries)

