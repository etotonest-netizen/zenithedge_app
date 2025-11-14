"""
Embedding & Semantic Search System for Knowledge Base
Uses sentence-transformers + FAISS for fast vector search
"""
import os
import logging
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed - embeddings disabled")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("faiss not installed - using fallback search")

from django.conf import settings
from django.utils import timezone as dj_timezone
from .models import KnowledgeEntry, QueryCache, ConceptRelationship

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Generate embeddings using sentence-transformers"""
    
    DEFAULT_MODEL = 'all-MiniLM-L6-v2'  # Fast, lightweight model
    
    def __init__(self, model_name: str = DEFAULT_MODEL, use_cuda: bool = False):
        """
        Initialize embedding engine
        
        Args:
            model_name: SentenceTransformer model name
            use_cuda: Use GPU if available
        """
        self.model_name = model_name
        self.model = None
        self.dimension = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                device = 'cuda' if use_cuda else 'cpu'
                self.model = SentenceTransformer(model_name, device=device)
                # Get embedding dimension
                test_embedding = self.model.encode("test")
                self.dimension = len(test_embedding)
                logger.info(f"Loaded embedding model: {model_name} (dim={self.dimension})")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
        else:
            logger.error("sentence-transformers not available - embeddings disabled")
    
    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """
        Encode texts to embeddings
        
        Args:
            texts: List of text strings
            show_progress: Show progress bar
        
        Returns:
            numpy array of shape (len(texts), dimension)
        """
        if not self.model:
            # Fallback: return random embeddings (for testing)
            logger.warning("Using random embeddings - model not loaded")
            return np.random.rand(len(texts), 384).astype('float32')
        
        embeddings = self.model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        return embeddings.astype('float32')
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text"""
        return self.encode([text])[0]


class FAISSIndex:
    """FAISS vector index for semantic search"""
    
    def __init__(self, dimension: int = 384, index_type: str = 'flat'):
        """
        Initialize FAISS index
        
        Args:
            dimension: Embedding dimension
            index_type: 'flat' (exact) or 'ivf' (approximate for large datasets)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.id_map = []  # Map FAISS index positions to KB entry IDs
        
        if FAISS_AVAILABLE:
            self._build_index()
        else:
            logger.warning("FAISS not available - using fallback search")
    
    def _build_index(self):
        """Build FAISS index"""
        if self.index_type == 'flat':
            # Exact search - good for < 1M vectors
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == 'ivf':
            # Approximate search - good for > 1M vectors
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        
        logger.info(f"Built FAISS index: {self.index_type} (dim={self.dimension})")
    
    def add_vectors(self, vectors: np.ndarray, ids: List[int]):
        """
        Add vectors to index
        
        Args:
            vectors: numpy array of shape (N, dimension)
            ids: List of KB entry IDs corresponding to vectors
        """
        if not FAISS_AVAILABLE or self.index is None:
            return
        
        # Train index if needed (IVF only)
        if self.index_type == 'ivf' and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(vectors)
        
        # Add vectors
        self.index.add(vectors)
        self.id_map.extend(ids)
        
        logger.info(f"Added {len(ids)} vectors to index (total: {len(self.id_map)})")
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for nearest neighbors
        
        Args:
            query_vector: Query embedding (1D array)
            k: Number of results to return
        
        Returns:
            List of (entry_id, distance) tuples
        """
        if not FAISS_AVAILABLE or self.index is None:
            return []
        
        # Reshape query to (1, dimension)
        query = query_vector.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query, k)
        
        # Map indices to entry IDs
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.id_map):
                entry_id = self.id_map[idx]
                results.append((entry_id, float(dist)))
        
        return results
    
    def save(self, filepath: str):
        """Save index to disk"""
        if not FAISS_AVAILABLE or self.index is None:
            return
        
        # Save FAISS index
        faiss.write_index(self.index, filepath)
        
        # Save ID map
        with open(filepath + '.idmap', 'wb') as f:
            pickle.dump(self.id_map, f)
        
        logger.info(f"Saved FAISS index to {filepath}")
    
    def load(self, filepath: str):
        """Load index from disk"""
        if not FAISS_AVAILABLE:
            return
        
        # Load FAISS index
        self.index = faiss.read_index(filepath)
        
        # Load ID map
        with open(filepath + '.idmap', 'rb') as f:
            self.id_map = pickle.load(f)
        
        logger.info(f"Loaded FAISS index from {filepath} ({len(self.id_map)} vectors)")


