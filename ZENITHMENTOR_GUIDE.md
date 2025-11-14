# ZenithMentor - Complete Training System

## Overview

**ZenithMentor** is an end-to-end training module that transforms complete novices into disciplined, repeatable traders through simulation-based learning, adaptive AI coaching, and prop-style certification.

## Key Features

### 🎓 **Structured 12-Week Curriculum**
- **Week 0**: Market Microstructure & Foundations
- **Weeks 1-5**: Core Strategies (Trend, Breakout, Mean Reversion, Volatility, VWAP)
- **Weeks 6-7**: Smart Money Concepts (SMC) - Order Blocks, Liquidity Sweeps
- **Weeks 8-9**: Scalping & Supply/Demand Trading
- **Weeks 10-12**: Prop Challenge Prep & Certification

### 🎮 **Scenario-Based Training**
- **200+ Replayable Market Scenarios**: Historical + synthetic data
- **Regime Types**: Trending, Ranging, High/Low Volatility, Breakouts, News-Driven
- **Difficulty Levels**: 1-10 adaptive scaling
- **Session Focus**: Asian, London, NY, Overlaps

### 🤖 **Adaptive AI Coach**
- **ML-Powered Profiling**: Classifies learners (Analytical, Intuitive, Aggressive, Conservative)
- **Pass Probability Prediction**: scikit-learn RandomForest models
- **Dynamic Difficulty**: Adapts to performance (55% win rate target)
- **Personalized Feedback**: Strategy-specific coaching based on learner type

### 📊 **Performance Analytics**
- **Comprehensive Metrics**: Win rate, Expectancy, Max DD, Discipline score
- **Strategy Breakdown**: Per-strategy proficiency tracking
- **Equity Curves**: Visual performance over time
- **Journal Quality**: NLP-based sentiment & bias detection

### 🏆 **Gamification & Badges**
- **12 Default Badges**: First Steps, Risk Manager, Profitable Trader, Century, etc.
- **Mastery Badges**: Strategy-specific achievements (Trend Master, SMC Expert)
- **Certification**: "ZenithMentor Certified" for graduates
- **Leaderboards**: Composite scoring system

### 🧠 **Psychology & Risk Management**
- **NLP Journal Analysis**: Detects overconfidence, revenge trading, fear, greed
- **Sentiment Tracking**: spaCy + TextBlob + NLTK
- **Intervention System**: Blocks risky trades in "assisted mode"
- **Emotional Control Scoring**: 0-100 discipline rating

## Architecture

```
zenithmentor/
├── models.py              # 11 core models (ApprenticeProfile, Scenario, SimulationRun, etc.)
├── views.py               # Django views & API endpoints
├── urls.py                # URL routing
├── admin.py               # Django admin customization
├── adaptive_coach.py      # ML-powered coaching system
├── scenario_engine.py     # Scenario generator & bank manager
├── nlp_analysis.py        # Journal & rationale NLP analysis
├── grading.py             # Simulation grading logic
├── gamification.py        # Badges, leaderboards, achievements
├── management/
│   └── commands/
│       ├── initialize_zenithmentor.py    # Setup badges & curriculum
│       ├── build_scenario_bank.py        # Generate/import scenarios
│       └── train_ml_models.py            # Train/retrain ML models
└── templates/
    └── zenithmentor/
        └── dashboard.html  # Main training dashboard
```

## Database Models

### Core Models
1. **ApprenticeProfile**: Extended user profile with ML features (24 fields)
2. **Lesson**: 12-week curriculum structure (13 lessons)
3. **LessonStep**: Micro-lessons within each lesson
4. **Scenario**: Replayable market situations (200+ scenarios)
5. **SimulationRun**: Trainee attempts at scenarios
6. **TradeEntry**: Individual trades during simulations
7. **SkillBadge**: Gamification achievements
8. **AssessmentResult**: Quiz & exam results
9. **CoachingSession**: AI coaching interactions
10. **MLModel**: Trained model versioning

