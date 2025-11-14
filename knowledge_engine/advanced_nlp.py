"""
Advanced NLP Pipeline for Strategy-Aware Knowledge Processing
Includes: T5 summarization, concept extraction, relationship detection, paraphrasing
"""
import re
import json
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

import numpy as np

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from transformers import T5Tokenizer, T5ForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .strategy_domains import STRATEGY_DOMAINS, classify_content_by_keywords

logger = logging.getLogger(__name__)


class T5Summarizer:
    """Local T5-small model for generating concise summaries"""
    
    def __init__(self, model_name='t5-small'):
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("transformers not available - summarization disabled")
            self.model = None
            return
        
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(model_name)
            logger.info(f"Loaded T5 model: {model_name}")
        except Exception as e:
            logger.error(f"Error loading T5 model: {e}")
            self.model = None
    
    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Generate summary of text
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length in tokens
            min_length: Minimum summary length in tokens
            
        Returns:
            Summary text
        """
        if not self.model:
            # Fallback: return first sentences
            return self._fallback_summary(text, max_length)
        
        try:
            # Prepare input
            input_text = f"summarize: {text[:1000]}"  # Limit input
            inputs = self.tokenizer.encode(input_text, return_tensors='pt', max_length=512, truncation=True)
            
            # Generate summary
            outputs = self.model.generate(
                inputs,
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
            
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return summary
            
        except Exception as e:
            logger.error(f"Error in T5 summarization: {e}")
            return self._fallback_summary(text, max_length)
    
    def _fallback_summary(self, text: str, max_length: int) -> str:
        """Fallback summary: take first N chars"""
        sentences = re.split(r'[.!?]\s+', text)
        summary = []
        length = 0
        
        for sent in sentences:
            if length + len(sent) > max_length * 5:  # Approx chars
                break
            summary.append(sent)
            length += len(sent)
        
        return '. '.join(summary) + '.'


class StrategyConceptExtractor:
    """Extract strategy-specific concepts and entities from text"""
    
    def __init__(self):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
                logger.info("Loaded spaCy model")
            except:
                logger.warning("spaCy model not loaded")
        
        # Build concept index from all strategies
        self.concept_index = {}
        for strategy, info in STRATEGY_DOMAINS.items():
            for concept in info['core_concepts']:
                self.concept_index[concept.lower()] = {
                    'strategy': strategy,
                    'canonical': concept
                }
    
    def extract_concepts(self, text: str, strategy: str = None) -> List[Dict]:
        """
        Extract trading concepts from text
        
        Args:
            text: Input text
            strategy: Optional strategy filter
            
        Returns:
            List of extracted concept dicts
        """
        text_lower = text.lower()
        found_concepts = []
        
        # Exact match extraction
        for concept, info in self.concept_index.items():
            if strategy and info['strategy'] != strategy:
                continue
            
            if concept in text_lower:
                # Find context around concept
                pattern = re.compile(rf'.{{0,100}}{re.escape(concept)}.{{0,100}}', re.IGNORECASE)
                matches = pattern.findall(text)
                
                for match in matches[:3]:  # Max 3 contexts per concept
                    found_concepts.append({
                        'concept': info['canonical'],
                        'strategy': info['strategy'],
                        'context': match.strip(),
                        'confidence': 1.0
                    })
        
        # NER extraction if spaCy available
        if self.nlp:
            doc = self.nlp(text[:5000])  # Limit text length
            
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'MONEY', 'PERCENT']:
                    # Could be trading-related
                    found_concepts.append({
                        'concept': ent.text,
                        'strategy': 'ta',  # Default
                        'context': ent.sent.text[:200],
                        'confidence': 0.5,
                        'entity_type': ent.label_
                    })
        
        return found_concepts
    
    def extract_noun_phrases(self, text: str) -> List[str]:
        """Extract noun phrases that might be concepts"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text[:5000])
        phrases = []
        
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 4:  # Max 4 words
                phrases.append(chunk.text)
        
        return phrases


