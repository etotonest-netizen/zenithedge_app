"""
Management command to fetch and analyze financial news
Usage: python manage.py fetch_news
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from zennews.models import NewsEvent, NewsAlert
from zennews.utils import fetch_latest_news, NewsAnalyzer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch and analyze financial news from RSS feeds'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Fetch news from the last N hours (default: 24)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force fetch even if duplicates exist'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS(f'Fetching news from the last {hours} hours...'))
        
        try:
            # Fetch news from RSS feeds
            news_items = fetch_latest_news(max_age_hours=hours)
            self.stdout.write(f'Fetched {len(news_items)} news items')
            
            if not news_items:
                self.stdout.write(self.style.WARNING('No news items found'))
                return
            
            # Get existing hashes to avoid duplicates
            existing_hashes = set(
                NewsEvent.objects.values_list('content_hash', flat=True)
            )
            
            # Analyze news items
            analyzer = NewsAnalyzer()
            self.stdout.write('Analyzing news sentiment and extracting entities...')
            analyzed_items = analyzer.batch_analyze(news_items)
            
            # Save to database
            saved_count = 0
            alert_count = 0
            
            for item in analyzed_items:
                # Skip duplicates unless force is enabled
                if not force and item['content_hash'] in existing_hashes:
                    continue
                
                # Create news events for each detected symbol
                symbols = item.get('symbols', ['GENERAL'])
                
                for symbol in symbols:
                    try:
                        news_event = NewsEvent.objects.create(
                            symbol=symbol,
                            headline=item['headline'],
                            sentiment=item['sentiment'],
                            impact_level=item['impact_level'],
                            topic=', '.join(item.get('topics', [])[:3]),  # Store up to 3 topics
                            source=item['source'],
                            source_url=item.get('source_url', ''),
                            content_hash=item['content_hash'],
                            timestamp=item['timestamp'],
                        )
                        saved_count += 1
                        
                        # Create alert for high-impact news
                        if item['impact_level'] == 'high' and abs(item['sentiment']) > 0.5:
                            sentiment_label = 'bullish' if item['sentiment'] > 0 else 'bearish'
                            alert_message = f"High impact {sentiment_label} news for {symbol}: {item['headline'][:100]}"
                            
                            NewsAlert.objects.create(
                                news_event=news_event,
                                alert_type='high_impact',
                                message=alert_message
                            )
                            alert_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving news event: {str(e)}")
                        continue
            
            # Output summary
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully saved {saved_count} news events'
            ))
            
            if alert_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created {alert_count} high-impact alerts'
                ))
            
            # Show some statistics
            recent_news = NewsEvent.objects.filter(
                timestamp__gte=timezone.now() - timezone.timedelta(hours=hours)
            )
            
            self.stdout.write(f'\n📊 Statistics (last {hours} hours):')
            self.stdout.write(f'  Total news events: {recent_news.count()}')
            self.stdout.write(f'  High impact: {recent_news.filter(impact_level="high").count()}')
            self.stdout.write(f'  Medium impact: {recent_news.filter(impact_level="medium").count()}')
            self.stdout.write(f'  Low impact: {recent_news.filter(impact_level="low").count()}')
            
            # Show sentiment distribution
            avg_sentiment = recent_news.aggregate(
                avg=models.Avg('sentiment')
            )['avg'] or 0
            
            self.stdout.write(f'  Average sentiment: {avg_sentiment:.3f}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            logger.exception("Error in fetch_news command")
            raise
