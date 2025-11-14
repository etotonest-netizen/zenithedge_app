# 🤖 ZenBot - AI Trading Assistant for ZenithEdge

ZenBot is an intelligent chatbot module integrated into the ZenithEdge Django trading platform. It provides real-time Q&A, user-specific analytics, and contextual help for traders.

## ✨ Features

### 1. **Intelligent Q&A System**
- Fuzzy matching algorithm with 60%+ confidence threshold
- 20+ pre-loaded Q&As covering strategies, risk, challenges, and technical support
- Category-based organization (strategy, risk, challenge, signals, technical, general, journal, replay)
- Priority-based answer ranking
- Keyword boosting for better match accuracy

### 2. **Dynamic User Queries**
- **Challenge Status**: Real-time prop challenge progress, P&L, violations
- **Signal Statistics**: Win rate, total signals, strategy breakdown
- **Risk Control**: Current status, consecutive losses, halt reasons
- **Recent Trades**: Last 5 signals with outcomes
- **Account Summary**: Overview of all user metrics

### 3. **Admin Management**
- CSV import/export for bulk Q&A management
- Usage analytics and top Q&As tracking
- Low confidence conversation identification for training
- Clear conversation history and reset usage counters
- Configurable match threshold and feature toggles

### 4. **Chat Widget**
- Floating chat button on all pages
- Smooth animations and glass-effect UI
- Quick action buttons for common queries
- Session-based conversation history
- Real-time typing indicators

## 📁 File Structure

```
bot/
├── __init__.py
├── apps.py
├── models.py              # BotQA, BotConversation, BotSettings
├── logic.py               # ZenBotEngine with matching and query logic
├── views.py               # chat_api, admin_panel, management endpoints
├── urls.py                # URL routing
├── admin.py               # Django admin with CSV import
├── migrations/
│   └── 0001_initial.py
└── templates/
    ├── bot/
    │   ├── chat_widget.html     # Floating chat widget
    │   └── admin_panel.html     # Superuser dashboard
    └── admin/bot/
        └── import_csv.html      # CSV upload form
```

## 🗂️ Models

### BotQA
Stores question-answer pairs with metadata:
- `question`: Question text (use `|` to separate variations)
- `answer`: Bot response
- `category`: One of 8 categories
- `keywords`: Comma-separated keywords for matching boost
- `priority`: 0-100 (higher = more important)
- `is_active`: Enable/disable specific Q&As
- `usage_count`: Track answer popularity

### BotConversation
Tracks user interactions:
- `user`: User who asked the question
- `session_id`: Browser session identifier
- `user_message`: User's query
- `bot_response`: Bot's answer
- `matched_qa`: FK to BotQA (if matched)
- `confidence_score`: Match confidence (0-100)

### BotSettings
Singleton configuration:
- `match_threshold`: Minimum similarity score (default: 60%)
- `enable_user_stats`: Allow user-specific queries
- `enable_signal_queries`: Allow signal database access
- `enable_learning`: Future ML feature toggle
- `default_fallback_message`: Response when no match found

## 🚀 Setup & Usage

### Installation
1. Add `'bot'` to `INSTALLED_APPS` in `settings.py`
2. Add `path('bot/', include('bot.urls'))` to `urlpatterns`
3. Run migrations:
   ```bash
   python manage.py makemigrations bot
   python manage.py migrate bot
   ```

### Loading Q&A Data
Create a CSV file with columns: `question,answer,category,keywords,priority,is_active`

Example CSV:
```csv
question,answer,category,keywords,priority,is_active
"What is trend following?|Explain trend trading","Trend following is...",strategy,"trend,strategy",80,True
```

**Via Django Admin:**
1. Login to `/admin/`
2. Navigate to Bot → Bot Q&As
3. Actions → Import Q&As from CSV
4. Upload your CSV file

**Via Script:**
```python
import csv
from bot.models import BotQA

with open('qa_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        BotQA.objects.create(
            question=row['question'],
            answer=row['answer'],
            category=row['category'],
            keywords=row['keywords'],
            priority=int(row['priority']),
            is_active=row['is_active'].lower() == 'true'
        )
```

### Adding Chat Widget to Templates
Add this line before `</body>` tag:
```django
{% include "bot/chat_widget.html" %}
```

Already added to: `dashboard.html`, `challenge_overview.html`, `challenge_setup.html`

## 🔌 API Endpoints

### `/bot/chat/` (POST)
Main chat API for user queries.

**Request:**
```json
{
  "message": "What is my challenge status?",
  "session_id": "zenbot_12345_abc"
}
```

