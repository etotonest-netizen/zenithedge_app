# ZenithEdge Intelligence Console

## 🚀 Quick Links
- **[TradingView Setup Guide](TRADINGVIEW_SETUP_GUIDE.md)** - Complete integration guide
- **[Pine Script Template](TRADINGVIEW_INDICATOR_TEMPLATE.pine)** - Copy-paste indicator code
- **[Quick Reference](QUICK_REFERENCE.md)** - API & Command reference

A comprehensive Django-based AI Decision Intelligence Console with market analysis, contextual insights, and performance analytics.

## Project Overview

**ZenithEdge Intelligence Console** is a professional market intelligence platform designed for traders who need AI-powered market analysis, contextual insights, and comprehensive performance tracking. Our system transforms raw market data into actionable intelligence through advanced AI contextualizers and multi-layer validation.

## Key Features

### 🎯 Core Functionality
- **Market Intelligence Engine** - Receive and contextualize market data from TradingView webhooks
- **AI Insight Index** - ML-based quality scoring for incoming market analysis
- **Contextual Validation Pipeline** - Multi-layer validation with narrative generation
- **Risk Control System** - Configurable limits for daily loss, consecutive losers, and analysis frequency
- **Prop Challenge Integration** - FTMO, FTMO Swing, MyForexFunds, and The5ers support
- **Analysis Journal** - Comprehensive market analysis logging and tracking
- **Dynamic Backtesting** - Test analysis strategies with historical market data
- **Performance Analytics** - Detailed statistics and insight quality tracking

### 🔐 Authentication & Security
- Custom user model with email-based authentication
- API key authentication for webhook endpoints
- Session management with configurable timeouts
- Role-based access control (Traders, Staff, Admins)

### 📊 Analytics & Reporting
- Win rate and profit factor calculation
- Maximum drawdown tracking
- Risk-reward ratio analysis
- Interactive charts with Chart.js
- CSV export functionality

## Project Structure

```
zenithedge_trading_hub/
├── accounts/          # User authentication and management
├── signals/           # Market insights and contextual validation
├── bot/              # AI configuration and automation
├── analytics/        # Backtesting and performance analysis
├── zenithedge/       # Project settings and configuration
├── docs/             # Comprehensive documentation
├── staticfiles/      # Static assets (CSS, JS, images)
└── db.sqlite3        # SQLite database
```

## Installation

```bash
# Navigate to project directory
cd /tmp/zenithedge_trading_hub

# Install dependencies
pip install django pillow

# Run migrations
python3 manage.py migrate

# Create superuser
python3 manage.py createsuperuser

# Start development server
python3 manage.py runserver 0.0.0.0:8000
```

## Access Points

- **Intelligence Console**: http://localhost:8000/signals/insights/
- **Legacy Dashboard**: http://localhost:8000/signals/dashboard/
- **Admin Panel**: http://localhost:8000/admin/
- **Backtesting**: http://localhost:8000/backtest/
- **Insights API**: http://localhost:8000/api/insights/
- **Webhook API**: http://localhost:8000/api/signals/webhook/?api_key=YOUR_KEY

## Default Credentials

- **Admin**: admin@zenithedge.com / admin123
- **Trader**: trader@zenithedge.com / trader123

## Documentation

Detailed guides available in the `/docs` directory:
- AI Trade Score Predictor
- Signal Validation Pipeline
- Dynamic Backtesting
- Webhook Configuration
- Session Rules & Filters

## Technology Stack

- **Framework**: Django 4.2.7
- **Database**: SQLite3
- **Frontend**: Bootstrap 5, Chart.js 4.4.0
- **Python**: 3.9+

## License

Proprietary - All rights reserved

## Version

Current Version: 1.0.0
Last Updated: November 9, 2025
