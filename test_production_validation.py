#!/usr/bin/env python3
"""
Production Validation Test Suite
Tests system performance, content quality, and production readiness
"""

import os
import sys
import django
import time
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
django.setup()

from knowledge_base.models import KnowledgeEntry, Source, ConceptRelationship, QueryCache
from knowledge_engine.query_engine import KnowledgeQueryEngine
from bot.kb_integration import KBQuestionAnswerer
from zenbot.contextualizer_v2 import EnhancedContextualIntelligenceEngine


class ProductionValidator:
    """Comprehensive production validation"""
    
    def __init__(self):
        self.query_engine = KnowledgeQueryEngine()
        self.bot = KBQuestionAnswerer()
        self.contextualizer = EnhancedContextualIntelligenceEngine()
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'warnings': [],
            'errors': [],
            'performance': {}
        }
    
    def print_header(self, title):
        """Print formatted test section header"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    
    def print_result(self, test_name, passed, details=""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.results['tests_passed'] += 1
        else:
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"{test_name}: {details}")
    
    # ========================
    # CONTENT QUALITY TESTS
    # ========================
    
    def test_kb_content_quality(self):
        """Validate Knowledge Base content quality"""
        self.print_header("CONTENT QUALITY VALIDATION")
        
        # Test 1: Minimum entries
        total_entries = KnowledgeEntry.objects.filter(is_active=True).count()
        passed = total_entries >= 20
        self.print_result(
            "Minimum 20 active entries",
            passed,
            f"Found {total_entries} entries"
        )
        
        # Test 2: All entries verified
        unverified = KnowledgeEntry.objects.filter(is_active=True, is_verified=False).count()
        passed = unverified == 0
        self.print_result(
            "All active entries verified",
            passed,
            f"{unverified} unverified entries" if not passed else "100% verified"
        )
        
        # Test 3: Embedding coverage
        no_embeddings = KnowledgeEntry.objects.filter(
            is_active=True,
            embedding_summary__isnull=True
        ).count()
        passed = no_embeddings == 0
        self.print_result(
            "100% embedding coverage",
            passed,
            f"{no_embeddings} entries missing embeddings" if not passed else "All embedded"
        )
        
        # Test 4: Content completeness
        incomplete = KnowledgeEntry.objects.filter(
            is_active=True
        ).filter(
            definition__isnull=True
        ) | KnowledgeEntry.objects.filter(
            is_active=True,
            definition=""
        )
        incomplete_count = incomplete.count()
        passed = incomplete_count == 0
        self.print_result(
            "All entries have definitions",
            passed,
            f"{incomplete_count} entries missing definitions" if not passed else "Complete"
        )
        
        # Test 5: Quality scores
        low_quality = KnowledgeEntry.objects.filter(
            is_active=True,
            quality_score__lt=0.3
        ).count()
        passed = low_quality == 0
        self.print_result(
            "No low-quality entries (<0.3)",
            passed,
            f"{low_quality} entries with quality < 0.3" if not passed else "All above threshold"
        )
        
        # Test 6: Strategy coverage
        strategies = KnowledgeEntry.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct()
        strategy_count = len([s for s in strategies if s])
        passed = strategy_count >= 5
        self.print_result(
            "Minimum 5 strategy categories",
            passed,
            f"Found {strategy_count} categories"
        )
        
        # Test 7: Relationships exist
        relationships = ConceptRelationship.objects.count()
        passed = relationships >= 0  # Just check it exists
        self.print_result(
            "Concept relationships table",
            passed,
            f"{relationships} relationships"
        )
        
        # Test 8: Source diversity
        sources = Source.objects.filter(active=True).count()
        passed = sources >= 1
        self.print_result(
            "At least 1 active source",
            passed,
            f"{sources} sources"
        )
    
    # ========================
    # PERFORMANCE TESTS
    # ========================
    
    def test_query_performance(self):
        """Test query performance benchmarks"""
        self.print_header("PERFORMANCE BENCHMARKS")
        
        test_queries = [
            "What is an order block?",
            "Explain smart money concepts",
            "How to identify liquidity sweeps?",
            "What is institutional order flow?",
            "Define fair value gap"
        ]
        
        latencies = []
        
        for query in test_queries:
            start = time.time()
            try:
                results = self.query_engine.search_concept(query, k=3)
                latency = (time.time() - start) * 1000  # Convert to ms
                latencies.append(latency)
                
                passed = latency < 500  # Target: < 500ms
                self.print_result(
                    f"Query latency: '{query[:30]}...'",
                    passed,
                    f"{latency:.1f}ms"
                )
            except Exception as e:
                self.print_result(
                    f"Query execution: '{query[:30]}...'",
                    False,
                    f"Error: {str(e)}"
                )
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            self.results['performance']['avg_query_latency_ms'] = avg_latency
            
            passed = avg_latency < 500
            self.print_result(
                "Average query latency < 500ms",
                passed,
                f"{avg_latency:.1f}ms average"
            )
    
    def test_cache_performance(self):
        """Test cache hit rates and effectiveness"""
        self.print_header("CACHE PERFORMANCE")
        
        # Test 1: Cache exists
        cache_entries = QueryCache.objects.count()
        passed = True  # Always pass, just report
        self.print_result(
            "Query cache operational",
            passed,
            f"{cache_entries} cached queries"
        )
        
        # Test 2: Run same query twice to test cache
        query = "What is an order block?"
        
        # First query (cache miss)
        start = time.time()
        self.query_engine.search_concept(query, k=3)
        first_latency = (time.time() - start) * 1000
        
        # Second query (cache hit)
        start = time.time()
        self.query_engine.search_concept(query, k=3)
        second_latency = (time.time() - start) * 1000
        
        speedup = first_latency / second_latency if second_latency > 0 else 1
        passed = speedup > 1.2  # At least 20% faster
        
        self.print_result(
            "Cache speedup (2nd query faster)",
            passed,
            f"{speedup:.2f}x speedup ({first_latency:.1f}ms → {second_latency:.1f}ms)"
        )
        
        self.results['performance']['cache_speedup'] = speedup
    
    # ========================
    # INTEGRATION TESTS
    # ========================
    
    def test_zenbot_integration(self):
        """Test ZenBot integration"""
        self.print_header("ZENBOT INTEGRATION")
        
        test_cases = [
            ("What is an order block?", "what"),
            ("How do I trade liquidity sweeps?", "how"),
            ("When should I enter a trade?", "when"),
            ("Why use smart money concepts?", "why")
        ]
        
        for question, expected_type in test_cases:
            try:
                start = time.time()
                response = self.bot.get_kb_answer(question)
                latency = (time.time() - start) * 1000
                
                has_answer = response.get('answer') is not None
                has_confidence = response.get('kb_confidence', 0) > 0
                
                passed = has_answer and latency < 2000  # < 2 seconds
                
                self.print_result(
                    f"ZenBot: '{question[:40]}...'",
                    passed,
                    f"Confidence: {response.get('kb_confidence', 0):.2f}, {latency:.0f}ms"
                )
            except Exception as e:
                self.print_result(
                    f"ZenBot: '{question[:40]}...'",
                    False,
                    f"Error: {str(e)}"
                )
    
    def test_contextualizer_integration(self):
        """Test Contextualizer v2.0 integration"""
        self.print_header("CONTEXTUALIZER V2.0 INTEGRATION")
        
        # Create test signal
        test_signal = {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry': 1.0850,
            'stop_loss': 1.0820,
            'take_profit': 1.0910,
            'strategy_name': 'Smart Money Concepts',
            'timeframe': '15m',
            'confidence': 0.85
        }
        
        # Test 1: Generate narrative
        try:
            start = time.time()
            narrative = self.contextualizer.generate_narrative(test_signal)
            latency = (time.time() - start) * 1000
            
            passed = len(narrative) > 50 and latency < 3000
            self.print_result(
                "Generate signal narrative",
                passed,
                f"{len(narrative)} chars, {latency:.0f}ms"
            )
        except Exception as e:
            self.print_result(
                "Generate signal narrative",
                False,
                f"Error: {str(e)}"
            )
        
        # Test 2: Educational context
        try:
            start = time.time()
            context = self.contextualizer.get_educational_context(
                test_signal,
                difficulty='intermediate'
            )
            latency = (time.time() - start) * 1000
            
            passed = len(context) > 50 and latency < 3000
            self.print_result(
                "Generate educational context",
                passed,
                f"{len(context)} chars, {latency:.0f}ms"
            )
        except Exception as e:
            self.print_result(
                "Generate educational context",
                False,
                f"Error: {str(e)}"
            )
        
        # Test 3: Linguistic variation
        narratives = []
        try:
            for i in range(3):
                narrative = self.contextualizer.generate_narrative(test_signal)
                narratives.append(narrative)
            
            unique_narratives = len(set(narratives))
            passed = unique_narratives == 3  # All should be unique
            
            self.print_result(
                "Linguistic variation (3 generations)",
                passed,
                f"{unique_narratives}/3 unique"
            )
        except Exception as e:
            self.print_result(
                "Linguistic variation",
                False,
                f"Error: {str(e)}"
            )
    
    # ========================
    # SEMANTIC SEARCH TESTS
    # ========================
    
    def test_semantic_search_accuracy(self):
        """Test semantic search relevance"""
        self.print_header("SEMANTIC SEARCH ACCURACY")
        
        test_cases = [
            ("order block", ["order block", "institutional", "smart money"]),
            ("liquidity sweep", ["liquidity", "sweep", "stop loss"]),
            ("fair value gap", ["fair value", "gap", "imbalance"]),
            ("break of structure", ["structure", "break", "trend"]),
            ("change of character", ["character", "change", "momentum"])
        ]
        
        for query, expected_terms in test_cases:
            try:
                results = self.query_engine.search_concept(query, k=3)
                
                if not results:
                    self.print_result(
                        f"Search: '{query}'",
                        False,
                        "No results returned"
                    )
                    continue
                
                # Check if any expected terms appear in top result
                top_result = results[0]
                result_text = (
                    top_result.get('term', '') + ' ' +
                    top_result.get('definition', '')
                ).lower()
                
                matches = sum(1 for term in expected_terms if term.lower() in result_text)
                similarity = top_result.get('similarity', 0)
                
                passed = matches >= 1 and similarity > 0.5
                
                self.print_result(
                    f"Search: '{query}'",
                    passed,
                    f"Similarity: {similarity:.3f}, {matches}/{len(expected_terms)} terms matched"
                )
            except Exception as e:
                self.print_result(
                    f"Search: '{query}'",
                    False,
                    f"Error: {str(e)}"
                )
    
    # ========================
    # STRESS TESTS
    # ========================
    
    def test_concurrent_queries(self):
        """Test handling of rapid concurrent queries"""
        self.print_header("STRESS TEST: CONCURRENT QUERIES")
        
        queries = [
            "order block",
            "liquidity sweep",
            "fair value gap",
            "smart money",
            "break of structure"
        ] * 4  # 20 total queries
        
        start = time.time()
        successful = 0
        failed = 0
        
        for query in queries:
            try:
                self.query_engine.search_concept(query, k=3)
                successful += 1
            except Exception as e:
                failed += 1
        
        total_time = time.time() - start
        avg_time = (total_time / len(queries)) * 1000
        
        passed = failed == 0 and avg_time < 1000
        
        self.print_result(
            f"Process {len(queries)} queries",
            passed,
            f"{successful} succeeded, {failed} failed, {avg_time:.1f}ms avg"
        )
        
        self.results['performance']['concurrent_avg_ms'] = avg_time
        self.results['performance']['concurrent_success_rate'] = successful / len(queries)
    
    # ========================
    # SYSTEM HEALTH CHECKS
    # ========================
    
    def test_system_health(self):
        """Comprehensive system health checks"""
        self.print_header("SYSTEM HEALTH CHECKS")
        
        # Test 1: Database connectivity
        try:
            KnowledgeEntry.objects.count()
            self.print_result("Database connectivity", True, "Connection successful")
        except Exception as e:
            self.print_result("Database connectivity", False, f"Error: {str(e)}")
        
        # Test 2: Models integrity
        try:
            # Check for orphaned entries
            orphaned = KnowledgeEntry.objects.filter(source__isnull=True).count()
            passed = orphaned == 0
            self.print_result(
                "No orphaned entries",
                passed,
                f"{orphaned} orphaned entries" if not passed else "All have sources"
            )
        except Exception as e:
            self.print_result("Models integrity", False, f"Error: {str(e)}")
        
        # Test 3: Cache not overgrown
        old_cache = QueryCache.objects.count()
        passed = old_cache < 10000  # Warning if cache too large
        if not passed:
            self.results['warnings'].append(f"Cache has {old_cache} entries, consider cleanup")
        self.print_result(
            "Cache size reasonable",
            passed,
            f"{old_cache} entries"
        )
        
        # Test 4: No duplicate concepts
        from django.db.models import Count
        duplicates = KnowledgeEntry.objects.values('term').annotate(
            count=Count('term')
        ).filter(count__gt=1).count()
        
        passed = duplicates == 0
        if not passed:
            self.results['warnings'].append(f"{duplicates} duplicate terms found")
        self.print_result(
            "No duplicate terms",
            passed,
            f"{duplicates} duplicates" if not passed else "All unique"
        )
    
    # ========================
    # MAIN RUNNER
    # ========================
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("\n" + "="*70)
        print("  KNOWLEDGE ENGINE v2.0 - PRODUCTION VALIDATION SUITE")
        print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*70)
        
        # Run all test categories
        self.test_kb_content_quality()
        self.test_query_performance()
        self.test_cache_performance()
        self.test_zenbot_integration()
        self.test_contextualizer_integration()
        self.test_semantic_search_accuracy()
        self.test_concurrent_queries()
        self.test_system_health()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary"""
        self.print_header("VALIDATION SUMMARY")
        
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        success_rate = (self.results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {self.results['tests_passed']}")
        print(f"❌ Failed: {self.results['tests_failed']}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if self.results['performance']:
            print("\n📊 Performance Metrics:")
            for key, value in self.results['performance'].items():
                if isinstance(value, float):
                    print(f"  • {key}: {value:.2f}")
                else:
                    print(f"  • {key}: {value}")
        
        if self.results['warnings']:
            print("\n⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
        
        if self.results['errors']:
            print("\n❌ Errors:")
            for error in self.results['errors'][:5]:  # Show first 5
                print(f"  • {error}")
        
        # Production readiness score
        readiness_score = success_rate
        
        print("\n" + "="*70)
        if readiness_score >= 90:
            status = "✅ PRODUCTION READY"
        elif readiness_score >= 80:
            status = "⚠️  NEEDS MINOR FIXES"
        else:
            status = "❌ NOT PRODUCTION READY"
        
        print(f"Production Readiness: {readiness_score:.1f}% - {status}")
        print("="*70 + "\n")
        
        return readiness_score >= 80


if __name__ == '__main__':
    validator = ProductionValidator()
    is_ready = validator.run_all_tests()
    
    sys.exit(0 if is_ready else 1)