class KnowledgeBaseSearch:
    """High-level semantic search interface for KB"""
    
    def __init__(self, cache_timeout_hours: int = 6):
        """
        Initialize KB search
        
        Args:
            cache_timeout_hours: Query cache timeout
        """
        self.embedding_engine = EmbeddingEngine()
        self.faiss_index = FAISSIndex(dimension=self.embedding_engine.dimension)
        self.cache_timeout = timedelta(hours=cache_timeout_hours)
        
        # Load existing index if available
        self._load_index()
    
    def _get_index_path(self) -> str:
        """Get FAISS index filepath"""
        kb_dir = os.path.join(settings.BASE_DIR, 'data', 'knowledge_base')
        os.makedirs(kb_dir, exist_ok=True)
        return os.path.join(kb_dir, 'faiss_index.bin')
    
    def _load_index(self):
        """Load existing FAISS index"""
        index_path = self._get_index_path()
        if os.path.exists(index_path):
            try:
                self.faiss_index.load(index_path)
                logger.info("Loaded existing FAISS index")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
    
    def _save_index(self):
        """Save FAISS index"""
        index_path = self._get_index_path()
        try:
            self.faiss_index.save(index_path)
            logger.info("Saved FAISS index")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    def rebuild_index(self, batch_size: int = 100):
        """
        Rebuild FAISS index from all KB entries
        
        Args:
            batch_size: Process entries in batches
        """
        logger.info("Rebuilding FAISS index from KB...")
        
        # Get all active entries
        entries = KnowledgeEntry.objects.filter(is_active=True).order_by('id')
        total = entries.count()
        
        # Rebuild index
        self.faiss_index = FAISSIndex(dimension=self.embedding_engine.dimension)
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = entries[i:i + batch_size]
            
            # Collect texts and IDs
            texts = []
            ids = []
            
            for entry in batch:
                # Use summary for embedding (faster, good for search)
                texts.append(entry.summary)
                ids.append(entry.id)
            
            # Generate embeddings
            embeddings = self.embedding_engine.encode(texts)
            
            # Add to index
            self.faiss_index.add_vectors(embeddings, ids)
            
            # Save embeddings to DB (for reproducibility)
            for entry, embedding in zip(batch, embeddings):
                entry.embedding_summary = embedding.tolist()
                entry.save(update_fields=['embedding_summary'])
            
            logger.info(f"Processed {i + len(batch)}/{total} entries")
        
        # Save index
        self._save_index()
        
        logger.info(f"Index rebuilt: {total} entries indexed")
    
    def add_entry_to_index(self, entry: KnowledgeEntry):
        """Add single entry to index"""
        # Generate embedding
        embedding = self.embedding_engine.encode_single(entry.summary)
        
        # Add to index
        self.faiss_index.add_vectors(
            embedding.reshape(1, -1),
            [entry.id]
        )
        
        # Save embedding to DB
        entry.embedding_summary = embedding.tolist()
        entry.save(update_fields=['embedding_summary'])
    
    def _get_query_hash(self, query: str, symbol: str = '') -> str:
        """Generate hash for query caching"""
        key = f"{query}|{symbol}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def search(
        self,
        query: str,
        k: int = 10,
        category: Optional[str] = None,
        asset_class: Optional[str] = None,
        min_quality: float = 0.3,
        use_cache: bool = True,
        symbol: str = ''
    ) -> List[Dict]:
        """
        Semantic search over knowledge base
        
        Args:
            query: Search query text
            k: Number of results
            category: Filter by category
            asset_class: Filter by asset class
            min_quality: Minimum quality score
            use_cache: Use query cache
            symbol: Trading symbol for cache key
        
        Returns:
            List of dicts with entry info + similarity scores
        """
        # Check cache
        if use_cache:
            query_hash = self._get_query_hash(query, symbol)
            cached = QueryCache.objects.filter(
                query_hash=query_hash,
                expires_at__gt=dj_timezone.now()
            ).first()
            
            if cached:
                cached.hit_count += 1
                cached.save(update_fields=['hit_count', 'last_accessed'])
                
                # Fetch entries from cached IDs
                entry_ids = [r['id'] for r in cached.results]
                entries = KnowledgeEntry.objects.filter(id__in=entry_ids)
                entry_map = {e.id: e for e in entries}
                
                results = []
                for result in cached.results:
                    if result['id'] in entry_map:
                        entry = entry_map[result['id']]
                        results.append({
                            'entry': entry,
                            'score': result['score'],
                            'cached': True
                        })
                
                logger.debug(f"Cache hit: {query[:50]}... ({len(results)} results)")
                return results
        
        # Generate query embedding
        query_embedding = self.embedding_engine.encode_single(query)
        
        # Search FAISS index
        faiss_results = self.faiss_index.search(query_embedding, k=k*2)  # Get more for filtering
        
        if not faiss_results:
            logger.warning(f"No FAISS results for query: {query}")
            return []
        
        # Fetch entries
        entry_ids = [r[0] for r in faiss_results]
        entries = KnowledgeEntry.objects.filter(
            id__in=entry_ids,
            is_active=True,
            quality_score__gte=min_quality
        )
        
        # Apply filters
        if category:
            entries = entries.filter(category=category)
        
        if asset_class:
            entries = entries.filter(asset_classes__contains=[asset_class])
        
        # Map distances to scores (convert L2 distance to similarity)
        entry_map = {e.id: e for e in entries}
        results = []
        
        for entry_id, distance in faiss_results:
            if entry_id in entry_map:
                # Convert distance to similarity score (0-1 range)
                # L2 distance -> similarity via exponential decay
                similarity = np.exp(-distance / 10.0)  # Adjust scale as needed
                
                results.append({
                    'entry': entry_map[entry_id],
                    'score': float(similarity),
                    'distance': distance,
                    'cached': False
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]
        
        # Cache results
        if use_cache and results:
            expires_at = dj_timezone.now() + self.cache_timeout
            query_hash = self._get_query_hash(query, symbol)
            
            QueryCache.objects.update_or_create(
                query_hash=query_hash,
                defaults={
                    'query_text': query[:512],
                    'results': [{'id': r['entry'].id, 'score': r['score']} for r in results],
                    'embedding': query_embedding.tolist(),
                    'expires_at': expires_at,
                    'symbol': symbol,
                    'concept_tags': [r['entry'].term for r in results[:3]]
                }
            )
        
        logger.info(f"Search complete: {query[:50]}... ({len(results)} results)")
        return results
    
    def get_related_concepts(
        self,
        entry: KnowledgeEntry,
        relationship_type: Optional[str] = None,
        max_depth: int = 1
    ) -> List[Dict]:
        """
        Get related concepts via knowledge graph
        
        Args:
            entry: Source KB entry
            relationship_type: Filter by relationship type
            max_depth: Graph traversal depth
        
        Returns:
            List of related entries with relationship info
        """
        results = []
        visited = {entry.id}
        
        # Get direct relationships
        relationships = ConceptRelationship.objects.filter(
            source_concept=entry
        )
        
        if relationship_type:
            relationships = relationships.filter(relationship_type=relationship_type)
        
        relationships = relationships.select_related('target_concept').order_by('-strength')
        
        for rel in relationships:
            if rel.target_concept.id not in visited:
                results.append({
                    'entry': rel.target_concept,
                    'relationship': rel.relationship_type,
                    'strength': rel.strength,
                    'depth': 1
                })
                visited.add(rel.target_concept.id)
        
        return results
    
    def clear_cache(self, symbol: Optional[str] = None, older_than_hours: Optional[int] = None):
        """
        Clear query cache
        
        Args:
            symbol: Clear cache for specific symbol
            older_than_hours: Clear cache older than N hours
        """
        qs = QueryCache.objects.all()
        
        if symbol:
            qs = qs.filter(symbol=symbol)
        
        if older_than_hours:
            cutoff = dj_timezone.now() - timedelta(hours=older_than_hours)
            qs = qs.filter(created_at__lt=cutoff)
        
        deleted_count = qs.delete()[0]
        logger.info(f"Cleared {deleted_count} cached queries")
        
        return deleted_count