### Key Relationships
- `ApprenticeProfile` ↔ `SimulationRun` (one-to-many)
- `Scenario` ↔ `SimulationRun` (one-to-many)
- `SimulationRun` ↔ `TradeEntry` (one-to-many)
- `ApprenticeProfile` ↔ `SkillBadge` (many-to-many via BadgeAward)

## Installation & Setup

### 1. Install Dependencies
```bash
pip install scikit-learn pandas numpy textblob nltk feedparser
python -m nltk.downloader punkt vader_lexicon
```

### 2. Add to Django Settings
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'zenithmentor',
]
```

### 3. Add URL Configuration
```python
# zenithedge/urls.py
urlpatterns = [
    path('mentor/', include('zenithmentor.urls')),
]
```

### 4. Run Migrations
```bash
python manage.py makemigrations zenithmentor
python manage.py migrate
```

### 5. Initialize System
```bash
# Create badges & curriculum structure
python manage.py initialize_zenithmentor

# Build scenario bank (200 scenarios)
python manage.py build_scenario_bank --synthetic --count 200

# Optional: Import from CSV
python manage.py build_scenario_bank --csv /path/to/ohlcv.csv --count 100
```

### 6. Add Navigation Link
Update `signals/templates/signals/dashboard.html` to add ZenithMentor link:
```html
<a class="nav-link" href="{% url 'zenithmentor:dashboard' %}">
    <i class="bi bi-mortarboard-fill"></i> ZenithMentor
