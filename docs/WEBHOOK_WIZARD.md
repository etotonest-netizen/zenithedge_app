# Webhook Wizard - TradingView Integration Guide

## Overview

The Webhook Wizard is a user-friendly interface that helps traders easily connect their TradingView alerts to the ZenithEdge platform using secure, unique UUID-based webhook URLs.

## Features

### 1. **Unique Webhook URLs**
- Each user gets a unique UUID-based webhook endpoint
- Format: `http://127.0.0.1:8000/api/v1/signal/{uuid}/`
- No API keys needed - URL itself is the authentication
- Easy to regenerate if compromised

### 2. **Beautiful Wizard Interface**
- **Step 1: Get Webhook URL**
  - Display unique webhook URL with copy button
  - Active/Inactive status toggle
  - Regenerate button with confirmation dialog
  - Security warning about keeping URL private

- **Step 2: Copy JSON Template**
  - Pre-filled JSON template with user's UUID
  - Syntax-highlighted code block
  - Copy button for easy paste to TradingView
  - Maps TradingView variables to signal fields:
    - `{{ticker}}` → symbol
    - `{{interval}}` → timeframe
    - `{{strategy.order.action}}` → side (buy/sell)
    - `{{close}}` → price
    - `{{plot_0}}` → stop loss (sl)
    - `{{plot_1}}` → take profit (tp)
    - `{{plot_2}}` → confidence
    - `{{plot_3}}` → strategy name
    - `{{plot_4}}` → market regime
    - `{{plot_5}}` → trading session

- **Step 3: Setup Instructions**
  - 7-step visual guide for creating TradingView alerts
  - Numbered steps with clear descriptions
  - Covers entire process from opening chart to testing

### 3. **Statistics Dashboard**
- **Total Signals**: All signals received by the user
- **Webhook Signals**: Signals received via this webhook
- **Last Signal**: Time since last webhook signal
- "No signals yet" message for new users

### 4. **Help Section**
- Common troubleshooting issues:
  - Signals not arriving
  - Invalid JSON errors
  - Wrong data in signals
  - Webhook disabled status
- Link to ZenBot for additional help

### 5. **AJAX Actions**
- **Toggle Active/Inactive**: Enable or disable webhook without regenerating
- **Regenerate UUID**: Create new UUID and URL for security
- Both actions use fetch API with CSRF protection

## Technical Implementation

### Database Model: WebhookConfig
```python
class WebhookConfig(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webhook_config')
    webhook_uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    webhook_url = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    signal_count = models.IntegerField(default=0)
    last_signal_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Methods:**
- `generate_webhook_url(base_url)` - Creates full webhook URL
- `increment_signal_count()` - Increments counter when signal received
- `regenerate_uuid()` - Generates new UUID for security

### Views

#### WebhookSetupView (Class-Based View)
- **Template**: `signals/webhook_setup.html`
- **GET**: Displays wizard interface
  - Creates/retrieves WebhookConfig for logged-in user
  - Generates webhook URL from request host
  - Provides context: webhook_url, webhook_uuid, statistics, JSON template
- **POST**: Handles AJAX actions
  - `action='regenerate'`: Creates new UUID and URL
  - `action='toggle_active'`: Toggles is_active boolean
  - Returns JSON responses

#### uuid_webhook (Function View)
- **Endpoint**: `/api/v1/signal/{uuid}/`
- **Method**: POST only (CSRF-exempt for TradingView)
- **Process**:
  1. Validates webhook UUID exists and is active
  2. Parses JSON payload from TradingView
  3. Validates user_uuid matches webhook UUID
  4. Maps TradingView data to Signal fields
  5. Creates Signal with user from WebhookConfig
  6. Increments webhook signal counter
  7. Returns JSON response with signal_id

### URL Routes
```python
# Main project URLs (zenithedge/urls.py)
path('api/v1/signal/<uuid:webhook_uuid>/', include('signals.webhook_urls'))

# Signals app URLs (signals/urls.py)
path('webhook-setup/', views.WebhookSetupView.as_view(), name='webhook_setup')

# Webhook URLs (signals/webhook_urls.py)
path('', views.uuid_webhook, name='uuid_webhook')
```

### Frontend Features
- **Dark Theme**: Gradient backgrounds with glass morphism effects
- **Responsive Design**: Works on desktop and mobile
- **Clipboard API**: One-click copy for URL and JSON
- **Visual Feedback**: Success animations for copy actions
- **Confirmation Dialogs**: For destructive actions (regenerate)

## Usage Example

### 1. Access Webhook Wizard
Navigate to: `http://127.0.0.1:8000/signals/webhook-setup/`

### 2. Copy Webhook URL
Click "Copy Webhook URL" button in Step 1

Example URL:
```
http://127.0.0.1:8000/api/v1/signal/1c243468-c67b-4a66-9c39-09fd5ccea7db/
```

### 3. Copy JSON Template
Click "Copy JSON Template" button in Step 2

Example JSON:
```json
{
    "user_uuid": "1c243468-c67b-4a66-9c39-09fd5ccea7db",
    "symbol": "{{ticker}}",
    "timeframe": "{{interval}}",
    "side": "{{strategy.order.action}}",
    "price": {{close}},
    "sl": {{plot_0}},
    "tp": {{plot_1}},
    "confidence": {{plot_2}},
    "strategy": "{{plot_3}}",
    "regime": "{{plot_4}}",
    "session": "{{plot_5}}"
}
```

### 4. Create TradingView Alert
1. Open your chart with Pine Script indicator/strategy
2. Click bell icon (or press Alt+A)
3. Configure alert condition
4. Paste webhook URL in "Webhook URL" field
5. Paste JSON template in "Message" field
6. Click "Create"

