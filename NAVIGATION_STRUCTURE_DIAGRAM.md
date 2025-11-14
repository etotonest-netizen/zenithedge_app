# ZenithEdge Navigation Structure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         🏦 ZENITHEDGE DASHBOARD                                 │
│                         Trading Intelligence Platform                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  📊 Dashboard  │  📈 Trading ▼  │  🏆 PropCoach NEW  │  📰 ZenNews NEW  │     │
│  🤖 ZenBot ▼  │  🚩 Challenge ▼  │  💬 Support  │  👤 User ▼               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┬────────────────────┬──────────────────────────────────────┐
│                     │                    │                                      │
│  📊 DASHBOARD       │  📈 TRADING        │  🏆 PROPCOACH (NEW)                 │
│  ═════════════      │  ════════════      │  ═══════════════════                │
│                     │                    │                                      │
│  Main Hub           │  ├─ Strategies     │  Prop Firm Training Simulator       │
│  Real-time signals  │  ├─ Trade Journal  │                                      │
│  Portfolio stats    │  ├─ Backtest       │  Features:                          │
│  Win rate metrics   │  └─ Webhook Setup  │  • 10 Firm Templates                │
│  Safety indicators  │                    │  • Auto Rule Enforcement            │
│                     │  Core Trading      │  • AI Coaching (6 types)            │
│  /signals/          │  Features          │  • ML Pass/Fail Predictor           │
│                     │                    │  • Real-time Tracking               │
│                     │  /signals/         │  • Challenge Leaderboard            │
│                     │  /analytics/       │                                      │
│                     │                    │  /propcoach/                        │
│                     │                    │                                      │
├─────────────────────┼────────────────────┼──────────────────────────────────────┤
│                     │                    │                                      │
│  📰 ZENNEWS (NEW)   │  🤖 ZENBOT         │  🚩 CHALLENGE                       │
│  ════════════════   │  ═══════════       │  ══════════                         │
│                     │                    │                                      │
│  Financial News &   │  ├─ Ask ZenBot     │  ├─ Setup                          │
│  Sentiment Analysis │  ├─ Chat History   │  └─ Overview                        │
│                     │  └─ Bot Admin      │                                      │
│  Features:          │                    │  Legacy Challenge System            │
│  • Multi-source     │  AI Assistant      │  (Use PropCoach instead)            │
│  • Real-time        │  with Cognition    │                                      │
│  • Sentiment Score  │  Integration       │  /signals/challenge-setup/          │
│  • Impact Alerts    │                    │  /signals/challenge-overview/       │
│  • Symbol Filter    │  Psychology        │                                      │
│  • Trend Charts     │  Bias Detection    │                                      │
│                     │  Market Regime     │                                      │
│  /news/             │  Pattern Match     │                                      │
│                     │                    │                                      │
│                     │  /bot/ask/         │                                      │
│                     │  /bot/history/     │                                      │
│                     │                    │                                      │
├─────────────────────┼────────────────────┴──────────────────────────────────────┤
│                     │                                                           │
│  💬 SUPPORT         │  👤 USER MENU                                            │
│  ════════════       │  ══════════                                              │
│                     │                                                           │
│  Help & Tickets     │  ├─ Profile                                              │
│  Live Chat          │  ├─ Admin Panel (Staff)                                  │
│  File Attachments   │  ├─ Superuser Badge                                      │
│  Priority Levels    │  └─ Logout                                               │
│                     │                                                           │
│  /support/          │  /accounts/profile/                                      │
│                     │  /admin/                                                  │
│                     │  /accounts/logout/                                        │
│                     │                                                           │
└─────────────────────┴───────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
                            🔗 FEATURE INTEGRATIONS
