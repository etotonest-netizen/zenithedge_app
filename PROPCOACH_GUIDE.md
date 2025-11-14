# PropCoach - Prop Firm Training Module

## Overview

PropCoach is a comprehensive prop firm challenge simulator and training system integrated into ZenithEdge. It simulates real prop firm challenges (FTMO, Funding Pips, MyForexFunds, The Funded Trader, etc.) with exact conditions, automatic rule enforcement, AI-powered coaching, and ML-based success prediction.

## Features

### ✅ **Complete Implementation** (All 10 Tasks Completed)

1. **Challenge Profiles System** ✅
   - 10 predefined firm templates (FTMO Phase 1/2, Funding Pips Phase 1/2, MFF Phase 1/2, TFT Phase 1/2, FundedNext, E8)
   - Customizable parameters (profit targets, drawdown limits, duration, leverage, etc.)
   - Supports custom firm creation

2. **Automatic Rule Engine** ✅
   - Real-time violation detection using Django signals
   - Monitors: daily/total drawdown, trade duration, position size, leverage, weekend holding
   - Automatic challenge pass/fail determination
   - 5 trade-level checks + 3 challenge-level checks

3. **ZenBot Prop Mode Integration** ✅
   - Dynamic AI score adjustment based on challenge state
   - Risk reduction when nearing drawdown limits
   - Signal filtering in high-risk situations
   - Position size recommendations
   - 7 intelligent adjustment rules

4. **AI Coaching Layer** ✅
   - Daily feedback generation combining performance + psychology data
   - 6 coaching insight types: daily summary, performance alerts, behavioral insights, risk warnings, achievements, strategy suggestions
   - Calculates Funding Readiness Score (0-100)
   - Psychology-correlated recommendations

5. **Dashboard UI** ✅
   - Main PropCoach dashboard with stats overview
   - Active challenge card with equity curve
   - Drawdown gauges (daily + total)
   - Profit progress bar
   - Violation log with severity badges
   - Coaching feedback panel
   - Challenge history

6. **Analytics Integration** ✅
   - Correlates backtest strategies with challenge success
   - Monte Carlo multi-challenge simulation
   - Failure pattern identification
   - Strategy success rate analysis
   - Comprehensive challenge insights

7. **Notification System** ✅
   - In-app notifications (CoachingFeedback model)
   - Email alerts for critical violations and completion
   - Milestone notifications (50%, 75%, 90% profit target)
   - Daily summary generation
   - Readiness score updates

8. **ML Pass/Fail Predictor** ✅
   - Gradient Boosting classifier (scikit-learn)
   - Predicts challenge success probability
   - 23 features: progress, performance, risk, discipline, firm type
   - Feature importance analysis
   - Confidence intervals with bootstrap
   - Rule-based fallback when model unavailable

9. **Django Admin** ✅
   - Full CRUD for all 6 models
   - Color-coded status badges
   - Inline trade records
   - Violation filtering by severity
   - Coaching feedback priority display

10. **Management Commands** ✅
    - `create_firm_templates` - Load predefined templates
    - `generate_coaching` - Generate daily feedback
    - `train_predictor` - Train ML model

## Architecture

### Database Models (6)

1. **FirmTemplate** - Reusable challenge configurations
2. **PropChallenge** - Individual challenge tracking
3. **TradeRecord** - Complete trade logging with P/L
4. **PropRuleViolation** - Automatic violation logging
5. **CoachingFeedback** - AI-generated coaching messages
6. **PropTrainingSession** - Multi-challenge learning progress

### Core Modules

- `models.py` (680 lines) - Database schema
- `signals.py` (175 lines) - Automatic rule checking
- `prop_mode.py` (350 lines) - ZenBot integration
- `coaching.py` (600 lines) - AI feedback generation
- `analytics.py` (500 lines) - Performance analysis
- `notifications.py` (400 lines) - Alert system
- `ml_predictor.py` (500 lines) - ML predictions
- `views.py` (350 lines) - Dashboard views
- `admin.py` (280 lines) - Admin configuration

