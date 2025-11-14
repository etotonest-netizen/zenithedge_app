"""
Django Management Command: Test KB semantic search
Usage: python manage.py test_kb_search "order block" --k 5
"""
from django.core.management.base import BaseCommand
from knowledge_base.kb_search import KnowledgeBaseSearch


class Command(BaseCommand):
    help = 'Test semantic search over knowledge base'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'query',
            type=str,
            help='Search query'
        )
        parser.add_argument(
            '--k',
            type=int,
            default=5,
            help='Number of results to return'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Filter by category (smc, ict, ta, etc.)'
        )
        parser.add_argument(
            '--asset-class',
            type=str,
            help='Filter by asset class (forex, crypto, stocks, etc.)'
        )
    
    def handle(self, *args, **options):
        query = options.get('query')
        k = options.get('k')
        category = options.get('category')
        asset_class = options.get('asset_class')
        
        self.stdout.write('='*60)
        self.stdout.write(f'Searching KB: "{query}"')
        if category:
            self.stdout.write(f'Category filter: {category}')
        if asset_class:
            self.stdout.write(f'Asset class filter: {asset_class}')
        self.stdout.write('='*60 + '\n')
        
        try:
            kb_search = KnowledgeBaseSearch()
            results = kb_search.search(
                query=query,
                k=k,
                category=category,
                asset_class=asset_class,
                use_cache=False
            )
            
            if not results:
                self.stdout.write(self.style.WARNING('No results found'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(results)} results:\n'))
            
            for i, result in enumerate(results, 1):
                entry = result['entry']
                score = result['score']
                
                self.stdout.write(f'\n{"-"*60}')
                self.stdout.write(self.style.SUCCESS(f'{i}. {entry.term}'))
                self.stdout.write(f'{"-"*60}')
                self.stdout.write(f'Score: {score:.4f} | Quality: {entry.quality_score:.2f}')
                self.stdout.write(f'Category: {entry.get_category_display()} | Difficulty: {entry.difficulty}')
                self.stdout.write(f'Source: {entry.source.name} ({entry.source.trust_level})')
                self.stdout.write(f'\nSummary:')
                self.stdout.write(f'{entry.summary}\n')
                
                if entry.aliases:
                    self.stdout.write(f'Aliases: {entry.get_aliases_display()}')
                
                self.stdout.write(f'\nURL: {entry.source_url}')
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('Search complete!'))
            self.stdout.write('='*60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Search failed: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