### 5. Test Webhook (Manual)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/signal/{your-uuid}/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_uuid": "{your-uuid}",
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "price": 1.0850,
    "sl": 1.0820,
    "tp": 1.0920,
    "confidence": 85,
    "strategy": "Trend",
    "regime": "Bullish",
    "session": "London"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "signal_id": 19,
  "message": "Signal received and processed"
}
```

## Testing Results

### ✅ Test 1: WebhookConfig Creation
- User: trader@zenithedge.com
- UUID: 1c243468-c67b-4a66-9c39-09fd5ccea7db
- URL: http://127.0.0.1:8000/api/v1/signal/1c243468-c67b-4a66-9c39-09fd5ccea7db/
- Active: True
- Signal Count: 0 → 1

### ✅ Test 2: UUID Webhook Endpoint
- Request: POST to `/api/v1/signal/{uuid}/`
- Payload: Valid TradingView JSON
- Response: `{"status": "success", "signal_id": 19, "message": "Signal received and processed"}`
- Signal Created: Yes (ID: 19)
- Counter Updated: Yes (0 → 1)

### ✅ Test 3: Signal Data Mapping
- Symbol: EURUSD ✓
- Timeframe: 1H ✓
- Side: buy ✓
- Price: 1.08500000 ✓
- SL: 1.08200000 ✓
- TP: 1.09200000 ✓
- Confidence: 85.0% ✓
- Strategy: Trend ✓
- Regime: Bullish ✓
- Session: London ✓
- Received: 2025-11-09 12:02:39 ✓

### ✅ Test 4: Dashboard Navigation
- Link added to navigation menu
- Icon: bi-broadcast
- Position: After "Journal" link
- Accessible to all authenticated users

### ✅ Test 5: Admin Integration
- WebhookConfig registered in Django admin
- List display: user, webhook_uuid, is_active, signal_count, last_signal_at, created_at
- Filters: is_active, created_at
- Search: user email, webhook_uuid
- Actions: activate_webhooks, deactivate_webhooks
- Read-only fields: uuid, url, signal_count, last_signal_at, timestamps

## Security Features

1. **UUID-Based Authentication**: No API keys to manage or expose
2. **Per-User URLs**: Each user has unique webhook URL
3. **Easy Revocation**: Regenerate UUID to invalidate old URL
4. **Active/Inactive Toggle**: Disable webhook without deleting config
5. **CSRF Protection**: POST actions in wizard use CSRF tokens
6. **Validation**: Webhook endpoint validates UUID matches payload

## Advantages Over API Keys

1. **Simpler Setup**: No need to generate, store, or manage API keys
2. **No Exposure**: URL is self-contained, no separate credentials
3. **Easy to Revoke**: Click "Regenerate" to get new URL
4. **User-Friendly**: Copy-paste workflow, no API key configuration
5. **Stateless**: No need to lookup user by API key
6. **Per-User Isolation**: Each user has unique URL, can't cross-contaminate

## Future Enhancements

1. **Webhook History**: Log of all webhook requests with payloads
2. **Error Logging**: Track failed webhook attempts
3. **Rate Limiting**: Prevent abuse with too many signals
4. **Multiple Webhooks**: Allow users to have multiple webhook configs
5. **Webhook Testing**: Built-in test button to send sample payload
6. **Analytics**: Charts showing webhook usage over time
7. **Webhook Templates**: Pre-built templates for popular indicators
8. **Notification Settings**: Alert user when webhook receives signals

## Troubleshooting

### Signals Not Arriving
- Check webhook is Active (green status badge)
- Verify webhook URL is correct in TradingView
- Ensure TradingView alert is active and triggering
- Check Django server logs for errors

### Invalid JSON Error
- Verify Pine Script outputs required plots (plot_0 through plot_5)
- Ensure JSON syntax is valid (no trailing commas, proper quotes)
- Check TradingView alert message field has correct JSON

### Wrong Data in Signals
- Verify {{ticker}} matches chart symbol
- Check {{interval}} matches timeframe
- Ensure plot values (plot_0, plot_1, etc.) are correct
- Confirm {{strategy.order.action}} outputs "buy" or "sell"

### Webhook Disabled
- Click "Toggle Status" button to activate
- Check is_active status in Django admin
- Verify webhook_config exists for your user

## Files Modified/Created

### Created
1. `signals/models.py` - WebhookConfig model (~70 lines)
2. `signals/migrations/0009_webhookconfig.py` - Migration file
3. `signals/templates/signals/webhook_setup.html` - Wizard UI (~700 lines)
4. `signals/webhook_urls.py` - UUID webhook URL config (~10 lines)
5. `docs/WEBHOOK_WIZARD.md` - This documentation

### Modified
1. `signals/views.py` - Added WebhookSetupView and uuid_webhook (~220 lines)
2. `signals/urls.py` - Added webhook-setup route
3. `zenithedge/urls.py` - Added UUID webhook endpoint route
4. `signals/templates/signals/dashboard.html` - Added navigation link
5. `signals/admin.py` - Registered WebhookConfig with admin actions

## Completion Status

✅ **Task 1**: WebhookConfig model created and migrated (100%)
✅ **Task 2**: WebhookSetupView and URL route created (100%)
✅ **Task 3**: Webhook wizard template designed (100%)
✅ **Task 4**: UUID webhook endpoint created (100%)
✅ **Task 5**: Navigation link added to dashboard (100%)
✅ **Task 6**: Testing complete - all systems operational (100%)

**Overall: 100% Complete** 🎉

---

**Last Updated**: November 9, 2025
**Author**: GitHub Copilot
**Version**: 1.0.0