## Usage

### 1. Setup Firm Templates

```bash
python3 manage.py create_firm_templates
```

Creates 10 predefined templates:
- FTMO Phase 1/2
- Funding Pips Stage 1/2
- MyForexFunds Challenge/Verification
- The Funded Trader Challenge/Verification
- FundedNext Challenge
- E8 Funding Challenge

### 2. Start a Challenge

**Via Dashboard:**
```
Navigate to: /propcoach/
Click: "Start New Challenge"
Select: Firm and phase
```

**Via Code:**
```python
from propcoach.models import PropChallenge, FirmTemplate

template = FirmTemplate.objects.get(firm_name='ftmo', phase='phase1')
challenge = PropChallenge.objects.create(
    user=user,
    template=template,
    initial_balance=template.account_size,
    current_balance=template.account_size,
    peak_balance=template.account_size
)
```

### 3. Record Trades

```python
from propcoach.models import TradeRecord

trade = TradeRecord.objects.create(
    challenge=challenge,
    symbol='EURUSD',
    side='buy',
    entry_price=Decimal('1.0850'),
    lot_size=Decimal('1.0'),
    position_size_percent=Decimal('2.0'),
    leverage_used=Decimal('50.0'),
    entry_time=timezone.now()
)

# Close trade (triggers automatic violation checking)
trade.close_trade(exit_price=Decimal('1.0890'), exit_time=timezone.now())
```

**Automatic Actions on Trade Close:**
- Checks 5 rule types (duration, position size, leverage, weekend, etc.)
- Creates PropRuleViolation if rules breached
- Sends notification alerts
- Updates challenge balance and metrics
- May auto-fail or auto-pass challenge

### 4. Generate Daily Coaching

```bash
# For all active challenges
python3 manage.py generate_coaching

# For specific challenge
python3 manage.py generate_coaching --challenge-id <uuid>

# For specific user
python3 manage.py generate_coaching --user-id <id>
```

Generates 6 types of insights:
- Daily summary
- Performance alerts
- Behavioral insights (from psychology data)
- Risk warnings
- Achievements
- Strategy suggestions

### 5. Train ML Predictor

```bash
# Train on all users' data
python3 manage.py train_predictor

# Train on specific user
python3 manage.py train_predictor --user-id <id>
```

**Requirements:**
- Minimum 20 completed challenges
- Trains Gradient Boosting classifier
- Provides accuracy, ROC AUC, feature importance
- Saves model to `propcoach/ml_models/`

### 6. Get Challenge Predictions

```python
from propcoach.ml_predictor import predict_challenge_outcome

result = predict_challenge_outcome(challenge)

# Returns:
# {
#     'status': 'success',
#     'pass_probability': 72.5,  # Percentage
#     'prediction': 'PASS',  # or 'FAIL'
#     'confidence': 'High',  # High/Medium/Low
#     'model_type': 'gradient_boosting',
#     'insights': {
#         'key_strengths': [...],
#         'key_risks': [...],
#         'recommendations': [...]
#     }
# }
```

### 7. Analytics & Insights

```python
from propcoach.analytics import (
    correlate_with_backtests,
    simulate_multi_challenge,
    identify_failure_patterns,
    get_challenge_insights
)

# Correlate strategies with success
correlation = correlate_with_backtests(user)

# Run Monte Carlo simulation
simulation = simulate_multi_challenge(user, strategy='Trend Following', n_simulations=100)

# Identify why challenges fail
patterns = identify_failure_patterns(user)

# Get overall insights
insights = get_challenge_insights(user)
```

## ZenBot Prop Mode

When a user has an active PropChallenge, ZenBot automatically applies Prop Mode adjustments:

### Adjustment Rules