**Response:**
```json
{
  "success": true,
  "response": "🟢 **FTMO Challenge Status:** ...",
  "confidence": 95.0,
  "category": null,
  "timestamp": "2025-11-09T12:00:00Z"
}
```

### `/bot/history/` (GET)
Retrieve user's conversation history (last 20).

### `/bot/admin-panel/` (GET)
Superuser dashboard with analytics.

### `/bot/admin/clear-conversations/` (POST)
Delete all conversation history.

### `/bot/admin/retrain/` (POST)
Reset usage counters.

### `/bot/admin/update-settings/` (POST)
Update bot configuration.

## 🧠 Bot Logic

### Matching Algorithm
1. **Exact Match**: Question exactly matches user query → 100% confidence
2. **Substring Match**: Query contains question or vice versa → 85% confidence
3. **Word-Based**: Common words between query and question → Up to 70%
4. **Character-Based**: SequenceMatcher similarity → Up to 60%
5. **Keyword Boost**: +10 per matching keyword
6. **Priority Boost**: +0.5 per priority point

### Dynamic Query Detection
Bot checks for keywords in user message to trigger dynamic queries:
- **Challenge**: "challenge", "prop", "ftmo", "progress", "pass", "fail"
- **Signals**: "signals", "trades", "win rate", "performance", "statistics"
- **Risk**: "risk", "halted", "control", "threshold", "limits"
- **Recent**: "recent", "latest", "last trade", "today"
- **Summary**: "summary", "overview", "account", "my stats"

### Example Usage in Python
```python
from bot.logic import retrieve_answer

result = retrieve_answer(
    user_query="What is trend following?",
    user=request.user,
    session_id=request.session.session_key
)

print(result['response'])  # Bot's answer
print(result['confidence'])  # Match confidence
print(result['category'])  # Q&A category
```

## 📊 Admin Panel

Access at `/bot/admin-panel/` (staff only)

**Features:**
- View total Q&As and conversations
- See match threshold and feature toggles
- Category breakdown chart
- Top Q&As by usage
- Low confidence conversations (training opportunities)
- Recent activity log

**Management Actions:**
- Clear all conversation history
- Reset usage counters
- Direct link to Django admin Q&A management

## 💡 Tips for Training

1. **Monitor Low Confidence Conversations** in admin panel to identify gaps
2. **Add Question Variations** using `|` separator:
   ```
   "What is trend?|Explain trend trading|Tell me about trends"
   ```
3. **Use Keywords** to boost matching:
   ```
   keywords="trend,strategy,momentum,direction"
   ```
4. **Set Priority** for critical Q&As (80-100 for important topics)
5. **Review Usage Analytics** to see which answers are most helpful

## 🔧 Configuration

Edit in Django Admin → Bot → Bot Settings:

- **Match Threshold**: Lower = more lenient matching (min: 40%, max: 80%)
- **Enable User Stats**: Allow bot to query user-specific data
- **Enable Signal Queries**: Allow bot to access signal database
- **Fallback Message**: Shown when no match found
- **Max Conversation History**: Limit per user (default: 100)

## 📈 Performance

- **Average Response Time**: ~200ms for Q&A matching
- **Dynamic Query Time**: ~500ms for database queries
- **Conversation Storage**: ~500 bytes per conversation
- **Memory Usage**: Minimal (singleton settings, no caching)

## 🛡️ Security

- All endpoints require authentication (`@login_required`)
- Admin endpoints require staff status (`@staff_member_required`)
- CSRF protection on all POST requests
- Session-based conversation isolation
- No PII stored in conversations (only user FK)

## 🔮 Future Enhancements

- [ ] Machine learning integration for better matching
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Sentiment analysis
- [ ] Proactive suggestions based on user behavior
- [ ] Integration with external knowledge bases
- [ ] A/B testing for answer quality

## 📝 Sample Q&A CSV

See `bot_qa_sample.csv` for 20 pre-loaded Q&As covering:
- Trading strategies (Trend, Range, Breakout)
- Prop challenge setup and status
- Risk management and controls
- Signal information and statistics
- TradingView webhook setup
- Trade journal and replay features

## 🤝 Contributing

To add new Q&As:
1. Create CSV with required columns
2. Use Django Admin → Import Q&As from CSV
3. Test matching with test queries
4. Monitor confidence scores and adjust keywords/priority

## 📞 Support

For issues or questions:
- Check `/bot/admin-panel/` for low confidence conversations
- Review Django logs for errors
- Test queries in Django shell:
  ```python
  from bot.logic import retrieve_answer
  from accounts.models import CustomUser
  
  user = CustomUser.objects.first()
  result = retrieve_answer("your test query", user=user)
  print(result)
  ```

---

**ZenBot** - Making trading assistance intelligent and accessible 🚀
