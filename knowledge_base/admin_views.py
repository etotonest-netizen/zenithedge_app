"""
Enhanced Knowledge Base Admin Dashboard
Custom views for KB management, statistics, and testing
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json

from knowledge_base.models import (
    KnowledgeEntry, Source, ConceptRelationship, 
    CrawlLog, QueryCache
)


@staff_member_required
def kb_dashboard(request):
    """
    Main Knowledge Base management dashboard
    Shows statistics, recent activity, and quick actions
    """
    # Overall statistics
    total_entries = KnowledgeEntry.objects.count()
    verified_entries = KnowledgeEntry.objects.filter(is_verified=True).count()
    active_entries = KnowledgeEntry.objects.filter(is_active=True).count()
    with_embeddings = KnowledgeEntry.objects.filter(
        embedding_summary__isnull=False
    ).count()
    
    # Quality metrics
    avg_quality = KnowledgeEntry.objects.aggregate(
        avg=Avg('quality_score')
    )['avg'] or 0
    
    high_quality = KnowledgeEntry.objects.filter(quality_score__gte=0.8).count()
    medium_quality = KnowledgeEntry.objects.filter(
        quality_score__gte=0.5, quality_score__lt=0.8
    ).count()
    low_quality = KnowledgeEntry.objects.filter(quality_score__lt=0.5).count()
    
    # Strategy distribution
    strategy_stats = KnowledgeEntry.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent activity
    recent_entries = KnowledgeEntry.objects.order_by('-created_at')[:10]
    recent_crawls = CrawlLog.objects.order_by('-started_at')[:5]
    
    # Cache statistics
    cache_stats = {
        'total': QueryCache.objects.count(),
        'expired': QueryCache.objects.filter(expires_at__lt=timezone.now()).count(),
        'top_queries': QueryCache.objects.order_by('-hit_count')[:5]
    }
    
    # Source statistics
    source_stats = Source.objects.annotate(
        entry_count=Count('entries')
    ).order_by('-entry_count')
    
    # Relationship statistics
    relationship_count = ConceptRelationship.objects.count()
    verified_relationships = ConceptRelationship.objects.filter(is_verified=True).count()
    
    context = {
        'stats': {
            'total_entries': total_entries,
            'verified_entries': verified_entries,
            'active_entries': active_entries,
            'with_embeddings': with_embeddings,
            'embedding_coverage': (with_embeddings / total_entries * 100) if total_entries > 0 else 0,
            'verification_rate': (verified_entries / total_entries * 100) if total_entries > 0 else 0,
            'avg_quality': avg_quality,
            'high_quality': high_quality,
            'medium_quality': medium_quality,
            'low_quality': low_quality,
            'relationship_count': relationship_count,
            'verified_relationships': verified_relationships,
        },
        'strategy_stats': strategy_stats,
        'recent_entries': recent_entries,
        'recent_crawls': recent_crawls,
        'cache_stats': cache_stats,
        'source_stats': source_stats,
    }
    
    return render(request, 'admin/kb_dashboard.html', context)


@staff_member_required
def kb_search_test(request):
    """
    Test semantic search functionality
    """
    results = []
    query = None
    strategy_filter = None
    
    if request.method == 'POST':
        query = request.POST.get('query', '')
        strategy_filter = request.POST.get('strategy', None)
        k = int(request.POST.get('k', 5))
        
        try:
            from knowledge_engine.query_engine import KnowledgeQueryEngine
            engine = KnowledgeQueryEngine()
            
            search_results = engine.search_concept(
                term=query,
                strategy=strategy_filter if strategy_filter else None,
                k=k
            )
            
            results = search_results
            messages.success(request, f'Found {len(results)} results for "{query}"')
            
        except Exception as e:
            messages.error(request, f'Search error: {str(e)}')
    
    # Get available strategies
    strategies = KnowledgeEntry.CATEGORY_CHOICES
    
    context = {
        'query': query,
        'strategy_filter': strategy_filter,
        'results': results,
        'strategies': strategies,
    }
    
    return render(request, 'admin/kb_search_test.html', context)


@staff_member_required
def regenerate_embeddings(request):
    """
    Regenerate embeddings for all entries or selected entries
    """
    if request.method == 'POST':
        entry_ids = request.POST.getlist('entry_ids')
        
        if entry_ids:
            entries = KnowledgeEntry.objects.filter(id__in=entry_ids)
        else:
            entries = KnowledgeEntry.objects.all()
        
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            count = 0
            for entry in entries:
                # Generate embeddings
                summary_emb = model.encode(entry.summary)
                full_emb = model.encode(entry.definition)
                
                entry.embedding_summary = json.dumps(summary_emb.tolist())
                entry.embedding_full = json.dumps(full_emb.tolist())
                entry.save(update_fields=['embedding_summary', 'embedding_full'])
                
                count += 1
            
            messages.success(request, f'Successfully regenerated embeddings for {count} entries')
            
        except Exception as e:
            messages.error(request, f'Error regenerating embeddings: {str(e)}')
        
        return redirect('admin:kb_dashboard')
    
    # GET request - show form
    entries = KnowledgeEntry.objects.all().order_by('term')
    
    context = {
        'entries': entries,
    }
    
    return render(request, 'admin/kb_regenerate_embeddings.html', context)


@staff_member_required
def clear_cache(request):
    """
    Clear query cache
    """
    if request.method == 'POST':
        cache_type = request.POST.get('cache_type', 'expired')
        
        if cache_type == 'all':
            deleted = QueryCache.objects.all().delete()[0]
            messages.success(request, f'Cleared all cache ({deleted} entries)')
        elif cache_type == 'expired':
            deleted = QueryCache.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            messages.success(request, f'Cleared expired cache ({deleted} entries)')
        elif cache_type == 'old':
            cutoff = timezone.now() - timedelta(days=7)
            deleted = QueryCache.objects.filter(
                created_at__lt=cutoff
            ).delete()[0]
            messages.success(request, f'Cleared old cache ({deleted} entries)')
        
        # Also clear Django cache
        from django.core.cache import cache
        cache.clear()
        messages.info(request, 'Cleared Django application cache')
        
        return redirect('admin:kb_dashboard')
    
    # GET request - show confirmation
    cache_stats = {
        'total': QueryCache.objects.count(),
        'expired': QueryCache.objects.filter(expires_at__lt=timezone.now()).count(),
        'old': QueryCache.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=7)
        ).count()
    }
    
    context = {
        'cache_stats': cache_stats,
    }
    
    return render(request, 'admin/kb_clear_cache.html', context)


@staff_member_required
def entry_approval_queue(request):
    """
    Review and approve unverified entries
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        entry_ids = request.POST.getlist('entry_ids')
        
        if action == 'approve':
            updated = KnowledgeEntry.objects.filter(id__in=entry_ids).update(
                is_verified=True
            )
            messages.success(request, f'Approved {updated} entries')
        elif action == 'reject':
            updated = KnowledgeEntry.objects.filter(id__in=entry_ids).update(
                is_active=False
            )
            messages.warning(request, f'Deactivated {updated} entries')
        
        return redirect('admin:kb_approval_queue')
    
    # GET request - show unverified entries
    unverified = KnowledgeEntry.objects.filter(
        is_verified=False, is_active=True
    ).order_by('-created_at')
    
    context = {
        'unverified_entries': unverified,
        'unverified_count': unverified.count(),
    }
    
    return render(request, 'admin/kb_approval_queue.html', context)


