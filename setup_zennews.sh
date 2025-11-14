#!/bin/bash
# ZenNews Setup Script
# Installs dependencies and configures the news system

echo "🚀 Setting up ZenNews - Financial News Integration"
echo "=================================================="

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install feedparser textblob vaderSentiment spacy scikit-learn python-dateutil nltk

# Download TextBlob corpora
echo ""
echo "📚 Downloading TextBlob corpora..."
python3 -m textblob.download_corpora

# Download spaCy model
echo ""
echo "🧠 Downloading spaCy English model..."
python3 -m spacy download en_core_web_sm

# Run migrations
echo ""
echo "🗄️  Running database migrations..."
python3 manage.py makemigrations zennews
python3 manage.py migrate

# Fetch initial news
echo ""
echo "📰 Fetching initial news data..."
python3 manage.py fetch_news --hours=48

echo ""
echo "✅ ZenNews setup complete!"
echo ""
echo "Next steps:"
echo "1. Visit http://127.0.0.1:8000/news/ to see the news dashboard"
echo "2. Run 'python manage.py fetch_news' periodically to update news"
echo "3. Set up a cron job or Celery task for automatic updates"
echo ""
echo "Example cron job (every 10 minutes):"
echo "*/10 * * * * cd /path/to/zenithedge && python manage.py fetch_news >> logs/news_fetch.log 2>&1"