═══════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  🏆 PROPCOACH  ←────→  🤖 ZENBOT                                              │
│                                                                                 │
│  PropCoach uses ZenBot for dynamic risk adjustment:                            │
│  • 13 Adjustment Rules (drawdown, profit, violations)                          │
│  • Real-time AI scoring based on challenge state                               │
│  • Automatic trade blocking when limits approached                             │
│                                                                                 │
│  Example: predict_score(signal, apply_prop_mode=True)                          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  📰 ZENNEWS  ←────→  📊 TRADING SIGNALS                                       │
│                                                                                 │
│  ZenNews provides market context for trading decisions:                        │
│  • High-impact news alerts before trade execution                              │
│  • Sentiment analysis influences signal confidence                             │
│  • Symbol-specific news filtering                                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  🧠 COGNITION  ←────→  🤖 ZENBOT                                              │
│                                                                                 │
│  Cognition powers ZenBot's psychological insights:                             │
│  • TraderPsychology: Emotional state tracking                                  │
│  • Bias Detection: Cognitive bias identification                               │
│  • Market Regime: Trend and volatility analysis                                │
│  • Pattern Recognition: Similar signal clustering                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  🏆 PROPCOACH  ←────→  📈 ANALYTICS                                           │
│                                                                                 │
│  PropCoach leverages Analytics for insights:                                   │
│  • Backtest Correlation: Strategy success in challenges                        │
│  • Monte Carlo Simulation: Challenge outcome predictions                       │
│  • Failure Pattern Analysis: Common violation causes                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
                            🎨 VISUAL DESIGN SYSTEM
═══════════════════════════════════════════════════════════════════════════════════

┌────────────────────┬───────────────┬──────────────────────────────────────────┐
│ FEATURE            │ COLOR         │ ICON                                     │
├────────────────────┼───────────────┼──────────────────────────────────────────┤
│ PropCoach          │ Gold          │ 🏆 Trophy + "NEW" badge (animated)      │
│                    │ #fbbf24       │ Premium training feature                 │
├────────────────────┼───────────────┼──────────────────────────────────────────┤
│ ZenNews            │ Blue          │ 📰 Newspaper + "NEW" badge (animated)   │
│                    │ #60a5fa       │ Information & intelligence               │
├────────────────────┼───────────────┼──────────────────────────────────────────┤
│ ZenBot             │ Purple        │ 🤖 Robot (AI-powered)                   │
│                    │ #a78bfa       │ Intelligent assistant                    │
├────────────────────┼───────────────┼──────────────────────────────────────────┤
│ Dashboard          │ White         │ 📊 Speedometer                          │
│                    │ Default       │ Central hub                              │
├────────────────────┼───────────────┼──────────────────────────────────────────┤
│ Trading            │ White         │ 📈 Graph Up                             │
│                    │ Default       │ Core trading features                    │
├────────────────────┼───────────────┼──────────────────────────────────────────┤
│ Support            │ White + Red   │ 💬 Chat + notification badge            │
│                    │ Badge #ef4444 │ Help system with alerts                  │
└────────────────────┴───────────────┴──────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
                            📱 RESPONSIVE LAYOUTS
═══════════════════════════════════════════════════════════════════════════════════

DESKTOP (>992px)
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ZenithEdge  Dashboard  Trading▼  PropCoach🏆  ZenNews📰  ZenBot🤖▼  Support  👤│
└─────────────────────────────────────────────────────────────────────────────────┘

TABLET (768px - 992px)
┌──────────────────────────────────┐
│ ZenithEdge            [☰ Menu]   │
└──────────────────────────────────┘
         ↓ Collapsed Menu
┌──────────────────────────────────┐
│ Dashboard                         │
│ Trading ▼                         │
│ PropCoach 🏆 NEW                 │
│ ZenNews 📰 NEW                   │
│ ZenBot 🤖 ▼                      │
│ Challenge ▼                       │
│ Support                           │
│ User 👤 ▼                        │
└──────────────────────────────────┘

MOBILE (<768px)
┌─────────────────┐
│ ZenithEdge [☰] │
└─────────────────┘
       ↓
