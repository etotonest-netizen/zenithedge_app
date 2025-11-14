# Intelligence Console Setup Guide

## Overview

The Intelligence Console provides a professional, real-time view of all market insights generated from TradingView's ZenithEdge AI analysis system.

## Features

### Visual Design
- **Professional intelligence theme** optimized for market analysis
- **Bootstrap 5** for responsive design
- **Bootstrap Icons** for visual elements
- **Modern gradient cards** with intelligence-focused palette (teal, amber, steel gray)

### Dashboard Components

1. **Statistics Cards**
   - Total Market Insights count
   - High Quality Insights (passed validation)
   - Low Quality Insights (failed validation)
   - Average Confidence score

2. **Filter Section**
   - Filter by Quality (High Quality/Low Quality)
   - Filter by Bias (Bullish/Bearish)
   - Filter by Market Phase (Trend/Breakout/MeanReversion/Squeeze)
   - Filter by Symbol (text search)

3. **Insight Cards**
   - ID and Symbol with timeframe
   - Market Bias (Bullish/Bearish) with professional color coding
   - Market Phase badge
   - Confidence score with visual progress bar
   - Observation price
   - Insight Index (AI quality score)
   - Quality status (High Quality/Low Quality)
   - AI-generated narrative (contextual analysis)
   - Timestamp

4. **Pagination**
   - Shows 20 insights per page
   - Navigate between pages
   - Preserves filters across pages

## URLs

The Intelligence Console is accessible at:
- `/signals/insights/` - **NEW Intelligence Console** (Recommended)
- `/signals/dashboard/` - Legacy dashboard URL
- `/api/insights/` - REST API for market insights

## Setup Instructions

### 1. Templates Directory Structure

Make sure your templates are in the correct location:
```
signals/
├── templates/
│   └── signals/
│       └── dashboard.html
```

### 2. Views Configuration

The `DashboardView` is already added to `views.py` and includes:
- Signal listing with pagination
- Query parameter filtering
- Statistics calculations

### 3. URL Configuration

URLs are already configured in `signals/urls.py`:
```python
urlpatterns = [
    path('webhook/', views.signal_webhook, name='signal_webhook'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('', views.DashboardView.as_view(), name='dashboard_root'),
]
```

### 4. Settings Configuration

Ensure Django templates are configured in `settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # This must be True
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

## Usage

### Accessing the Dashboard

1. Start your Django server:
```bash
python manage.py runserver
```

2. Navigate to:
```
http://localhost:8000/api/signals/dashboard/
```

### Filtering Signals

Use the filter section at the top to narrow down signals:

**By Status:**
- All signals
- Only allowed signals
- Only rejected signals

**By Side:**
- All trades
- Only buy signals
- Only sell signals

**By Regime:**
- All regimes
- Trend only
- Breakout only
- Mean Reversion only
- Squeeze only

**By Symbol:**
- Enter symbol name (e.g., "BTCUSDT")
- Case-insensitive partial matching

### Understanding the Display

**Confidence Score Colors:**
- **Green** (75%+): High confidence signal
- **Yellow** (60-74%): Medium confidence signal
- **Red** (<60%): Low confidence signal

**Status Badges:**
- **Green "ALLOWED"**: Signal passed all prop rules
- **Red "REJECTED"**: Signal failed one or more prop rules
  - Hover or see rejection reason below badge

**Side Badges:**
- **Green with up arrow**: BUY signal
- **Orange with down arrow**: SELL signal

## Customization

### Change Page Size

Edit the `paginate_by` value in `views.py`:
```python
class DashboardView(ListView):
    paginate_by = 100  # Change from 50 to 100
```

### Auto-Refresh

Uncomment the JavaScript at the bottom of `dashboard.html` to enable auto-refresh:
```javascript
// Auto-refresh page every 30 seconds
setTimeout(function() {
    location.reload();
}, 30000);
```

### Theme Colors

Modify the CSS variables in the `<style>` section of `dashboard.html`:
```css
body {
    background-color: #0f172a;  /* Dark background */
    color: #e2e8f0;             /* Light text */
}
```

### Statistics

The statistics cards automatically calculate:
- Total signals from database
- Count of allowed signals
- Count of rejected signals
- Average confidence score across all signals

## Mobile Responsive

The dashboard is fully responsive and works on:
- Desktop (optimal experience)
- Tablets (adjusted layout)
- Mobile phones (stacked cards and scrollable table)

## Performance Tips

For large datasets:
1. Keep pagination enabled
2. Use database indexes (already configured in models)
3. Consider adding caching for statistics
4. Use Django Debug Toolbar in development

## Integration with Real-Time Updates

For real-time updates without page refresh, consider adding:
1. **WebSockets** with Django Channels
2. **AJAX polling** to check for new signals
3. **Server-Sent Events (SSE)** for push notifications

Example AJAX polling (add to dashboard.html):
```javascript
setInterval(function() {
    fetch('/api/signals/latest/')
        .then(response => response.json())
        .then(data => {
            // Update UI with new signals
        });
}, 5000); // Check every 5 seconds
```

## Troubleshooting

**Dashboard shows 404:**
- Check that `signals` app is in `INSTALLED_APPS`
- Verify URL patterns in project's main `urls.py`
- Ensure `APP_DIRS` is True in `TEMPLATES` setting

**No styling:**
- Check internet connection (Bootstrap loaded from CDN)
- Verify Bootstrap CDN links are not blocked

**Filters don't work:**
- Clear browser cache
- Check browser console for JavaScript errors
- Verify query parameters in URL

**No signals showing:**
- Confirm signals exist in database
- Check if filters are too restrictive
- Verify database connection

## Next Steps

Consider adding:
1. **Export functionality** (CSV, Excel)
2. **Charts and graphs** (Chart.js, Plotly)
3. **Signal performance tracking** (P&L calculation)
4. **Email/SMS alerts** for high-confidence signals
5. **WebSocket integration** for real-time updates