</a>
```

## Usage Guide

### For Trainees

1. **Access Dashboard**: Navigate to `/mentor/`
2. **Start First Lesson**: Week 0 - Foundations automatically assigned
3. **Complete Lesson Steps**:
   - Read theory content
   - Watch annotated demos
   - Complete knowledge checks
   - Practice in scenarios
4. **Launch Scenarios**: Browse scenarios by difficulty/regime
5. **Simulation Workflow**:
   - Replay controls (play/pause/step)
   - Submit trades with rationale
   - Receive instant ZenBot feedback
   - Journal your thought process
   - Get AI coaching suggestions
6. **Complete & Review**:
   - Graded on 5 dimensions (technical, risk, execution, journal, discipline)
   - Receive personalized feedback
   - Earn badges for milestones
7. **Track Progress**:
   - View performance analytics
   - Check certification requirements
   - Monitor pass probability

### For Admins

1. **Add Lesson Content**: Django admin → Lessons → Edit theory_content (Markdown)
2. **Create Scenarios**:
   - Via admin interface (manual)
   - Via management command (bulk)
   - From CSV files (historical data)
3. **Monitor Trainees**: Admin → Apprentice Profiles
4. **Retrain ML Models**:
   ```bash
   python manage.py train_ml_models --model all --min-samples 50
   ```
5. **Create Custom Badges**: Admin → Skill Badges → Add Badge

## API Endpoints

### Simulation Management
- `POST /mentor/simulation/launch/` - Start new simulation
- `GET /mentor/simulation/<uuid:id>/` - View/resume simulation
- `GET /mentor/simulation/<uuid:id>/results/` - View results

### Trading Actions
- `POST /mentor/api/trade/submit/` - Submit trade entry
- `POST /mentor/api/trade/close/` - Close open trade
- `POST /mentor/api/journal/add/` - Add journal entry
- `POST /mentor/api/simulation/complete/` - Complete & grade simulation

### Progress & Analytics
- `GET /mentor/progress/` - Detailed performance report
- `GET /mentor/badges/` - View earned badges
- `GET /mentor/curriculum/` - Browse lessons

## Machine Learning Components

### 1. Apprentice Profiler
**Purpose**: Classify learner types
**Algorithm**: RandomForest Classifier (100 estimators)
**Features** (12 total):
- Win rate, Risk per trade, Risk consistency
- Stop loss adherence, R:R ratio
- Discipline, Journaling quality, Emotional control
- Scenarios attempted, Lessons completed
- Revenge trades, Overconfidence incidents

**Output**: 4 learner types (Analytical, Intuitive, Aggressive, Conservative)

### 2. Pass Predictor
**Purpose**: Predict certification pass probability
**Algorithm**: RandomForest Regressor (100 estimators)
**Features** (14 total):
- Expectancy, Win rate, Risk metrics
- Drawdown, Discipline scores
- Journal quality, Emotional control
- Progress metrics, Current difficulty

**Output**: Pass probability (0-100%)

### 3. Difficulty Adapter
**Purpose**: Adaptive scenario difficulty
**Logic**:
- Target 55% win rate
- Increase difficulty if win rate > 70% and score > 80
- Decrease difficulty if win rate < 40% or score < 60
- Adjusts every 5 scenarios

## NLP Analysis

### Journal Analyzer
**Tools**: TextBlob, NLTK VADER, spaCy (ready)
**Detects**:
- Overconfidence (keywords: definitely, certain, guaranteed, easy money)
- Revenge trading (keywords: get back, make up for, payback)
- Fear (keywords: scared, worried, nervous, panic)
- Greed (keywords: FOMO, missed out, bigger position)
- Discipline (positive/negative language patterns)

**Output**:
- Quality score (0-100)
- Sentiment (positive/negative/neutral)
- Bias scores (overconfidence, revenge risk, fear, greed)
- Warnings & suggestions

### Rationale Validator
**Checks**:
- Entry reason (why, signal, setup, pattern)
- Risk management (stop, risk, target, R:R)
- Context (trend, support, resistance, timeframe)

**Output**:
- Completeness score (0-100)
- Missing elements
- Actionable feedback

## Grading System

### 5 Dimensions (each scored 0-100)

1. **Technical Analysis** (30% weight)
   - ZenBot score integration
   - Direction correctness vs optimal
   - Entry price proximity

2. **Risk Management** (25% weight)
   - Position sizing within limits
   - R:R ratio >= 1.5
   - Stop loss usage
   - Max risk per trade <= 2.5%

3. **Execution** (20% weight)
   - Clean exits (stop/target hit)
   - Proper trade closure
   - Minimal slippage

4. **Journaling** (15% weight)
   - NLP quality score
   - Completeness
   - Sentiment balance

5. **Discipline** (10% weight)
   - Max consecutive losses <= 3
   - Consistent risk sizing
   - No revenge trading patterns
   - Drawdown adherence

**Pass Criteria**: Overall score >= 70 (adjustable per scenario)

## Certification Requirements

To earn **ZenithMentor Certified** badge:

1. ✅ Complete **40 lessons** (12-week curriculum)
2. ✅ Pass **100 scenarios**
3. ✅ Achieve **expectancy >= 0.2R**
4. ✅ Maintain **discipline score >= 75**
5. ✅ Pass **Mock Prop Challenge** (Week 11)
6. ✅ Pass **Certification Exam** (Week 12)

## Gamification System

### Badge Categories
- **Discipline**: First Steps, Risk Manager, Journal Master
- **Performance**: Profitable Trader, High Win Rate
- **Consistency**: Consistent Performer, Risk Discipline
- **Milestones**: Century (100 scenarios), Certification
- **Mastery**: Trend Master, SMC Expert, Breakout Specialist

### Leaderboard Scoring
**Composite Score** = 
- Expectancy (40%)
- Win Rate (20%)
- Discipline (20%)
- Scenarios Passed (10%)
- Badge Count (10%)

## Integration with Existing Modules

### ZenBot Integration
- Trades during simulations scored via `bot.ai_score.predict_score()`
- Provides technical validity assessment
- Coach verdict includes ZenBot breakdown

### Cognition Integration
- Journal entries analyzed for psychological patterns
- Mood tracking influences coaching interventions
- Revenge trading detection triggers warnings

### PropCoach Integration
- Week 11: Mock Prop Challenge uses PropCoach scenarios
- Certification exam can be PropSim challenge
- Final assessment mapped to prop-firm rules

### ZenNews Integration (Ready)
- Scenarios can inject synthetic news events
- `feedparser` integration for real news feeds
- News sentiment affects scenario grading

## Management Commands

### initialize_zenithmentor
```bash
python manage.py initialize_zenithmentor
```
- Creates 12 default badges
- Builds 12-week curriculum structure
- One-time setup

### build_scenario_bank
```bash
# Generate synthetic scenarios
python manage.py build_scenario_bank --synthetic --count 200