┌─────────────────┐
│ Dashboard       │
├─────────────────┤
│ Trading ▼       │
│ • Strategies    │
│ • Journal       │
│ • Backtest      │
│ • Webhook       │
├─────────────────┤
│ PropCoach NEW   │
├─────────────────┤
│ ZenNews NEW     │
├─────────────────┤
│ ZenBot ▼        │
│ • Ask ZenBot    │
│ • History       │
│ • Admin         │
├─────────────────┤
│ Support         │
├─────────────────┤
│ User ▼          │
│ • Profile       │
│ • Admin Panel   │
│ • Logout        │
└─────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
                            🎯 USER WORKFLOWS
═══════════════════════════════════════════════════════════════════════════════════

BEGINNER TRADER JOURNEY
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌────────┐     ┌─────────┐
│Dashboard│ ──→ │PropCoach │ ──→ │ZenNews  │ ──→ │ZenBot  │ ──→ │Journal  │
└─────────┘     └──────────┘     └─────────┘     └────────┘     └─────────┘
   View             Start          Check           Ask if         Log the
  Signals          FTMO P1        Sentiment      good trade        trade

ADVANCED TRADER JOURNEY
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐     ┌────────┐
│Backtest │ ──→ │Strategies│ ──→ │PropCoach │ ──→ │ZenNews  │ ──→ │Execute │
└─────────┘     └──────────┘     └──────────┘     └─────────┘     └────────┘
  Monte Carlo     Compare         Test with       Monitor          Place via
  Simulation      Performance     Firm Rules      News Impact      Webhook

PROP FIRM ASPIRANT JOURNEY
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐     ┌────────┐
│PropCoach │ ──→ │Trade 10+ │ ──→ │AI Coach  │ ──→ │ML Pred. │ ──→ │Pass!   │
└──────────┘     └──────────┘     └──────────┘     └─────────┘     └────────┘
Select FTMO       Disciplined      Review          Check Pass       Achieve
Template          Trading          Feedback        Probability      Target


═══════════════════════════════════════════════════════════════════════════════════
                            🚀 QUICK LINKS REFERENCE
═══════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────┬──────────────────────────────────────────────────────┐
│ FEATURE                 │ PRIMARY URL                                          │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ 📊 Dashboard            │ /signals/                                            │
│ 🏆 PropCoach            │ /propcoach/                                          │
│ 📰 ZenNews              │ /news/                                               │
│ 🤖 ZenBot Ask           │ /bot/ask/                                            │
│ 🤖 ZenBot History       │ /bot/history/                                        │
│ 🤖 ZenBot Admin         │ /bot/admin-panel/                                    │
│ 📈 Strategies           │ /signals/strategies/                                 │
│ 📓 Trade Journal        │ /signals/journal/                                    │
│ 📊 Backtest             │ /analytics/backtest/                                 │
│ 📡 Webhook Setup        │ /signals/webhook-setup/                              │
│ 🚩 Challenge Setup      │ /signals/challenge-setup/                            │
│ 🚩 Challenge Overview   │ /signals/challenge-overview/                         │
│ 💬 Support              │ /support/                                            │
│ 👤 Profile              │ /accounts/profile/                                   │
│ ⚙️ Admin Panel          │ /admin/                                              │
└─────────────────────────┴──────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
                            ✅ IMPLEMENTATION STATUS
═══════════════════════════════════════════════════════════════════════════════════

[✅] Navigation structure reorganized
[✅] PropCoach menu item added with gold icon
[✅] ZenNews menu item added with blue icon
[✅] ZenBot dropdown created with purple icon
[✅] Trading features grouped into dropdown
[✅] Animated "NEW" badges implemented
[✅] Color coding applied to all features
[✅] Responsive design for mobile/tablet
[✅] Icons updated (Bootstrap Icons)
[✅] CSS animations (pulse, hover effects)
[✅] Django template syntax validated
[✅] All URLs functional and tested
[✅] Documentation created (2 guides)
[✅] No console errors
[✅] Django check passes (0 issues)


═══════════════════════════════════════════════════════════════════════════════════
                    🎉 DEPLOYMENT READY - NOVEMBER 11, 2025
═══════════════════════════════════════════════════════════════════════════════════
