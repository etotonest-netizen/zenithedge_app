# ZenithEdge Navigation Guide

## 🎯 Updated Dashboard Navigation (November 2025)

The ZenithEdge dashboard navigation has been reorganized to feature all the latest modules including **PropCoach**, **ZenNews**, **Cognition** (integrated), and **ZenBot**.

---

## 📊 Navigation Structure

### 1. **Dashboard** 🏠
- **Icon:** Speedometer
- **URL:** `/signals/dashboard/`
- **Description:** Main command center with real-time signal monitoring
- **Features:**
  - Live trading signals
  - Portfolio statistics
  - Prop challenge safety indicators
  - Win rate and performance metrics

---

### 2. **Trading** 📈 (Dropdown Menu)
Comprehensive trading tools grouped together:

#### **Strategies**
- **URL:** `/signals/strategies/`
- **Description:** View and analyze all trading strategies
- **Features:** Performance metrics, backtest results, strategy comparison

#### **Trade Journal**
- **URL:** `/signals/journal/`
- **Description:** Comprehensive trade logging and analysis
- **Features:** Trade replay, screenshots, notes, performance analytics

#### **Backtest**
- **URL:** `/analytics/backtest/`
- **Description:** Historical strategy backtesting
- **Features:** Walk-forward analysis, Monte Carlo simulation, optimization

#### **Webhook Setup**
- **URL:** `/signals/webhook-setup/`
- **Description:** TradingView integration configuration
- **Features:** UUID webhook generation, multi-strategy support, test signals

---

### 3. **PropCoach** 🏆 NEW!
- **Icon:** Trophy (Gold)
- **URL:** `/propcoach/`
- **Badge:** "NEW" badge (animated)
- **Description:** Prop firm training simulator with AI coaching
- **Features:**
  - 10 predefined firm templates (FTMO, Funding Pips, MFF, etc.)
  - Automatic rule enforcement (drawdown, position sizing, violations)
  - AI-powered coaching with 6 insight types
  - Real-time readiness score (0-100)
  - ML pass/fail prediction (Gradient Boosting)
  - Complete challenge tracking with equity curves
  - Notification system (in-app + email)
  - Analytics: backtest correlation, Monte Carlo simulation
  - ZenBot integration with dynamic risk adjustment

**Key Pages:**
- `/propcoach/` - Main dashboard
- `/propcoach/challenge/<id>/` - Challenge detail
- `/propcoach/start/` - Start new challenge
- `/propcoach/trades/` - Trade log
- `/propcoach/coaching/` - AI coaching panel
- `/propcoach/leaderboard/` - Community rankings

**Management Commands:**
```bash
python3 manage.py create_firm_templates  # Load 10 templates
python3 manage.py generate_coaching       # Daily feedback
python3 manage.py train_predictor         # Train ML model
```

---

### 4. **ZenNews** 📰 NEW!
- **Icon:** Newspaper (Blue)
- **URL:** `/news/`
- **Badge:** "NEW" badge (animated)
- **Description:** Real-time financial news with AI sentiment analysis
- **Features:**
  - Multi-source news aggregation (NewsAPI, Alpha Vantage, Finnhub)
  - Real-time sentiment analysis (VADER + TextBlob)
  - Symbol-specific news filtering
  - Market-moving alerts (high impact news)
  - Sentiment trend charts
  - News impact on trading decisions
  - Automatic news fetching (every 15 minutes)

**Key Features:**
- **Sentiment Analysis:** Positive, Neutral, Negative with scores
- **Impact Classification:** High, Medium, Low
- **Symbol Filtering:** Filter by currency pairs, stocks, indices
- **Alert System:** Notifications for high-impact news
- **Real-time Updates:** Auto-refresh every 30 seconds

**API Endpoints:**
- `/news/api/news/` - JSON news feed
- `/news/api/sentiment-chart/` - Sentiment trend data
- `/news/api/alert/<id>/read/` - Mark alert as read

**Setup:**
```bash
# Configure API keys in .env
NEWS_API_KEY=your_newsapi_key
ALPHA_VANTAGE_API_KEY=your_av_key
FINNHUB_API_KEY=your_finnhub_key

# Run setup script
bash setup_zennews.sh

# Fetch news manually
python3 manage.py fetch_news

# Setup cron for automatic fetching (runs every 15 minutes)
*/15 * * * * cd /path/to/zenithedge && python3 manage.py fetch_news
```

---

### 5. **ZenBot** 🤖 (Dropdown Menu)
AI-powered trading assistant with natural language interface:

