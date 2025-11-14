# 🧪 ZenithEdge System Testing Guide

## ✅ Test Account Created

**Trader Account:**
- Email: `trader@zenithedge.com`
- Password: `trader123`
- Status: Active trader with full access

## 🌐 Access Points

### Main Application
- **Login**: http://localhost:8000/accounts/login/
- **Dashboard**: http://localhost:8000/signals/dashboard/
- **Challenge Overview**: http://localhost:8000/signals/challenge/overview/
- **Challenge Setup**: http://localhost:8000/signals/challenge/setup/
- **Trade Journal**: http://localhost:8000/signals/journal/
- **ZenBot Admin Panel** (admin only): http://localhost:8000/bot/admin-panel/

### API Endpoints
- **Webhook URL**: `http://localhost:8000/api/signals/webhook/?api_key=[YOUR_API_KEY]`
- **Bot Chat API**: `http://localhost:8000/bot/chat/`

## 📋 Testing Checklist

### 1. Login & Authentication ✓
```
1. Visit http://localhost:8000/accounts/login/
2. Login with: trader@zenithedge.com / trader123
3. Should redirect to dashboard
```

### 2. Dashboard Features ✓
```
✓ View 5 pre-loaded sample signals
✓ Check signal statistics (3 green, 1 red, 1 pending)
✓ Verify win rate calculation (~75%)
✓ See strategy breakdown (Trend, Range, Breakout)
✓ Test signal filters (by strategy, regime)
✓ Click "Replay" button on any signal
```

### 3. ZenBot Chat Widget ✓
```
Open any page with the widget (dashboard, challenge pages):

1. Click the 💬 button in bottom-right corner
2. Chat should open with welcome message
3. Try quick action buttons:
   - "📊 My Stats" → Should show signal statistics
   - "🏆 Challenge" → Should show FTMO challenge status
   - "⚠️ Risk Status" → Should show risk control info
   - "📈 Recent Trades" → Should list last 5 signals

4. Type custom questions:
   - "What is trend following?" → Should match Q&A (100% confidence)
   - "How do I connect TradingView?" → Should show setup instructions
   - "What is my win rate?" → Should query database and show stats
   - "Am I passing my challenge?" → Should show challenge progress
```

**If you still get errors:**
1. Open browser console (F12 → Console tab)
2. Check for JavaScript errors or network errors
3. Look at the response body in Network tab
4. Check server logs: `tail -f /tmp/django_trading_webhook/server.log`

### 4. Prop Challenge Features ✓
```
Visit: http://localhost:8000/signals/challenge/overview/

Should see:
✓ Status indicator (🟢 green - on track)
✓ Current balance: $10,150.00
✓ Total P&L: $150.00
✓ Daily P&L: $50.00
✓ Win Rate: 62.5% (5 wins / 8 total trades)
✓ Progress bars for profit target
✓ Challenge checklist with checkmarks
✓ Trading statistics
✓ Violation counters (all should be 0)

Test the setup page:
Visit: http://localhost:8000/signals/challenge/setup/
✓ See 6 firm cards (FTMO, Funding Pips, etc.)
✓ Click different firms to load presets
✓ Current active challenge should be displayed
```

### 5. Risk Control ✓
```
From Dashboard:
✓ Check Risk Control widget/section
✓ Should show: Active, no halts
✓ Max consecutive losers: 3
✓ Max daily trades: 10
✓ Current consecutive losses: 0 (because last signal was green)

Ask ZenBot: "What is my risk status?"
Should respond with current risk settings
```

### 6. Trade Journal ✓
```
Visit: http://localhost:8000/signals/journal/

(Note: Journal entries need to be created manually)
✓ Click "New Entry" button
✓ Fill in emotions, notes, tags
✓ Save and verify it appears in list
```

### 7. Trade Replay ✓
```
From Dashboard:
1. Find any signal in the table
2. Click "Replay" button in Actions column
3. Should open trade replay page with:
   ✓ Candlestick chart
   ✓ Entry/SL/TP markers
   ✓ Play/Pause controls
   ✓ Exit point indicator
```

### 8. Admin Features (login as admin first) ✓
```
Login: admin@zenithedge.com / admin123

Visit Django Admin:
http://localhost:8000/admin/

✓ Bot → Bot Q&As (manage Q&A database)
✓ Bot → Bot Conversations (see chat history)
✓ Bot → Bot Settings (configure matching threshold)
✓ Signals → Signals (view all signals)
✓ Signals → Prop Challenge Configs
✓ Signals → Prop Challenge Progress

Visit ZenBot Admin Panel:
http://localhost:8000/bot/admin-panel/

✓ View statistics (20 Q&As, conversation count)
✓ See category breakdown
✓ Check top Q&As by usage
✓ Monitor low confidence conversations
✓ Test "Clear All Conversations" button
✓ Test "Reset Usage Counters" button
```