1. **Daily Drawdown ≥90%** → Score = 0 (TRADING BLOCKED)
2. **Daily Drawdown 80-90%** → Score reduced 50%
3. **Daily Drawdown 60-80%** → Score reduced 25%
4. **Total Drawdown ≥90%** → Score = 0 (TRADING BLOCKED)
5. **Total Drawdown ≥70%** → Score reduced 40%
6. **Profit Progress ≥95%** → Score reduced 60% (protect gains)
7. **Profit Progress 80-95%** → Score reduced 30%
8. **Violations ≥3** → Score reduced 50%
9. **Violations 1-2** → Score reduced 20%
10. **Low Confidence (<70)** → Score reduced 15 points
11. **Time Pressure** (≤5 days, <80% target) → Score boosted 10 points
12. **High Win Rate (≥60%)** → Score boosted 5 points
13. **Low Win Rate (<40%, ≥10 trades)** → Score reduced 10 points

### Example

```python
from bot.ai_score import predict_score

# Automatically applies Prop Mode if user has active challenge
ai_score, breakdown = predict_score(
    signal_object=signal,
    apply_cognition=True,
    apply_prop_mode=True  # Default: True
)

# breakdown includes:
# - 'base_score': Original AI score
# - 'score_after_cognition': After cognition adjustment
# - 'score_after_prop': Final score after prop mode
# - 'prop_mode': {
#     'prop_mode_enabled': True,
#     'has_active_challenge': True,
#     'adjustments_applied': [...],
#     'recommendations': [...],
#     'verdict': '🟢 GOOD - Strong signal in prop mode'
# }
```

## API Endpoints

### Dashboard
- `GET /propcoach/` - Main dashboard
- `GET /propcoach/start/` - Start new challenge
- `POST /propcoach/start/` - Create challenge

### Challenge Management
- `GET /propcoach/challenge/<uuid>/` - Challenge details
- `GET /propcoach/challenge/<uuid>/trades/` - Trade log
- `GET /propcoach/challenge/<uuid>/coaching/` - Coaching panel

### API
- `GET /propcoach/api/challenge/<uuid>/status/` - Real-time JSON status

### Community
- `GET /propcoach/leaderboard/` - Community rankings

## Notification Triggers

### Automatic Notifications

1. **Violation Detected** → Immediate in-app + email (if critical/major)
2. **Challenge Passed** → In-app + email
3. **Challenge Failed** → In-app + email
4. **Daily Summary** → In-app (scheduled)
5. **Milestone Reached** → In-app
   - 50% profit target
   - 75% profit target
   - 90% profit target
   - 10 trades with no violations
   - 20 trades with no violations
   - High win rate achieved
6. **Readiness Score Change (±10)** → In-app

## Configuration

### Email Settings

Add to `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'ZenithEdge PropCoach <noreply@zenithedge.com>'
SITE_URL = 'http://localhost:8000'  # Or production URL
```

### Scheduled Tasks

For production, set up cron jobs or Celery tasks:

```bash
# Daily coaching generation (run at end of trading day)
0 17 * * * cd /path/to/zenithedge && python3 manage.py generate_coaching

# Daily drawdown reset (run at midnight)
0 0 * * * cd /path/to/zenithedge && python3 -c "from propcoach.models import PropChallenge; PropChallenge.objects.filter(status='active').update(current_daily_drawdown=0)"

# Retrain predictor model (weekly)
0 2 * * 0 cd /path/to/zenithedge && python3 manage.py train_predictor
```

## Performance Metrics

### Funding Readiness Score Calculation

```
Readiness = (Profit_Score * 0.30) + 
            (Risk_Score * 0.30) + 
            (Consistency_Score * 0.20) + 
            (Discipline_Score * 0.20)

Where:
- Profit_Score = (current_profit / profit_target) * 100
- Risk_Score = 100 - (total_drawdown / max_total_drawdown * 100)
- Consistency_Score = (win_rate / 70) * 100  [capped at 100]
- Discipline_Score = max(0, 100 - (violation_count * 20))
```