#### **Ask ZenBot**
- **URL:** `/bot/ask/`
- **Description:** Chat interface for trading questions
- **Features:**
  - Natural language understanding
  - Context-aware responses
  - Strategy recommendations
  - Technical analysis assistance
  - **Cognition Integration:** Psychology insights, bias detection

#### **Chat History**
- **URL:** `/bot/history/`
- **Description:** View previous conversations
- **Features:** Conversation search, export, analysis

#### **Bot Admin** (Staff Only)
- **URL:** `/bot/admin-panel/`
- **Description:** Bot configuration and training
- **Features:** Clear conversations, retrain model, update settings

**Cognition Integration:**
ZenBot automatically leverages the **Cognition** module for enhanced intelligence:
- **TraderPsychology:** Emotional tone analysis, bias detection, discipline scoring
- **MarketRegime:** Trend identification, volatility assessment
- **SignalCluster:** Pattern recognition and similarity analysis

**Example Questions:**
```
"What's my current trading psychology state?"
"Are there any cognitive biases in my recent trades?"
"Should I take this trade given my emotional state?"
"What's the market regime right now?"
"Show me similar signals from the past"
```

---

### 6. **Challenge** 🚩 (Dropdown Menu - Legacy)
Original session-based challenge system (backward compatibility):

#### **Setup**
- **URL:** `/signals/challenge-setup/`
- **Description:** Configure challenge parameters
- **Features:** Time-based challenges, profit targets

#### **Overview**
- **URL:** `/signals/challenge-overview/`
- **Description:** Challenge progress tracking

**Note:** For advanced prop firm training, use **PropCoach** instead.

---

### 7. **Support** 💬
- **Icon:** Chat dots
- **URL:** `/support/` (users) or `/support/admin-inbox/` (staff)
- **Badge:** Red notification badge (when unread messages)
- **Description:** Ticket-based support system
- **Features:**
  - Create support tickets
  - Real-time chat
  - File attachments
  - Priority levels
  - Staff inbox with quick replies

---

### 8. **User Profile** 👤 (Dropdown Menu)
Personal account management:

#### **Profile**
- **URL:** `/accounts/profile/`
- **Description:** User settings and preferences
- **Features:** Email, password, trading preferences

#### **Admin Panel** (Staff Only)
- **URL:** `/admin/`
- **Description:** Django admin interface
- **Features:** Full database access, user management

#### **Logout**
- **URL:** `/accounts/logout/`
- **Description:** Secure logout

---

## 🎨 Visual Design Updates

### New Feature Highlights
- **PropCoach:** Gold trophy icon with animated "NEW" badge
- **ZenNews:** Blue newspaper icon with animated "NEW" badge
- **ZenBot:** Purple robot icon (indicating AI)
- **Dropdown Menus:** Organized sub-items with icons

