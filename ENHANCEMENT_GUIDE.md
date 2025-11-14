# ZenithEdge Backend Enhancement - Quick Reference

## ✅ COMPLETED FEATURES (30%)

### 1. Security & Environment ✓
- Environment variables with `.env` support
- Security headers middleware (CSP, HSTS, X-Frame-Options)
- Webhook rate limiting (10 req/sec per UUID)
- HMAC signature validation middleware
- Production-ready security settings

### 2. Database Optimization ✓
- Composite indexes on Signal, SignalEvaluation, TradeJournalEntry
- DailyPerformanceCache model for pre-aggregated stats
- Management command: `python manage.py aggregate_daily_performance`

### 3. Validation & Integrity Checks ✓
- Comprehensive signal validator in `signals/signal_validator.py`
- SL/TP sanity checks (BUY: sl < price < tp, SELL: tp < price < sl)
- Confidence validation (0-100)
- Symbol format validation (A-Z0-9/)
- Risk:Reward ratio calculation and warnings

---

## 🚧 REMAINING FEATURES (70%)

### To implement validation in webhook:
```python
# In signals/views.py @signal_webhook function:
from .signal_validator import validate_signal_data, sanitize_signal_data

# After parsing JSON, before creating signal:
validation_result = validate_signal_data(data)
if not validation_result['valid']:
    logger.warning(f"Webhook validation failed: {validation_result['errors']}")
    return JsonResponse({
        "status": "error",
        "message": "Validation failed",
        "errors": validation_result['errors'],
        "warnings": validation_result.get('warnings', [])
    }, status=400)

# Sanitize data before saving
sanitized_data = sanitize_signal_data(data)
```

### 4. ZenBot Scoring Enhancements
Create: `bot/management/commands/zenbot_train_score_model.py`
```python
# Uses existing ScoringWeights model
# Analyzes recent TradeJournal data
# Updates weights based on factor correlation with outcomes
# Command: python manage.py zenbot_train_score_model --window-days 30
```

### 5. Backtesting Module  
Create: `analytics/backtester.py`
```python
class TradeBacktester:
    def __init__(self, signals_queryset, initial_balance=10000, risk_per_trade=0.01):
        pass
    
    def simulate(self):
        # Iterate through signals chronologically
        # Simulate entry, SL/TP hits
        # Track equity curve
        # Return metrics dict
        pass
    
    def get_equity_curve(self):
        # Returns array of {date, equity} for Chart.js
        pass
```

### 6. Support System Upgrades
Update `support/models.py`:
```python
class SupportThread(models.Model):
    signal = models.ForeignKey(Signal, null=True, blank=True, on_delete=models.SET_NULL)
    
    def get_unread_count_for_user(user):
        return SupportThread.objects.filter(
            user=user,
            has_unread_admin_message=True
        ).count()
```

### 7. Bot/ZenBot Enhancements
Create: `bot/views.py` - `/bot/ask/` endpoint
```python
@csrf_exempt
@require_http_methods(["POST"])
def bot_ask(request):
    data = json.loads(request.body)
    prompt = data.get('prompt', '')
    
    # Parse commands
    if prompt.startswith('/score'):
        signal_id = extract_id(prompt)
        return get_signal_score(signal_id)
    elif prompt.startswith('/prop status'):
        return get_prop_status(request.user)
    elif prompt.startswith('/strategy stats'):
        return get_strategy_stats(request.user)
    
    # Save to BotChatHistory
    BotChatHistory.objects.create(
        user=request.user,
        prompt=prompt,
        response=response
    )
```

Create model:
```python
class BotChatHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### 8. Dashboard Improvements
Update `signals/templates/signals/dashboard.html`:
- Add strategy filter dropdown
- Add regime filter dropdown  
- Add AI score range slider (min/max)
- Create modal template for signal details
- Add Prop Status bar component

### 9. Webhook System Enhancement
Update `signals/models.py` WebhookConfig:
```python
class WebhookConfig(models.Model):
    hmac_secret = models.CharField(max_length=255, blank=True)
    
    def generate_hmac_secret(self):
        import secrets
        self.hmac_secret = secrets.token_urlsafe(32)
        self.save()
```

Add webhook logging in views:
```python
webhook_logger = logging.getLogger('webhook')
webhook_logger.info(f"Webhook received: {request.body.decode('utf-8')}")
```

### 10. Documentation Updates
Create: `docs/generate_strategy_docs.py`
```python
def generate_strategy_documentation():
    strategies = Signal.objects.values('strategy').distinct()
    for strategy in strategies:
        # Generate markdown doc with stats
        # Include win rate, best timeframes, best sessions
        # Save to docs/strategies/{strategy_name}.md
```

Update QUICK_START.md with:
- Environment setup section
- .env configuration guide
- Rate limiting details
- Security best practices

---

## Installation Steps

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings

# 3. Create logs directory
mkdir -p logs

# 4. Run migrations
python3 manage.py makemigrations
python3 manage.py migrate

# 5. Create superuser (if needed)
python3 manage.py createsuperuser

# 6. Run aggregation (optional)
python3 manage.py aggregate_daily_performance

# 7. Start server
python3 manage.py runserver
```

---

## Cron Setup (Optional)

Add to crontab for daily aggregation:
```bash
crontab -e

# Add line:
0 1 * * * cd /Users/macbook/zenithedge_trading_hub && python3 manage.py aggregate_daily_performance >> logs/cron.log 2>&1
```

---

## Testing Commands

```bash
# Test validation
python3 manage.py shell
>>> from signals.signal_validator import validate_signal_data
>>> data = {'symbol': 'EURUSD', 'side': 'buy', 'price': 1.1000, 'sl': 1.0950, 'tp': 1.1100, 'confidence': 75, 'strategy': 'Test', 'regime': 'Trend', 'timeframe': '1h'}
>>> validate_signal_data(data)

# Test aggregation
python3 manage.py aggregate_daily_performance --date 2025-11-09

# Test backtest (after implementing)
python3 manage.py shell
>>> from analytics.backtester import TradeBacktester
>>> from signals.models import Signal
>>> signals = Signal.objects.filter(strategy='ZenithEdge')
>>> bt = TradeBacktester(signals)
>>> results = bt.simulate()
```

---

## Key Improvements Summary

✅ **Security**: Environment variables, rate limiting, HTTPS enforcement, security headers
✅ **Performance**: Database indexes, cached aggregations, optimized queries  
✅ **Validation**: Comprehensive SL/TP checks, confidence validation, symbol format
🚧 **Scoring**: Strategy-specific weights, training commands, enhanced explanations
🚧 **Backtesting**: Full simulation engine with equity curves
🚧 **Dashboard**: Enhanced filters, signal modals, prop status bar
🚧 **Support**: Signal attachments, unread badges
🚧 **Bot**: Chat history, command interface, admin review panel
🚧 **Docs**: Auto-generated strategy docs, updated quick start guide

---

**Implementation Status: 30% Complete**
**Time to Complete Remaining: ~4-6 hours**

All foundation work is complete. Remaining items are feature additions that can be implemented incrementally without breaking existing functionality.
