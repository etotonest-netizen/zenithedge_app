"""
Django Management Command: Crawl and ingest knowledge from trading sources
Usage: python manage.py crawl_knowledge --source investopedia --max-pages 50
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from knowledge_base.models import Source, KnowledgeEntry, CrawlLog
from knowledge_base.scraper import KnowledgeScraper, SOURCE_CONFIGS
from knowledge_base.normalizer import ContentNormalizer, RelationshipDetector
from knowledge_base.models import ConceptRelationship

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crawl trading knowledge sources and populate KB'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Source to crawl (investopedia, babypips, fxstreet, etc.)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Crawl all active sources'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=100,
            help='Maximum pages to crawl per source'
        )
        parser.add_argument(
            '--rebuild-index',
            action='store_true',
            help='Rebuild FAISS index after crawling'
        )
    
    def handle(self, *args, **options):
        source_name = options.get('source')
        crawl_all = options.get('all')
        max_pages = options.get('max_pages')
        rebuild_index = options.get('rebuild_index')
        
        if not source_name and not crawl_all:
            self.stdout.write(self.style.ERROR('Please specify --source or --all'))
            return
        
        # Initialize components
        scraper = KnowledgeScraper()
        normalizer = ContentNormalizer()
        
        # Determine sources to crawl
        sources_to_crawl = []
        
        if crawl_all:
            sources_to_crawl = Source.objects.filter(active=True)
        else:
            try:
                sources_to_crawl = [Source.objects.get(domain__icontains=source_name, active=True)]
            except Source.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Source not found: {source_name}'))
                return
        
        # Crawl each source
        for source in sources_to_crawl:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.SUCCESS(f'Crawling: {source.name}'))
            self.stdout.write(f'{"="*60}\n')
            
            # Create crawl log
            crawl_log = CrawlLog.objects.create(
                source=source,
                status='running',
                config_snapshot={
                    'max_pages': max_pages,
                    'rate_limit': source.rate_limit_seconds
                }
            )
            
            try:
                # Get source config
                config_key = source.domain.split('.')[0]  # Extract: investopedia from investopedia.com
                source_config = SOURCE_CONFIGS.get(config_key, {})
                source_config['rate_limit_seconds'] = source.rate_limit_seconds
                
                # Crawl
                self.stdout.write(f'Fetching pages (max: {max_pages})...')
                scraped_content = scraper.crawl_source(source_config, max_pages=max_pages)
                
                crawl_log.urls_crawled = len(scraped_content)
                crawl_log.save()
                
                self.stdout.write(self.style.SUCCESS(f'Scraped {len(scraped_content)} pages'))
                
                # Normalize and save
                self.stdout.write('Normalizing content...')
                
                created_count = 0
                updated_count = 0
                skipped_count = 0
                
                for content in scraped_content:
                    # Normalize
                    normalized = normalizer.normalize(content, source.trust_level)
                    
                    if not normalized:
                        skipped_count += 1
                        continue
                    
                    # Save to DB
                    try:
                        # Check if entry exists
                        existing = KnowledgeEntry.objects.filter(
                            term__iexact=normalized.term,
                            source=source
                        ).first()
                        
                        if existing:
                            # Update existing
                            existing.summary = normalized.summary
                            existing.definition = normalized.definition
                            existing.examples = normalized.examples
                            existing.category = normalized.category
                            existing.difficulty = normalized.difficulty
                            existing.asset_classes = normalized.asset_classes
                            existing.quality_score = normalized.quality_score
                            existing.relevance_score = normalized.relevance_score
                            existing.completeness_score = normalized.completeness_score
                            existing.crawl_date = timezone.now()
                            existing.save()
                            updated_count += 1
                        else:
                            # Create new
                            KnowledgeEntry.objects.create(
                                term=normalized.term,
                                aliases=normalized.aliases,
                                summary=normalized.summary,
                                definition=normalized.definition,
                                examples='\n\n'.join(normalized.examples),
                                category=normalized.category,
                                difficulty=normalized.difficulty,
                                asset_classes=normalized.asset_classes,
                                source=source,
                                source_url=content.url,
                                quality_score=normalized.quality_score,
                                relevance_score=normalized.relevance_score,
                                completeness_score=normalized.completeness_score,
                                license_info='Fair Use - Educational',
                            )
                            created_count += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to save entry '{normalized.term}': {e}")
                        skipped_count += 1
                
                # Update crawl log
                crawl_log.entries_created = created_count
                crawl_log.entries_updated = updated_count
                crawl_log.entries_skipped = skipped_count
                crawl_log.status = 'completed'
                crawl_log.completed_at = timezone.now()
                crawl_log.save()
                
                # Update source stats
                source.last_crawled = timezone.now()
                source.total_entries = KnowledgeEntry.objects.filter(source=source).count()
                source.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'\n✅ Crawl complete:\n'
                    f'  Created: {created_count}\n'
                    f'  Updated: {updated_count}\n'
                    f'  Skipped: {skipped_count}\n'
                ))
                
            except Exception as e:
                crawl_log.status = 'failed'
                crawl_log.errors_count += 1
                crawl_log.error_log = str(e)
                crawl_log.completed_at = timezone.now()
                crawl_log.save()
                
                self.stdout.write(self.style.ERROR(f'Crawl failed: {e}'))
        
        # Rebuild FAISS index if requested
        if rebuild_index:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('Rebuilding FAISS index...')
            
            try:
                from knowledge_base.kb_search import KnowledgeBaseSearch
                kb_search = KnowledgeBaseSearch()
                kb_search.rebuild_index()
                self.stdout.write(self.style.SUCCESS('✅ Index rebuilt'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Index rebuild failed: {e}'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('All crawls complete!'))
