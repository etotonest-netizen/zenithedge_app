# ZenithMentor Admin Quick Start Guide

## 📝 Populating Lesson Content

### Access Django Admin
1. Navigate to: http://127.0.0.1:8000/admin/
2. Log in with admin credentials
3. Go to **ZenithMentor > Lessons**

### Edit a Lesson
1. Click on any lesson (e.g., "Week 1 - Trend Trading & Timeframe Alignment")
2. Fill in these fields:

#### Basic Information
- **Title**: Already set
- **Week**: Already set (0-12)
- **Category**: Already set (trend, breakout, etc.)
- **Slug**: Auto-generated from title

#### Content Fields (Add your content here)

**Theory Content** (Markdown supported):
```markdown
## Introduction to Trend Trading

Trend trading is one of the most reliable strategies when applied correctly. The key is identifying strong directional moves and riding them with proper risk management.

### Key Concepts
- **Higher Highs & Higher Lows** (uptrend)
- **Lower Highs & Lower Lows** (downtrend)
- **Moving Average alignment** (20/50/200 EMAs)

### Entry Rules
1. Wait for pullback to support in uptrend (or resistance in downtrend)
2. Confirm with candlestick pattern (bullish engulfing, hammer)
3. Entry on break of pullback high
4. Stop loss below pullback low
5. Target 2:1 or higher reward:risk

### Example Trade
![Trend Trade Example](https://example.com/chart1.png)

### Common Mistakes
❌ Entering too early before pullback completes
❌ Not waiting for confirmation
❌ Taking profits too early

### Practice Exercise
Complete 5 trending scenarios with:
- Clean entry on pullback
- Stop loss below structure
- 2:1 minimum R:R
```

**Video URL** (Optional):
```
https://www.youtube.com/embed/YOUR_VIDEO_ID
```

**Demo Chart URL** (Optional):
```
https://www.tradingview.com/chart/EURUSD/YOUR_CHART_ID
```

**Description** (Short summary):
```
Learn to identify and trade strong trends using multiple timeframe analysis and moving averages.
```

#### Advanced Settings
- **Min Pass Score**: 70 (default)
- **Prerequisites**: Select required previous lessons
- **Is Active**: ✓ (checked)

### Save Lesson
Click **SAVE** at bottom of page

---

## 📊 Adding Lesson Steps

### Create Steps for Each Lesson
While editing a lesson, scroll to **Lesson Steps** section (inline editor)

### Step Types

#### 1. Concept Step
- **Step Type**: Concept
- **Description**: "Understand trend structure and phases"
- **Order**: 1

#### 2. Rules Step
- **Step Type**: Rules
- **Description**: "Entry and exit rules for trend trading"
- **Order**: 2

#### 3. Demo Step
- **Step Type**: Demo
- **Description**: "Watch live trend trade breakdown"
- **Chart URL**: Link to TradingView chart
- **Order**: 3

#### 4. Mistakes Step
- **Step Type**: Mistakes
- **Description**: "Common trend trading errors and how to avoid them"
- **Order**: 4

#### 5. Quiz Step
- **Step Type**: Quiz
- **Description**: "Test your trend trading knowledge"
- **Quiz Questions** (JSON format):
```json
[
  {
    "question": "What defines an uptrend?",
    "options": [
      "Higher highs and higher lows",
      "Lower highs and lower lows",
      "Sideways price action",
      "Random price movement"
    ],
    "correct": 0,
    "explanation": "An uptrend consists of a series of higher highs and higher lows."
  },
  {
    "question": "Where is the best entry in an uptrend?",
    "options": [
      "At the all-time high",
      "After a pullback to support",
      "On a bearish candle",
      "Randomly"
    ],
    "correct": 1,
    "explanation": "Enter after a pullback to support/moving average when price shows signs of resuming the trend."
  }
]
```
- **Order**: 5

#### 6. Simulation Step
- **Step Type**: Simulation
- **Description**: "Practice trend trading on 5 scenarios"
- **Required Scenarios**: Select 5 trending scenarios from dropdown
- **Order**: 6

### Save All Steps
Click **SAVE** to save lesson with all steps

---

## 🎯 Creating Custom Scenarios

### Via Django Shell
```bash
python3 manage.py shell
```

```python
from zenithmentor.scenario_engine import ScenarioGenerator
import pandas as pd

# Load your historical data
df = pd.read_csv('data/EURUSD_15M.csv', parse_dates=['timestamp'])
df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

# Generate scenario
generator = ScenarioGenerator()
scenario_dict = generator.create_scenario_from_historical(
    df=df,
    name="EURUSD London Breakout",
    strategy='breakout',
    regime='high_volatility',
    difficulty=6,
    volatility_multiplier=1.2,
    inject_news=True
)

# Save to database
from zenithmentor.models import Scenario
scenario = Scenario.objects.create(**scenario_dict)
print(f"Created: {scenario.name}")
```

### Via CSV Import
```bash
python3 manage.py build_scenario_bank --csv data/EURUSD_15M.csv --count 50
```

---

## 🏆 Creating Custom Badges

### Access Badge Admin
1. Go to: http://127.0.0.1:8000/admin/zenithmentor/skillbadge/
2. Click **ADD SKILL BADGE**

### Badge Fields

**Name**: "Master Scalper"

**Description**: "Achieve 80% win rate on 30 scalping scenarios"

**Category**: Choose one:
- `discipline` - Risk management & journaling
- `performance` - Profitability metrics
- `consistency` - Stable performance
- `mastery` - Strategy expertise
- `milestone` - Major achievements