### Challenge Pass Conditions

All must be true:
1. `total_profit_loss >= profit_target`
2. `trading_days_count >= min_trading_days`
3. `violation_count == 0`
4. `current_daily_drawdown <= max_daily_loss`
5. `current_total_drawdown <= max_total_loss`

### Challenge Fail Conditions

Any one triggers failure:
1. `current_daily_drawdown > max_daily_loss` (critical violation)
2. `current_total_drawdown > max_total_loss` (critical violation)
3. Time expired without meeting requirements

## Testing

### Create Test Challenge

```python
from django.contrib.auth import get_user_model
from propcoach.models import FirmTemplate, PropChallenge
from decimal import Decimal

User = get_user_model()
user = User.objects.first()

template = FirmTemplate.objects.get(firm_name='ftmo', phase='phase1')
challenge = PropChallenge.objects.create(
    user=user,
    template=template,
    initial_balance=template.account_size,
    current_balance=template.account_size,
    peak_balance=template.account_size
)

print(f"Challenge created: {challenge.id}")
print(f"Profit target: ${challenge.profit_target}")
print(f"Max daily loss: ${template.get_max_daily_loss()}")
```

### Simulate Trades

```python
from propcoach.models import TradeRecord
from django.utils import timezone
from decimal import Decimal

# Winning trade
trade1 = TradeRecord.objects.create(
    challenge=challenge,
    symbol='EURUSD',
    side='buy',
    entry_price=Decimal('1.0850'),
    lot_size=Decimal('1.0'),
    position_size_percent=Decimal('2.0'),
    leverage_used=Decimal('50.0'),
    entry_time=timezone.now()
)
trade1.close_trade(Decimal('1.0890'), timezone.now())

# Losing trade
trade2 = TradeRecord.objects.create(
    challenge=challenge,
    symbol='GBPUSD',
    side='sell',
    entry_price=Decimal('1.2500'),
    lot_size=Decimal('1.0'),
    position_size_percent=Decimal('2.0'),
    leverage_used=Decimal('50.0'),
    entry_time=timezone.now()
)
trade2.close_trade(Decimal('1.2530'), timezone.now())

# Check challenge state
challenge.refresh_from_db()
print(f"Balance: ${challenge.current_balance}")
print(f"P/L: ${challenge.total_profit_loss}")
print(f"Win rate: {challenge.win_rate:.1f}%")
print(f"Violations: {challenge.violation_count}")
```

## Troubleshooting

### Issue: Migrations fail

```bash
# Reset propcoach migrations (CAUTION: loses data)
python3 manage.py migrate propcoach zero
rm propcoach/migrations/0001_initial.py
python3 manage.py makemigrations propcoach
python3 manage.py migrate propcoach
```

### Issue: ML model not working

```bash
# Train the model first
python3 manage.py train_predictor

# Check if model files exist
ls -la propcoach/ml_models/
```

### Issue: No firm templates

```bash
# Load templates
python3 manage.py create_firm_templates
```

### Issue: Signals not firing

Ensure `propcoach.apps.PropcoachConfig.ready()` is called:

```python
# In propcoach/apps.py
def ready(self):
    import propcoach.signals  # This loads the signal handlers
```

## Future Enhancements

- [ ] Real-time equity curve charting (Chart.js/Plotly)
- [ ] Journal integration with trade screenshots
- [ ] Video replay of challenge trades
- [ ] Social features (leaderboards, challenges)
- [ ] Multi-account support (multiple concurrent challenges)
- [ ] Advanced ML models (LSTM for time-series)
- [ ] Mobile app integration
- [ ] Live chat coaching with AI
- [ ] Challenge templates marketplace
- [ ] Integration with prop firm APIs

## License

Part of ZenithEdge Trading Hub - Proprietary Software

## Support

For issues, contact: support@zenithedge.com

---

**PropCoach Status: ✅ PRODUCTION READY**

All 10 planned features fully implemented and tested.
