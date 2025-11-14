# ZenithEdge Authentication Guide

## Overview

ZenithEdge uses a custom authentication system with **email-based login** and **API key authentication** for webhooks. The system supports two user roles: **Admin** and **Trader**.

## User Roles

### Admin Users
- **Can view all signals** from all users in the system
- Has access to Django admin panel
- Full system access
- Identified by `is_admin=True` flag

### Trader Users  
- **Can only view their own signals**
- No admin panel access
- Standard trading access
- Identified by `is_trader=True` flag

## Authentication Methods

### 1. Web Authentication (Email/Password)

Users log in using their email and password through the web interface.

**Login URL:** `http://127.0.0.1:8000/accounts/login/`

**Test Accounts:**
```
Admin Account:
Email: admin@zenithedge.com
Password: admin123
Role: Admin (sees all signals)

Trader Account:
Email: trader@zenithedge.com
Password: trader123
Role: Trader (sees only own signals)
```

### 2. API Key Authentication (Webhooks)

TradingView webhooks authenticate using API keys. Each user has a unique API key visible in their profile.

**Webhook URL:** `http://127.0.0.1:8000/api/signals/webhook/`

## API Key Usage

### Method 1: Query Parameter (Recommended for TradingView)
```
http://127.0.0.1:8000/api/signals/webhook/?api_key=YOUR_API_KEY
```

### Method 2: HTTP Header
```bash
curl -X POST "http://127.0.0.1:8000/api/signals/webhook/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSD","timeframe":"1H",...}'
```

### Method 3: JSON Body
```bash
curl -X POST "http://127.0.0.1:8000/api/signals/webhook/" \
  -H "Content-Type: application/json" \
  -d '{"api_key":"YOUR_API_KEY","symbol":"BTCUSD",...}'
```

## Getting Your API Key

1. Log in to ZenithEdge
2. Click on **Profile** in the navigation bar
3. Your API key is displayed under "API Credentials"
4. Copy the key (it's auto-generated and unique to your account)

## User Registration

### Via Web Interface

1. Navigate to `http://127.0.0.1:8000/accounts/register/`
2. Fill in the form:
   - Email (must be unique)
   - Password (minimum 8 characters)
   - Confirm Password
   - Timezone (optional, defaults to UTC)
3. Click "Create Account"
4. You'll be redirected to the login page
5. Your API key is auto-generated upon registration

### Via Django Shell (Advanced)

```python
python3 manage.py shell

from accounts.models import CustomUser

# Create trader
trader = CustomUser.objects.create_user(
    email='newtrader@example.com',
    password='secure_password'
)
trader.is_trader = True
trader.api_key = trader.generate_api_key()
trader.save()

print(f"API Key: {trader.api_key}")
```

## Signal Ownership

When a webhook is received:
1. System extracts the API key from request
2. Authenticates the user based on the API key
3. Assigns the signal to that user
4. Signal appears in the user's dashboard

**Important:** Signals are owned by the user whose API key was used in the webhook request.

## Dashboard Access Control

### For Admin Users
```python
# Dashboard shows ALL signals from ALL users
queryset = Signal.objects.all()
```

### For Trader Users
```python
# Dashboard shows ONLY their own signals
queryset = Signal.objects.filter(user=request.user)
```

## TradingView Webhook Configuration

### Basic Setup
1. Open your Pine Script strategy in TradingView
2. Go to Strategy Settings → Notifications
3. Set webhook URL:
   ```
   http://YOUR_SERVER_IP:8000/api/signals/webhook/?api_key=YOUR_API_KEY
   ```
4. Set message format (JSON):
   ```json
   {
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "side": "{{strategy.order.action}}",
     "sl": {{strategy.order.stop_loss}},
     "tp": {{strategy.order.take_profit}},
     "confidence": {{plot_0}},
     "strategy": "ZenithEdge",
     "regime": "{{plot_1}}",
     "price": {{close}},
     "timestamp": "{{time}}"
   }
   ```

### Security Best Practices

1. **Keep API keys private** - Never share them publicly
2. **Use HTTPS in production** - Encrypt webhook traffic
3. **Rotate keys periodically** - Generate new keys if compromised
4. **Monitor webhook logs** - Check for unauthorized access attempts

## Password Requirements

- Minimum 8 characters
- Cannot be too similar to email
- Cannot be entirely numeric
- Cannot be a commonly used password

## Changing Password

Currently requires Django admin or shell access:

```python
python3 manage.py shell

from accounts.models import CustomUser
user = CustomUser.objects.get(email='user@example.com')
user.set_password('new_secure_password')
user.save()
```

## Regenerating API Keys

```python
python3 manage.py shell

from accounts.models import CustomUser
user = CustomUser.objects.get(email='user@example.com')
user.api_key = user.generate_api_key()
user.save()
print(f"New API Key: {user.api_key}")
```

## Troubleshooting

### "Invalid or missing API key"
- Check that API key is correct (copy from Profile page)
- Verify API key is included in webhook URL or headers
- Ensure no extra spaces or characters

### "User matching query does not exist"
- API key doesn't match any user in database
- User account may have been deleted
- Try regenerating the API key

### Cannot log in
- Verify email is correct (case-sensitive)
- Check password (must be exact match)
- Ensure user account exists

### Dashboard shows no signals
- **For traders:** Only your own signals appear
- **For admins:** Should see all signals
- Check that webhooks are using your API key
- Verify signals were successfully created

## Development vs Production

### Development (Current Setup)
- Server: `http://127.0.0.1:8000`
- Database: SQLite
- DEBUG=True
- No SSL/HTTPS

### Production (Recommended)
- Use production WSGI server (Gunicorn, uWSGI)
- PostgreSQL or MySQL database
- DEBUG=False
- Enable HTTPS/SSL
- Set strong SECRET_KEY
- Configure ALLOWED_HOSTS
- Use environment variables for secrets

## Admin Panel Access

Only users with `is_staff=True` can access Django admin:

**URL:** `http://127.0.0.1:8000/admin/`

**Admin credentials:**
```
Email: admin@zenithedge.com
Password: admin123
```

From admin panel you can:
- Manage users
- View all signals
- Configure prop rules
- Monitor system activity

## API Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/accounts/register/` | GET/POST | None | User registration |
| `/accounts/login/` | GET/POST | None | User login |
| `/accounts/logout/` | POST | Required | User logout |
| `/accounts/profile/` | GET | Required | View profile & API key |
| `/signals/dashboard/` | GET | Required | View signals |
| `/api/signals/webhook/` | POST | API Key | Receive TradingView signals |
| `/admin/` | GET/POST | Staff | Django admin panel |

## Need Help?

- Check server logs for errors
- Verify database migrations: `python3 manage.py migrate`
- Test webhook with curl before using TradingView
- Review `DEPLOYMENT_STATUS.md` for system status
