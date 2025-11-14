"""
Django Management Command: Initialize knowledge base with default sources
Usage: python manage.py init_kb_sources
"""
from django.core.management.base import BaseCommand
from knowledge_base.models import Source


class Command(BaseCommand):
    help = 'Initialize knowledge base with default trusted sources'
    
    DEFAULT_SOURCES = [
        {
            'domain': 'investopedia.com',
            'name': 'Investopedia',
            'base_url': 'https://www.investopedia.com',
            'trust_level': 'high',
            'rate_limit_seconds': 3,
            'notes': 'Authoritative financial education source. Respect ToS.'
        },
        {
            'domain': 'babypips.com',
            'name': 'BabyPips',
            'base_url': 'https://www.babypips.com',
            'trust_level': 'high',
            'rate_limit_seconds': 2,
            'notes': 'Forex education platform. Respect ToS.'
        },
        {
            'domain': 'fxstreet.com',
            'name': 'FXStreet',
            'base_url': 'https://www.fxstreet.com',
            'trust_level': 'medium',
            'rate_limit_seconds': 3,
            'notes': 'Forex news and education. Respect ToS.'
        },
        {
            'domain': 'dailyfx.com',
            'name': 'DailyFX',
            'base_url': 'https://www.dailyfx.com',
            'trust_level': 'medium',
            'rate_limit_seconds': 2,
            'notes': 'Market analysis and education. Respect ToS.'
        },
        {
            'domain': 'tradingview.com',
            'name': 'TradingView Docs',
            'base_url': 'https://www.tradingview.com',
            'trust_level': 'high',
            'rate_limit_seconds': 2,
            'notes': 'Pine Script documentation. Public docs only.'
        },
        {
            'domain': 'oanda.com',
            'name': 'OANDA',
            'base_url': 'https://www.oanda.com',
            'trust_level': 'high',
            'rate_limit_seconds': 2,
            'notes': 'Forex broker educational resources. Respect ToS.'
        },
        {
            'domain': 'ig.com',
            'name': 'IG Group',
            'base_url': 'https://www.ig.com',
            'trust_level': 'medium',
            'rate_limit_seconds': 2,
            'notes': 'Broker educational content. Respect ToS.'
        },
    ]
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing knowledge base sources...\n')
        
        created_count = 0
        updated_count = 0
        
        for source_data in self.DEFAULT_SOURCES:
            source, created = Source.objects.update_or_create(
                domain=source_data['domain'],
                defaults={
                    'name': source_data['name'],
                    'base_url': source_data['base_url'],
                    'trust_level': source_data['trust_level'],
                    'rate_limit_seconds': source_data['rate_limit_seconds'],
                    'notes': source_data['notes'],
                    'active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {source.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {source.name}')
        
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Initialization complete!\n'
            f'  Created: {created_count} sources\n'
            f'  Updated: {updated_count} sources\n'
        ))
        self.stdout.write(f'{"="*60}\n')
        self.stdout.write(
            '\nNext steps:\n'
            '  1. Run: python manage.py crawl_knowledge --source investopedia --max-pages 50\n'
            '  2. Run: python manage.py rebuild_kb_index\n'
            '  3. Test: python manage.py test_kb_search "order block"\n'
        )