### 9. API Testing ✓
```
Get your API key:
1. Login as trader
2. Go to dashboard
3. Find API key section (or check account settings)

Test webhook with curl:
```bash
# Get the API key first
cd /tmp/django_trading_webhook && python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()
from accounts.models import CustomUser
trader = CustomUser.objects.get(email='trader@zenithedge.com')
print(f'API Key: {trader.api_key}')
"

# Then send a test signal (replace API_KEY with actual key)
curl -X POST "http://localhost:8000/api/signals/webhook/?api_key=API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "GBPJPY",
    "side": "BUY",
    "price": 187.50,
    "sl": 187.20,
    "tp": 188.10,
    "confidence": 88,
    "strategy": "Breakout",
    "regime": "Bullish",
    "timeframe": "1H"
  }'
```

### 10. Bot Q&A CSV Import ✓
```
As admin:
1. Visit http://localhost:8000/admin/bot/botqa/
2. Select "Import Q&As from CSV" action
3. Upload bot_qa_sample.csv (already in project root)
4. Verify 20 Q&As are imported
5. Test matching with queries

Or add custom Q&As:
1. Create CSV file with format:
   question,answer,category,keywords,priority,is_active
2. Upload via admin
```

## 🐛 Troubleshooting

### ZenBot Chat Errors

**Issue: "Sorry, I encountered an error"**

**Solutions:**
1. **Check Browser Console (F12):**
   - Look for JavaScript errors
   - Check Network tab for failed requests
   - See if CSRF token is being sent

2. **Check Server Logs:**
   ```bash
   tail -f /tmp/django_trading_webhook/server.log
   ```
   Look for [ZenBot] error messages

3. **Test Bot Logic Directly:**
   ```bash
   cd /tmp/django_trading_webhook
   python3 << 'EOF'
   import os, django
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
   django.setup()
   
   from bot.logic import retrieve_answer
   from accounts.models import CustomUser
   
   trader = CustomUser.objects.get(email='trader@zenithedge.com')
   result = retrieve_answer("What is trend following?", user=trader)
   print(result)
   EOF
   ```

4. **Common Causes:**
   - User not authenticated (must be logged in)
   - CSRF token missing
   - Session expired
   - Network connectivity issues

5. **Quick Fix:**
   - Logout and login again
   - Clear browser cache
   - Try in incognito/private window

### Challenge Not Showing

**Issue: Challenge overview shows "No active challenge"**

**Solution:**
```bash
cd /tmp/django_trading_webhook
python3 << 'EOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from accounts.models import CustomUser
from signals.models import PropChallengeConfig

trader = CustomUser.objects.get(email='trader@zenithedge.com')
challenges = PropChallengeConfig.objects.filter(user=trader, is_active=True)
print(f"Active challenges: {challenges.count()}")
for c in challenges:
    print(f"- {c.get_firm_name_display()}: ${c.account_size}")
EOF
```

### Signals Not Appearing

**Issue: Dashboard shows no signals**

**Solution:**
```bash
cd /tmp/django_trading_webhook
python3 << 'EOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from accounts.models import CustomUser
from signals.models import Signal

trader = CustomUser.objects.get(email='trader@zenithedge.com')
signals = Signal.objects.filter(user=trader)
print(f"Total signals: {signals.count()}")
for s in signals:
    print(f"- {s.symbol} {s.side} ({s.outcome})")
EOF
```

## 📊 Expected Results

After full testing, you should see:

**Dashboard:**
- 5 signals displayed
- Win rate: ~60-75%
- Strategy breakdown chart
- Risk control status
- ZenBot chat widget functional

**Challenge Overview:**
- FTMO challenge active
- $10,150 current balance
- $150 total P&L
- 8 total trades, 5 wins
- All checkmarks green
- 🟢 status indicator

**ZenBot:**
- Responds to all queries
- Shows user-specific data
- 20 Q&As loaded
- Chat history tracked
- Quick actions work

**Admin Panel:**
- 20 active Q&As
- Conversation logs visible
- Analytics functional
- CSV import/export working

## 🎉 Success Criteria

✅ Can login as trader
✅ Dashboard loads with 5 signals
✅ Challenge overview shows FTMO progress
✅ ZenBot responds to queries without errors
✅ Risk control displays correctly
✅ All quick action buttons work
✅ Admin panel accessible
✅ CSV import functional

## 📞 Need Help?

If you encounter issues:

1. **Check this guide's troubleshooting section**
2. **View server logs**: `tail -f /tmp/django_trading_webhook/server.log`
3. **Check browser console** (F12)
4. **Verify database**: Run the verification scripts above
5. **Restart server**: 
   ```bash
   pkill -9 -f "manage.py runserver"
   cd /tmp/django_trading_webhook
   python3 manage.py runserver 0.0.0.0:8000
   ```

---

**Happy Testing!** 🚀
