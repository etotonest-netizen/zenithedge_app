"""
Knowledge Base Models for Trading Dictionary & Semantic Search
Stores scraped trading concepts, definitions, examples, and relationships
"""
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import json


class Source(models.Model):
    """
    Tracks authoritative sources for trading knowledge
    """
    TRUST_LEVEL_CHOICES = [
        ('high', 'High - Authoritative (Investopedia, Official Docs)'),
        ('medium', 'Medium - Reputable (FXStreet, BabyPips)'),
        ('low', 'Low - Community/Blog'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    domain = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    base_url = models.URLField()
    trust_level = models.CharField(max_length=20, choices=TRUST_LEVEL_CHOICES, default='medium')
    
    # Crawling config
    respect_robots_txt = models.BooleanField(default=True)
    rate_limit_seconds = models.IntegerField(default=2, help_text="Seconds between requests")
    max_depth = models.IntegerField(default=3, help_text="Max crawl depth from seed URLs")
    
    # Metadata
    last_crawled = models.DateTimeField(null=True, blank=True)
    total_entries = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Legal notes, TOS constraints, etc.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-trust_level', 'name']
        verbose_name = 'Knowledge Source'
        verbose_name_plural = 'Knowledge Sources'
    
    def __str__(self):
        return f"{self.name} ({self.trust_level})"


class KnowledgeEntry(models.Model):
    """
    Core knowledge base entries - trading concepts, definitions, examples
    """
    # 10 Core Strategy Domains
    CATEGORY_CHOICES = [
        ('smc', 'Smart Money Concepts'),
        ('ict', 'Inner Circle Trader'),
        ('trend', 'Trend-Following Systems'),
        ('breakout', 'Breakout Strategies'),
        ('mean_reversion', 'Mean Reversion Models'),
        ('squeeze', 'Squeeze Volatility Setups'),
        ('scalping', 'Scalping / Momentum Trading'),
        ('vwap', 'VWAP Reclaim Systems'),
        ('supply_demand', 'Supply & Demand Zone Analysis'),
        ('confluence', 'Multi-Timeframe Confluence'),
        ('ta', 'Technical Analysis'),
        ('risk', 'Risk Management'),
        ('psychology', 'Trading Psychology'),
        ('fundamentals', 'Fundamental Analysis'),
        ('orderflow', 'Order Flow'),
        ('market_structure', 'Market Structure'),
        ('liquidity', 'Liquidity Concepts'),
        ('other', 'Other'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('intro', 'Introductory'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    ASSET_CLASS_CHOICES = [
        ('any', 'Universal'),
        ('forex', 'Forex'),
        ('crypto', 'Cryptocurrency'),
        ('stocks', 'Stocks'),
        ('futures', 'Futures'),
        ('commodities', 'Commodities'),
    ]
    
    # Core content
    term = models.CharField(max_length=255, db_index=True, help_text="Canonical term (e.g., 'Order Block')")
    aliases = models.JSONField(default=list, help_text="Alternative names (e.g., ['OB', 'demand zone'])")
    
    summary = models.TextField(help_text="One-liner definition (1-2 sentences)")
    definition = models.TextField(help_text="Detailed explanation (3-5 paragraphs)")
    examples = models.TextField(blank=True, help_text="Usage examples and scenarios")
    
    # Strategy-Aware Knowledge Engine Fields
    market_behavior_patterns = models.JSONField(default=list, help_text="Observable price patterns for this concept")
    trade_structures = models.JSONField(default=list, help_text="Key setups and entry/exit structures")
    psychology_context = models.TextField(blank=True, help_text="Psychological aspects and trader behavior")
    common_pitfalls = models.JSONField(default=list, help_text="Common mistakes and misconceptions")
    visual_description = models.TextField(blank=True, help_text="Text-based chart pattern description")
    related_concepts = models.JSONField(default=list, help_text="Related strategy concepts")
    
    # Classification
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    asset_classes = models.JSONField(default=list, help_text="Applicable asset classes")
    
    # Provenance
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='entries')
    source_url = models.URLField(help_text="Original page URL")
    crawl_date = models.DateTimeField(default=timezone.now)
    license_info = models.CharField(max_length=255, blank=True, help_text="CC-BY, Fair Use, etc.")
    
    # Embeddings (stored as JSON array for portability)
    embedding_summary = models.JSONField(null=True, blank=True, help_text="Vector for summary text")
    embedding_full = models.JSONField(null=True, blank=True, help_text="Vector for full definition")
    embedding_model = models.CharField(max_length=100, default='all-MiniLM-L6-v2')
    
    # Quality metrics
    quality_score = models.FloatField(default=0.5, db_index=True, help_text="0.0-1.0 quality rating")
    relevance_score = models.FloatField(default=0.5, help_text="How relevant to trading")
    completeness_score = models.FloatField(default=0.5, help_text="Has examples, definition, etc.")
    
    # Metadata
    view_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    version = models.IntegerField(default=1, help_text="KB version for snapshot tracking")
    
    is_verified = models.BooleanField(default=False, help_text="Human-reviewed and approved")
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-quality_score', 'term']
        verbose_name = 'Knowledge Entry'
        verbose_name_plural = 'Knowledge Entries'
        indexes = [
            models.Index(fields=['category', 'quality_score']),
            models.Index(fields=['term', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.term} ({self.category})"
    
    def increment_usage(self):
        """Track KB entry usage for analytics"""
        self.view_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['view_count', 'last_used'])
    
    def get_aliases_display(self):
        """Return comma-separated aliases"""
        return ', '.join(self.aliases) if self.aliases else 'None'


class ConceptRelationship(models.Model):
    """
    Graph edges between trading concepts for contextual explanations
    """
    RELATIONSHIP_TYPES = [
        ('related_to', 'Related To'),
        ('is_subconcept_of', 'Is Subconcept Of'),
        ('prerequisite_for', 'Prerequisite For'),
        ('contraindicates', 'Contraindicates'),
        ('common_with', 'Commonly Occurs With'),
        ('alternative_to', 'Alternative To'),
    ]
    
    source_concept = models.ForeignKey(
        KnowledgeEntry, 
        on_delete=models.CASCADE, 
        related_name='outgoing_relationships'
    )
    target_concept = models.ForeignKey(
        KnowledgeEntry, 
        on_delete=models.CASCADE, 
        related_name='incoming_relationships'
    )
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_TYPES, db_index=True)
    
    strength = models.FloatField(default=1.0, help_text="Relationship strength (0.0-1.0)")
    description = models.TextField(blank=True, help_text="Why these concepts are related")
    
    # Auto-detected or human-curated
    is_auto_detected = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['source_concept', 'target_concept', 'relationship_type']
        ordering = ['-strength', 'relationship_type']
        verbose_name = 'Concept Relationship'
        verbose_name_plural = 'Concept Relationships'
    
    def __str__(self):
        return f"{self.source_concept.term} {self.relationship_type} {self.target_concept.term}"


class CrawlLog(models.Model):
    """
    Audit trail for all scraping activities
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]
    
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='crawl_logs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Statistics
    urls_discovered = models.IntegerField(default=0)
    urls_crawled = models.IntegerField(default=0)
    entries_created = models.IntegerField(default=0)
    entries_updated = models.IntegerField(default=0)
    entries_skipped = models.IntegerField(default=0)
    
    # Error tracking
    errors_count = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
    
    # Config snapshot
    config_snapshot = models.JSONField(default=dict, help_text="Crawl parameters used")
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Crawl Log'
        verbose_name_plural = 'Crawl Logs'
    
    def __str__(self):
        return f"{self.source.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')} ({self.status})"
    
    def duration(self):
        """Calculate crawl duration"""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return f"{delta.total_seconds():.1f}s"
        return "In progress"


class KBSnapshot(models.Model):
    """
    Versioned snapshots of the knowledge base for reproducibility
    """
    version = models.IntegerField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Statistics
    total_entries = models.IntegerField(default=0)
    total_relationships = models.IntegerField(default=0)
    total_sources = models.IntegerField(default=0)
    
    # Snapshot metadata
    description = models.TextField(blank=True, help_text="What changed in this version")
    snapshot_data = models.JSONField(default=dict, help_text="Compressed KB state")
    
    # File backup path
    backup_path = models.CharField(max_length=512, blank=True, help_text="Path to FAISS index backup")
    
    is_current = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        ordering = ['-version']
        verbose_name = 'KB Snapshot'
        verbose_name_plural = 'KB Snapshots'
    
    def __str__(self):
        return f"KB v{self.version} - {self.created_at.strftime('%Y-%m-%d')} ({self.total_entries} entries)"


class QueryCache(models.Model):
    """
    Cache semantic search results for performance
    """
    query_text = models.CharField(max_length=512, db_index=True)
    query_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Cache payload
    results = models.JSONField(help_text="Top-K KB entry IDs + scores")
    embedding = models.JSONField(null=True, blank=True)
    
    # Cache metadata
    hit_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Context
    symbol = models.CharField(max_length=20, blank=True, db_index=True)
    concept_tags = models.JSONField(default=list, help_text="Related concepts for invalidation")
    
    class Meta:
        ordering = ['-last_accessed']
        verbose_name = 'Query Cache'
        verbose_name_plural = 'Query Cache'
        indexes = [
            models.Index(fields=['expires_at', 'symbol']),
        ]
    
    def __str__(self):
        return f"{self.query_text[:50]}... (hits: {self.hit_count})"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