class ConceptRelationshipDetector:
    """Detect relationships between trading concepts"""
    
    RELATIONSHIP_PATTERNS = {
        'prerequisite': [
            r'before.*?(?:can|should|must)',
            r'requires.*?understanding',
            r'need.*?to.*?know'
        ],
        'related': [
            r'(?:similar to|like|related to|connected to)',
            r'(?:also|additionally|furthermore)',
            r'(?:combined with|used with|paired with)'
        ],
        'opposite': [
            r'(?:opposite of|contrary to|versus|vs)',
            r'(?:instead of|rather than)',
            r'(?:not.*?but)'
        ],
        'example_of': [
            r'(?:example of|instance of|type of)',
            r'(?:such as|including|e\.g\.)',
            r'(?:form of|kind of)'
        ]
    }
    
    def detect_relationships(
        self,
        source_concept: str,
        text: str,
        all_concepts: List[str]
    ) -> List[Dict]:
        """
        Detect relationships between source concept and other concepts in text
        
        Args:
            source_concept: Main concept
            text: Text containing relationships
            all_concepts: List of all known concepts
            
        Returns:
            List of relationship dicts
        """
        relationships = []
        text_lower = text.lower()
        source_lower = source_concept.lower()
        
        # Find source concept in text
        if source_lower not in text_lower:
            return []
        
        # Check for each relationship type
        for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
            for pattern in patterns:
                # Build regex to capture concept pairs
                full_pattern = rf'{re.escape(source_lower)}\s+{pattern}\s+(\w+(?:\s+\w+){{0,3}})'
                matches = re.findall(full_pattern, text_lower, re.IGNORECASE)
                
                for match in matches:
                    # Check if match is a known concept
                    for concept in all_concepts:
                        if concept.lower() in match.lower():
                            relationships.append({
                                'source': source_concept,
                                'target': concept,
                                'type': rel_type,
                                'confidence': 0.8,
                                'context': match
                            })
        
        return relationships


class StrategyClusterer:
    """Build strategy clusters for cross-strategy reasoning"""
    
    def __init__(self):
        self.clusters = defaultdict(list)
        self.concept_vectors = {}
    
    def build_clusters(self, entries: List[Dict], embeddings: Dict[str, np.ndarray]):
        """
        Build strategy clusters from entries and their embeddings
        
        Args:
            entries: List of knowledge entries
            embeddings: Dict mapping entry IDs to embedding vectors
        """
        # Group by strategy
        strategy_groups = defaultdict(list)
        for entry in entries:
            strategy = entry.get('strategy', 'ta')
            strategy_groups[strategy].append(entry)
        
        # Compute centroid for each strategy
        for strategy, group in strategy_groups.items():
            vectors = []
            for entry in group:
                entry_id = entry.get('id')
                if entry_id in embeddings:
                    vectors.append(embeddings[entry_id])
            
            if vectors:
                centroid = np.mean(vectors, axis=0)
                self.clusters[strategy] = {
                    'centroid': centroid,
                    'count': len(group),
                    'concepts': [e.get('concept') for e in group]
                }
        
        logger.info(f"Built {len(self.clusters)} strategy clusters")
    
    def find_related_strategies(self, strategy: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Find strategies most related to given strategy
        
        Args:
            strategy: Source strategy code
            top_k: Number of results
            
        Returns:
            List of (strategy_code, similarity) tuples
        """
        if strategy not in self.clusters:
            return []
        
        source_centroid = self.clusters[strategy]['centroid']
        similarities = []
        
        for other_strategy, cluster_info in self.clusters.items():
            if other_strategy == strategy:
                continue
            
            other_centroid = cluster_info['centroid']
            similarity = np.dot(source_centroid, other_centroid) / (
                np.linalg.norm(source_centroid) * np.linalg.norm(other_centroid)
            )
            similarities.append((other_strategy, float(similarity)))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class TextParaphraser:
    """Generate paraphrased versions to avoid repetition"""
    
    TEMPLATES = {
        'definition': [
            "{concept} refers to {definition}",
            "{concept} is defined as {definition}",
            "In trading, {concept} means {definition}",
            "{concept} can be understood as {definition}",
            "The term {concept} describes {definition}"
        ],
        'example': [
            "For example, {example}",
            "Consider this: {example}",
            "A typical case: {example}",
            "This is illustrated by {example}",
            "One instance: {example}"
        ],
        'insight': [
            "This {behavior} typically indicates {implication}",
            "When {behavior} occurs, it often suggests {implication}",
            "{behavior} is commonly seen when {implication}",
            "Traders observe {behavior}, which signals {implication}",
            "The presence of {behavior} hints at {implication}"
        ]
    }
    
    def paraphrase(self, text: str, template_type: str = 'definition', **kwargs) -> str:
        """
        Generate paraphrased version of text
        
        Args:
            text: Original text
            template_type: Type of template to use
            **kwargs: Variables for template
            
        Returns:
            Paraphrased text
        """
        if template_type not in self.TEMPLATES:
            return text
        
        templates = self.TEMPLATES[template_type]
        import random
        template = random.choice(templates)
        
        try:
            return template.format(**kwargs)
        except KeyError:
            return text
    
    def vary_sentence_structure(self, sentences: List[str]) -> List[str]:
        """Vary sentence structures to avoid repetition"""
        varied = []
        
        for sent in sentences:
            # Simple variations
            if sent.startswith('The '):
                varied.append(sent)
            elif sent.startswith('This '):
                varied.append(sent.replace('This ', 'The ', 1))
            else:
                varied.append(sent)
        
        return varied


class ContentQualityAnalyzer:
    """Analyze quality and readability of scraped content"""
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze content quality
        
        Returns:
            Dict with quality metrics
        """
        metrics = {
            'length': len(text),
            'sentence_count': len(re.split(r'[.!?]\s+', text)),
            'word_count': len(text.split()),
            'avg_sentence_length': 0,
            'readability': 0,
            'trading_term_density': 0
        }
        
        if metrics['sentence_count'] > 0:
            metrics['avg_sentence_length'] = metrics['word_count'] / metrics['sentence_count']
        
        # Readability (simple heuristic)
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text[:1000])
                metrics['readability'] = min(1.0, len(blob.words) / 100)
            except:
                pass
        
        # Trading term density
        trading_terms = 0
        text_lower = text.lower()
        for strategy_info in STRATEGY_DOMAINS.values():
            for concept in strategy_info['core_concepts']:
                if concept.lower() in text_lower:
                    trading_terms += 1
        
        metrics['trading_term_density'] = min(1.0, trading_terms / 20)
        
        return metrics


