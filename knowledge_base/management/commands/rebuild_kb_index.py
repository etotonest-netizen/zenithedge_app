"""
Django Management Command: Rebuild FAISS index from KB entries
Usage: python manage.py rebuild_kb_index
"""
from django.core.management.base import BaseCommand
from knowledge_base.kb_search import KnowledgeBaseSearch


class Command(BaseCommand):
    help = 'Rebuild FAISS vector index from knowledge base entries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing entries'
        )
    
    def handle(self, *args, **options):
        batch_size = options.get('batch_size')
        
        self.stdout.write('='*60)
        self.stdout.write('Rebuilding FAISS index...')
        self.stdout.write('='*60 + '\n')
        
        try:
            kb_search = KnowledgeBaseSearch()
            kb_search.rebuild_index(batch_size=batch_size)
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✅ Index rebuilt successfully!'))
            self.stdout.write('='*60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Index rebuild failed: {e}'))