@staff_member_required
def kb_statistics(request):
    """
    Detailed statistics and analytics
    """
    # Time-based statistics
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    stats = {
        'created_24h': KnowledgeEntry.objects.filter(created_at__gte=last_24h).count(),
        'created_7d': KnowledgeEntry.objects.filter(created_at__gte=last_7d).count(),
        'created_30d': KnowledgeEntry.objects.filter(created_at__gte=last_30d).count(),
    }
    
    # Difficulty distribution
    difficulty_stats = KnowledgeEntry.objects.values('difficulty').annotate(
        count=Count('id')
    )
    
    # Asset class distribution
    asset_stats = {}
    for entry in KnowledgeEntry.objects.all():
        for asset in entry.asset_classes:
            asset_stats[asset] = asset_stats.get(asset, 0) + 1
    
    # Most viewed entries
    most_viewed = KnowledgeEntry.objects.filter(
        view_count__gt=0
    ).order_by('-view_count')[:10]
    
    # Most related concepts
    most_connected = []
    for entry in KnowledgeEntry.objects.all()[:20]:
        rel_count = (
            ConceptRelationship.objects.filter(source_concept=entry).count() +
            ConceptRelationship.objects.filter(target_concept=entry).count()
        )
        most_connected.append({
            'entry': entry,
            'connection_count': rel_count
        })
    most_connected.sort(key=lambda x: x['connection_count'], reverse=True)
    most_connected = most_connected[:10]
    
    context = {
        'stats': stats,
        'difficulty_stats': difficulty_stats,
        'asset_stats': asset_stats,
        'most_viewed': most_viewed,
        'most_connected': most_connected,
    }
    
    return render(request, 'admin/kb_statistics.html', context)