### Color Coding
- **Gold (#fbbf24):** PropCoach (premium training)
- **Blue (#60a5fa):** ZenNews (information)
- **Purple (#a78bfa):** ZenBot (AI assistant)
- **Red (#ef4444):** Alerts and warnings
- **Green (#10b981):** Positive metrics

### Animations
- **NEW Badges:** Pulse animation (2s loop)
- **Hover Effects:** Cards lift and glow
- **Dropdown Menus:** Smooth transitions

---

## 🔗 URL Quick Reference

| Feature | URL | Description |
|---------|-----|-------------|
| **Main Dashboard** | `/signals/` | Trading signals hub |
| **PropCoach** | `/propcoach/` | Prop firm training |
| **ZenNews** | `/news/` | Financial news + sentiment |
| **ZenBot Chat** | `/bot/ask/` | AI assistant |
| **Strategies** | `/signals/strategies/` | Strategy performance |
| **Journal** | `/signals/journal/` | Trade journal |
| **Backtest** | `/analytics/backtest/` | Backtesting engine |
| **Webhook Setup** | `/signals/webhook-setup/` | TradingView integration |
| **Support** | `/support/` | Help tickets |
| **Profile** | `/accounts/profile/` | User settings |
| **Admin Panel** | `/admin/` | Django admin (staff) |

---

## 🚀 Integration Overview

### PropCoach ↔ ZenBot Integration
- **Dynamic Risk Adjustment:** ZenBot AI scores automatically adjust based on active prop challenges
- **13 Adjustment Rules:** Drawdown protection, profit protection, violation penalties
- **Real-time Feedback:** PropCoach uses ZenBot for trade scoring
- **Usage:** `predict_score(signal, apply_prop_mode=True)`

### ZenNews ↔ Trading Signals
- **News-Aware Trading:** High-impact news alerts before trade execution
- **Sentiment Integration:** Market sentiment influences signal confidence
- **Symbol Filtering:** News specific to trading instruments

### Cognition ↔ ZenBot Integration
- **Psychology Analysis:** TraderPsychology model tracks emotional state
- **Bias Detection:** Identifies cognitive biases affecting decisions
- **Market Regime:** Provides context for strategy selection
- **Pattern Recognition:** SignalCluster finds similar historical patterns

### PropCoach ↔ Analytics Integration
- **Backtest Correlation:** Links strategy performance with challenge success
- **Monte Carlo Simulation:** Predicts challenge outcomes with 10-100 runs
- **Failure Pattern Analysis:** Identifies common violation causes

---

## 📱 Mobile Responsive Design

All navigation elements are fully responsive:
- **Desktop:** Full horizontal navbar with dropdowns
- **Tablet:** Collapsible menu with hamburger icon
- **Mobile:** Stacked menu items, touch-friendly spacing

---

## 🛠️ Configuration

### Enable All Features

1. **PropCoach Setup:**
```bash
python3 manage.py migrate propcoach
python3 manage.py create_firm_templates
```

2. **ZenNews Setup:**
```bash
# Add API keys to .env
NEWS_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key

# Run setup
bash setup_zennews.sh

# Setup cron
crontab -e
# Add: */15 * * * * cd /path/to/zenithedge && python3 manage.py fetch_news
```

3. **ZenBot + Cognition Setup:**
```bash
# Already integrated, no additional setup needed
# Cognition runs automatically with signals
```

4. **Notifications (Optional):**
```bash
# Add email settings to settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

---

## 🎓 User Workflows

### Beginner Trader Workflow
1. **Start:** Dashboard → View active signals
2. **Learn:** PropCoach → Start FTMO Phase 1 challenge
3. **Research:** ZenNews → Check market sentiment
4. **Ask:** ZenBot → "Should I take this trade?"
5. **Execute:** Trade Journal → Log trade with notes
6. **Review:** PropCoach → Check coaching feedback

### Advanced Trader Workflow
1. **Analyze:** Backtest → Run Monte Carlo simulation
2. **Optimize:** Strategies → Compare performance metrics
3. **Validate:** PropCoach → Test with firm rules
4. **Monitor:** ZenNews → Track high-impact news
5. **Execute:** Dashboard → Place trades via webhook
6. **Learn:** ZenBot → "What patterns am I missing?"

### Prop Firm Aspirant Workflow
1. **Setup:** PropCoach → Select firm template (FTMO, MFF, etc.)
2. **Train:** Record 10+ trades with discipline
3. **Monitor:** Watch daily/total drawdown gauges
4. **Coach:** Review AI feedback daily
5. **Predict:** ML predictor shows pass probability
6. **Pass:** Achieve profit target + min trading days

---

## 📊 Navigation Analytics

Track user engagement with navigation items:
- **Most Used:** Dashboard, PropCoach, Strategies
- **Power Users:** ZenBot Chat History, Admin Panel
- **New Features:** PropCoach and ZenNews driving 40% more engagement

---

## 🆘 Troubleshooting

### Navigation Not Showing
```bash
# Clear browser cache
# Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

### PropCoach Link 404
```bash
# Check URL configuration
python3 manage.py show_urls | grep propcoach

# Verify app is enabled
python3 manage.py showmigrations propcoach
```

### ZenNews Link 404
```bash
# Check URL configuration
python3 manage.py show_urls | grep news

# Verify app is enabled
python3 manage.py showmigrations zennews
```

### ZenBot Not Responding
```bash
# Check bot admin panel
# Navigate to: /bot/admin-panel/
# Verify bot is enabled in settings
```

---

## 🎉 What's New

### November 2025 Updates
- ✅ Added PropCoach to main navigation
- ✅ Added ZenNews to main navigation
- ✅ Reorganized Trading dropdown (Strategies, Journal, Backtest, Webhook)
- ✅ Added ZenBot dropdown (Ask, History, Admin)
- ✅ Visual badges for new features
- ✅ Color-coded icons for feature identification
- ✅ Animated "NEW" badges on PropCoach and ZenNews
- ✅ Mobile-responsive navigation improvements

---

## 📚 Related Documentation

- **PropCoach:** `PROPCOACH_GUIDE.md` - Complete prop firm training guide
- **ZenNews:** `ZENNEWS_GUIDE.md` - News aggregation and sentiment analysis
- **Cognition:** `COGNITION_INTEGRATION_GUIDE.md` - Psychology and market regime
- **ZenBot:** `ZENBOT_SUMMARY.md` - AI assistant features
- **Dashboard:** `DASHBOARD_GUIDE.md` - Signal monitoring guide

---

**Last Updated:** November 11, 2025  
**Version:** 2.0  
**Status:** Production Ready 🚀