# Main NLP pipeline
class AdvancedNLPPipeline:
    """Complete NLP pipeline for knowledge processing"""
    
    def __init__(self):
        self.summarizer = T5Summarizer()
        self.concept_extractor = StrategyConceptExtractor()
        self.relationship_detector = ConceptRelationshipDetector()
        self.clusterer = StrategyClusterer()
        self.paraphraser = TextParaphraser()
        self.quality_analyzer = ContentQualityAnalyzer()
    
    def process_content(self, raw_content: Dict) -> Dict:
        """
        Process raw scraped content through full NLP pipeline
        
        Args:
            raw_content: Dict with 'text', 'strategy', etc.
            
        Returns:
            Enriched content dict
        """
        text = raw_content.get('full_text', '')
        strategy = raw_content.get('strategy', 'ta')
        
        # Generate summary
        summary = self.summarizer.summarize(text)
        
        # Extract concepts
        concepts = self.concept_extractor.extract_concepts(text, strategy)
        
        # Analyze quality
        quality = self.quality_analyzer.analyze(text)
        
        # Extract noun phrases
        noun_phrases = self.concept_extractor.extract_noun_phrases(text)
        
        return {
            **raw_content,
            'summary': summary,
            'extracted_concepts': concepts,
            'noun_phrases': noun_phrases[:10],
            'quality_metrics': quality,
            'processed': True,
            'processor_version': '2.0'
        }
    
    def detect_all_relationships(self, entries: List[Dict]) -> List[Dict]:
        """Detect relationships across all entries"""
        all_concepts = [e.get('concept', '') for e in entries]
        relationships = []
        
        for entry in entries:
            concept = entry.get('concept', '')
            text = entry.get('full_text', '')
            
            rels = self.relationship_detector.detect_relationships(concept, text, all_concepts)
            relationships.extend(rels)
        
        return relationships
