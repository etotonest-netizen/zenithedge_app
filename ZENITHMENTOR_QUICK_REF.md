# ZenithMentor Quick Reference

## 🚀 Quick Start

```bash
# 1. Initialize system (one-time)
python manage.py initialize_zenithmentor

# 2. Build scenario bank
python manage.py build_scenario_bank --synthetic --count 200

# 3. Access dashboard
http://127.0.0.1:8000/mentor/
```

## 📍 Key URLs

| Feature | URL | Description |
|---------|-----|-------------|
| Dashboard | `/mentor/` | Main training hub |
| Curriculum | `/mentor/curriculum/` | 12-week lesson plan |
| Scenarios | `/mentor/scenarios/` | Browse practice scenarios |
| Progress | `/mentor/progress/` | Analytics & reports |
| Badges | `/mentor/badges/` | Achievements |

## 🎯 Certification Checklist

- [ ] Complete 40 lessons (12-week curriculum)
- [ ] Pass 100 scenarios (70+ score each)
- [ ] Achieve 0.2R+ expectancy
- [ ] Maintain 75+ discipline score  
- [ ] Pass Mock Prop Challenge (Week 11)
- [ ] Pass Certification Exam (Week 12)

## 🤖 ML Model Training

```bash
# After collecting 50+ apprentice profiles
python manage.py train_ml_models --model all --min-samples 50

# Train specific model
python manage.py train_ml_models --model profiler
python manage.py train_ml_models --model pass_predictor
```

## 📊 Grading Breakdown

| Dimension | Weight | Key Factors |
|-----------|--------|-------------|
| Technical | 30% | ZenBot score, Direction, Entry accuracy |
| Risk Mgmt | 25% | Position size, R:R ratio, Stop loss |
| Execution | 20% | Clean exits, Proper closure |
| Journaling | 15% | NLP quality, Completeness |
| Discipline | 10% | Consistency, No revenge trading |

**Pass Score**: 70/100

## 🏆 Badge Categories

- **Discipline**: First Steps, Risk Manager, Journal Master
- **Performance**: Profitable Trader, High Win Rate, Century
- **Consistency**: Consistent Performer, Risk Discipline
- **Mastery**: Trend Master, SMC Expert, Breakout Specialist
- **Ultimate**: ZenithMentor Certified

## 🧠 NLP Analysis Triggers

**Overconfidence Warning** (>60):
- Keywords: definitely, certain, guaranteed, easy money

**Revenge Trading Alert** (>70):
- Keywords: get back, make up for, payback, unlucky

**Fear Detection** (>70):
- Keywords: scared, worried, panic, hesitant

**Greed Indicators** (>70):
- Keywords: FOMO, missed out, bigger position

## 🎮 Scenario Types

| Regime | Difficulty | Strategy Focus |
|--------|-----------|---------------|
| Trending Bull/Bear | 2-4 | Trend following |
| Ranging | 3-6 | Mean reversion |
| High Volatility | 4-8 | Breakouts |
| Low Volatility | 2-5 | Scalping |
| Breakout | 3-7 | Range breakouts |
| Reversal | 5-9 | Liquidity sweeps |
| News-Driven | 6-10 | Event trading |

## 🔧 Admin Tasks

### Add Lesson Content
1. Navigate to `/admin/zenithmentor/lesson/`
2. Select lesson → Edit
3. Update `theory_content` (Markdown supported)
4. Add `demo_chart_url` and `video_url`
5. Save

### Create Custom Badge
1. Navigate to `/admin/zenithmentor/skillbadge/`
2. Click "Add Skill Badge"
3. Set `requirement_criteria` JSON:
```json
{
  "min_scenarios_passed": 50,
  "min_discipline_score": 80,
  "min_expectancy": 0.3
}
```
4. Choose icon from Bootstrap Icons
5. Save

### Import Scenarios from CSV
```bash
# CSV format: timestamp,open,high,low,close,volume
python manage.py build_scenario_bank --csv data/eurusd.csv --count 100
```

## 🔍 Database Queries