**Icon Name**: Choose from [Bootstrap Icons](https://icons.getbootstrap.com/):
- `lightning-fill` (speed/scalping)
- `bullseye` (precision)
- `star-fill` (achievement)
- `trophy-fill` (championship)
- `gem` (rare/valuable)

**Color**: HTML color code:
- `#4CAF50` (green - success)
- `#2196F3` (blue - discipline)
- `#FF9800` (orange - performance)
- `#9C27B0` (purple - mastery)
- `#FFD700` (gold - ultimate)

**Requirement Criteria** (JSON):
```json
{
  "min_scenarios_passed": 30,
  "min_win_rate": 80,
  "strategy_focus": "scalping",
  "min_proficiency": 80
}
```

### Common Requirement Criteria Options
```json
{
  "min_scenarios_passed": 50,
  "min_expectancy": 0.3,
  "min_win_rate": 65,
  "min_discipline_score": 80,
  "min_journal_quality": 75,
  "max_revenge_trades": 2,
  "min_risk_consistency": 85,
  "min_consecutive_wins": 15,
  "lessons_completed": 50,
  "total_scenarios": 150,
  "strategy_focus": "smc",
  "min_proficiency": 85
}
```

### Save Badge
Click **SAVE** - badge will auto-award when criteria met

---

## 🔧 Useful Management Commands

### Check System Health
```bash
python3 manage.py shell -c "
from zenithmentor.models import Scenario, Lesson, SkillBadge
print(f'Scenarios: {Scenario.objects.count()}')
print(f'Lessons: {Lesson.objects.count()}')
print(f'Badges: {SkillBadge.objects.count()}')
"
```

### Generate More Scenarios
```bash
# Add 100 more scenarios
python3 manage.py build_scenario_bank --synthetic --count 100
```

### Recalculate Apprentice Metrics
```bash
python3 manage.py shell
```

```python
from zenithmentor.models import ApprenticeProfile

for profile in ApprenticeProfile.objects.all():
    profile.update_metrics()
    print(f"Updated: {profile.user.email}")
```

### Award Badges Manually
```bash
python3 manage.py shell
```

```python
from zenithmentor.models import ApprenticeProfile
from zenithmentor.gamification import check_and_award_badges

profile = ApprenticeProfile.objects.get(user__email='trader@example.com')
newly_awarded = check_and_award_badges(profile, latest_run=None)
print(f"Awarded {len(newly_awarded)} badges!")
```

---

## 📊 Viewing User Progress

### Access Apprentice Profiles
1. Go to: http://127.0.0.1:8000/admin/zenithmentor/apprenticeprofile/
2. Click on any profile to see:
   - Performance metrics (expectancy, win rate, etc.)
   - Discipline scores
   - ML predictions (learner type, pass probability)
   - Current lesson progress

### View Simulation Runs
1. Go to: http://127.0.0.1:8000/admin/zenithmentor/simulationrun/
2. Filter by:
   - Status (completed, in_progress, etc.)
   - Passed (True/False)
   - Apprentice
   - Scenario

### View Trade Entries
1. Go to: http://127.0.0.1:8000/admin/zenithmentor/tradeentry/
2. See individual trades with:
   - Entry/exit prices
   - P&L
   - ZenBot scores
   - Risk metrics
   - Rationale text

---

## 🎓 Best Practices

### Lesson Content Guidelines
1. **Start Simple**: Week 0-2 should be beginner-friendly
2. **Progressive Difficulty**: Gradually increase complexity
3. **Real Examples**: Use actual chart images/links
4. **Clear Rules**: Be specific about entry/exit criteria
5. **Common Mistakes**: Address typical errors
6. **Practice**: Always include simulation steps

### Scenario Guidelines
1. **Variety**: Mix regimes (trending, ranging, volatile)
2. **Difficulty Spread**: Balance easy (1-3), medium (4-6), hard (7-10)
3. **Strategy Coverage**: Cover all strategies (trend, breakout, SMC, etc.)
4. **Real Patterns**: Base on actual market behavior
5. **News Events**: Add synthetic news for realism

### Badge Guidelines
1. **Achievable**: First badge should be easy (pass 1 scenario)
2. **Motivating**: Progressive milestones (10, 25, 50, 100)
3. **Specific**: Strategy-specific badges (Trend Master, SMC Expert)
4. **Ultimate**: Final certification badge (hard requirements)

---

## 🚀 Quick Content Templates

### Week 1-3 (Beginner)
- Focus: Basic concepts
- Difficulty: 1-3 scenarios
- Videos: Fundamentals
- Steps: Concept → Rules → Demo → Quiz → Practice (3 scenarios)

### Week 4-7 (Intermediate)
- Focus: Advanced techniques
- Difficulty: 4-6 scenarios
- Videos: Strategy breakdowns
- Steps: Concept → Rules → Demo → Mistakes → Quiz → Practice (5 scenarios)

### Week 8-11 (Advanced)
- Focus: Mastery & discipline
- Difficulty: 7-9 scenarios
- Videos: Live trade reviews
- Steps: Advanced Concepts → Complex Rules → Multiple Demos → Common Mistakes → Comprehensive Quiz → Intensive Practice (10 scenarios)

### Week 12 (Certification)
- Focus: Final exam
- Difficulty: 9-10 scenarios
- Videos: Exam prep
- Steps: Review → Final Exam (20 scenarios) → Certification

---

## 📞 Need Help?

### Check Logs
```bash
tail -f /tmp/django_server.log
```

### Test URL Access
```bash
curl http://127.0.0.1:8000/mentor/
```

### Verify Database
```bash
python3 manage.py dbshell
.tables  # List all tables
SELECT COUNT(*) FROM zenithmentor_scenario;
.quit
```

---

**Admin Access**: http://127.0.0.1:8000/admin/  
**ZenithMentor**: http://127.0.0.1:8000/mentor/  
**Documentation**: ZENITHMENTOR_GUIDE.md  

🎉 **You're all set! Start populating content!**