# Import from CSV
python manage.py build_scenario_bank --csv data/eurusd_15m.csv --count 100
```
**CSV Format**: `timestamp, open, high, low, close, volume`

### train_ml_models
```bash
# Train all models
python manage.py train_ml_models --model all --min-samples 50

# Train specific model
python manage.py train_ml_models --model profiler
python manage.py train_ml_models --model pass_predictor
```
**Requirements**:
- Profiler: 50+ apprentices with labeled learner types
- Pass Predictor: 50+ completed simulation runs

## Disclaimers & Compliance

**Built-in Warning** (display on first access):
> "ZenithMentor is a training simulation tool. Past simulated performance does not guarantee live trading profits. Always practice risk management and never risk more than you can afford to lose. Seek professional advice before live trading."

**Audit Trail**:
- Every trade logged with rationale
- All coaching interventions recorded
- Journal entries timestamped
- ML model versions tracked

## Performance Optimization

### Database Indexes
- `(apprentice, status)` on SimulationRun
- `(scenario, passed)` on SimulationRun
- `(regime, difficulty)` on Scenario
- `(strategy_focus)` on Scenario

### Caching Strategy (Future)
- Cache scenario candle data (rarely changes)
- Cache lesson content (static after creation)
- Cache leaderboard (update every 5 min)

### Resource Limits
- Max scenario candles: 500 (15m = ~5 days)
- Max trades per simulation: 50
- Max journal entries: 100 per simulation
- ML model training: Background task (Celery ready)

## Troubleshooting

### Issue: ML models not loaded
**Solution**:
```bash
python manage.py train_ml_models --model all
```
Models auto-create default instances if missing.

### Issue: Scenarios not appearing
**Solution**:
```bash
python manage.py build_scenario_bank --synthetic --count 50
```
Check `Scenario.is_active=True` in admin.

### Issue: NaN errors in scenarios
**Solution**: Fixed in v1.0 - ATR fallback to 0.001 if NaN.

### Issue: Timezone warnings
**Solution**: Use `timezone.now()` instead of `datetime.now()` for all timestamps.

## Future Enhancements

### Phase 2 Features (Planned)
- [ ] Live data integration (MT4/MT5 connectors)
- [ ] Multi-user challenges (compete with peers)
- [ ] Video lesson embedding
- [ ] Voice journal entries (speech-to-text)
- [ ] Mobile app (React Native)
- [ ] Advanced ML: LSTM for pattern recognition
- [ ] Social features: Share trades, Follow mentors

### Phase 3 (Advanced)
- [ ] Custom scenario builder (drag-drop)
- [ ] AI-generated lessons (GPT-4 integration)
- [ ] Virtual trading mentor (chatbot)
- [ ] Certification NFT (blockchain)

## Credits & License

**Built for**: ZenithEdge Trading Hub  
**Version**: 1.0  
**Author**: AI Development Team  
**License**: Proprietary (Internal Use)

**Technologies**:
- Django 4.2.7
- scikit-learn 1.3+
- pandas, numpy
- TextBlob, NLTK, spaCy (ready)
- Bootstrap 5.3.0
- Chart.js 4.4.0

## Support

For issues, feature requests, or questions:
- **Admin Panel**: `/admin/zenithmentor/`
- **Documentation**: This file
- **Logs**: `logs/zenithmentor.log` (configure in settings)

---

**Ready to transform novices into profitable traders!** 🚀