```python
# Get top performers
from zenithmentor.gamification import get_leaderboard
leaderboard = get_leaderboard(limit=10)

# Find struggling apprentices
from zenithmentor.models import ApprenticeProfile
struggling = ApprenticeProfile.objects.filter(
    pass_probability__lt=30,
    total_scenarios_attempted__gte=10
)

# Analyze journal quality
from zenithmentor.models import SimulationRun
runs_with_good_journals = SimulationRun.objects.filter(
    journaling_score__gte=80,
    status='completed'
)
```

## ⚙️ Configuration

### Adaptive Coach Settings (per user)
- **assisted**: System blocks risky trades
- **suggestions**: System advises but doesn't block
- **autonomous**: No intervention

Change via:
```python
profile.coaching_mode = 'assisted'  # or 'suggestions' or 'autonomous'
profile.save()
```

### Difficulty Adaptation
- **Target Win Rate**: 55%
- **Adjustment Threshold**: Every 5 scenarios
- **Range**: 1-10 difficulty levels

### Position Size Limits
- **High Discipline (80+)**: 2% risk per trade
- **Medium Discipline (60-79)**: 1.5% risk
- **Low Discipline (<60)**: 1% risk (training wheels)

## 📈 Performance Metrics

### Expectancy Calculation
```
Expectancy = (Avg Win × Win Rate) - (Avg Loss × Loss Rate)
```

### Discipline Score Factors
- Risk consistency (stdev < 0.5%)
- Stop loss adherence
- Max consecutive losses
- Revenge trading incidents

### Journal Quality Score
- Length (30 points)
- Structure (20 points)
- Discipline language (30 points)
- Bias-free (20 points)

## 🐛 Troubleshooting

**Scenarios not appearing**:
```bash
python manage.py shell
from zenithmentor.models import Scenario
print(Scenario.objects.filter(is_active=True).count())
```

**ML models not predicting**:
```bash
ls ~/zenithedge_trading_hub/ml_models/
# Should see: apprentice_classifier.pkl, pass_predictor.pkl
```

**NLP not detecting patterns**:
```python
from zenithmentor.nlp_analysis import journal_analyzer
result = journal_analyzer.analyze_journal_entry("Test entry text")
print(result)
```

## 💡 Tips for Trainers

1. **Start Easy**: Assign Week 0-2 lessons first
2. **Monitor Daily**: Check `/admin/zenithmentor/apprenticeprofile/`
3. **Intervene Early**: Assist struggling apprentices before patterns form
4. **Update Content**: Add real chart examples to lessons
5. **Retrain Models**: Monthly after collecting 50+ new data points

## 📞 Integration with Other Modules

### ZenBot
```python
# In simulation, ZenBot scores trades automatically
trade.zenbot_score  # 0-100
trade.coach_verdict  # Explanation text
```

### PropCoach
```python
# Week 11-12 uses PropCoach scenarios
from propcoach.models import FirmTemplate
template = FirmTemplate.objects.get(firm_name='FTMO')
# Link to simulation
```

### ZenNews
```python
# Inject news into scenarios
scenario.synthetic_news_events = [
    {'impact': 'high', 'title': 'NFP Surprise', 'candle_index': 50}
]
```

## 🎓 Curriculum Structure

```
Week 0:  Foundations          (Difficulty 1)
Week 1:  Trend Trading         (Difficulty 2)
Week 2:  Breakouts             (Difficulty 3)
Week 3:  Mean Reversion        (Difficulty 3)
Week 4:  Volatility Squeeze    (Difficulty 4)
Week 5:  VWAP & Session Bias   (Difficulty 4)
Week 6:  SMC Primer            (Difficulty 5)
Week 7:  SMC Advanced          (Difficulty 6)
Week 8:  Scalping              (Difficulty 5)
Week 9:  Supply & Demand       (Difficulty 5)
Week 10: Prop Prep             (Difficulty 6)
Week 11: Mock Prop             (Difficulty 8)
Week 12: Certification Exam    (Difficulty 9)
```

## 🔐 Security & Compliance

- **Disclaimers**: Auto-displayed on first dashboard access
- **Audit Trail**: All trades & journals logged
- **ML Versioning**: Models tracked in `MLModel` table
- **Data Privacy**: Per-user isolation enforced

---

**Version**: 1.0  
**Last Updated**: 2025-11-11  
**Module**: zenithmentor  
**Status**: ✅ Production Ready
